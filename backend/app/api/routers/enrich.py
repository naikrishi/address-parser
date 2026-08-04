from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.llm.embeddings import embed_text
from app.llm.summarize import generate_summary, score_confidence
from app.models.enrichment_result import EnrichmentResult
from app.models.geocode_result import GeocodeResult
from app.models.parse_result import ParseResult
from app.models.raw_input import RawInput
from app.schemas.enrich import EnrichRequest, EnrichResponse, EnrichmentStepTrace
from app.services import enrich as enrich_svc
from app.services import geocode as geocode_svc
from app.services.cost import estimate_cost

router = APIRouter(prefix="/enrich", tags=["enrich"])


@router.post("", response_model=EnrichResponse, status_code=status.HTTP_201_CREATED)
def run_enrich(payload: EnrichRequest, db: Session = Depends(get_db)) -> EnrichResponse:
    row = db.scalar(
        select(ParseResult)
        .options(selectinload(ParseResult.raw_input))
        .where(ParseResult.id == payload.parse_result_id)
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse result not found")

    raw_address: str = row.raw_input.raw_address
    components: dict = dict(row.parsed_components)
    steps: list[EnrichmentStepTrace] = []
    total_pt = total_ct = 0

    # Step 1 is already done (parse_result exists); record it as a trace entry
    step1_status = "complete" if row.is_complete else "partial"
    steps.append(EnrichmentStepTrace(step=1, provider="libpostal-stub", status=step1_status))

    # Step 2: LLM gap fill
    components, pt, ct, cost2, provider2 = enrich_svc.run_step2(raw_address, components)
    total_pt += pt; total_ct += ct
    step2_status = "skipped" if provider2 == "skipped" else ("error" if provider2 == "error" else "complete")
    steps.append(EnrichmentStepTrace(step=2, provider=provider2, status=step2_status, prompt_tokens=pt, completion_tokens=ct, estimated_cost=cost2))

    # Step 3: web-search fallback
    components, pt, ct, cost3, provider3 = enrich_svc.run_step3(raw_address, components)
    total_pt += pt; total_ct += ct
    step3_status = "skipped" if provider3 == "skipped" else ("error" if provider3 == "error" else "complete")
    steps.append(EnrichmentStepTrace(step=3, provider=provider3, status=step3_status, prompt_tokens=pt, completion_tokens=ct, estimated_cost=cost3))

    # Compute enrichment completeness
    required = ["street_line", "city", "state", "postal_code"]
    is_complete = all(components.get(k) for k in required)
    enrich_cost = estimate_cost(total_pt, total_ct)

    # Step 4: geocode
    address_str = ", ".join(v for v in components.values() if v)
    lat, lon, geocode_payload, backfill, pt4, ct4, cost4, geo_provider = geocode_svc.run_step4(
        address_str, components
    )
    steps.append(EnrichmentStepTrace(step=4, provider=geo_provider, status="complete" if lat else "partial", prompt_tokens=pt4, completion_tokens=ct4, estimated_cost=cost4))

    # Apply backfill from geocode
    if backfill:
        for k, v in backfill.items():
            if not components.get(k):
                components[k] = v
        is_complete = all(components.get(k) for k in required)

    # Confidence scoring
    steps_ran = [s.step for s in steps if s.status not in ("skipped", "error")]
    confidence_label, pt_conf, ct_conf = score_confidence(raw_address, dict(row.parsed_components), components, lat is not None)

    # Generate embedding for this parse (or update if missing)
    try:
        if row.embedding is None:
            row.embedding = embed_text(raw_address, components)
    except Exception:
        pass  # embedding failure must not block enrichment persistence

    # Persist enrichment result
    enrichment = EnrichmentResult(
        parse_result_id=row.id,
        provider_name="pipeline",
        status="complete" if is_complete else "partial",
        enriched_components=components,
        is_complete=is_complete,
        confidence_score=None,
        confidence_label=confidence_label,
        prompt_tokens=total_pt + pt_conf,
        completion_tokens=total_ct + ct_conf,
        estimated_cost=round(enrich_cost + estimate_cost(pt_conf, ct_conf), 6),
    )
    db.add(enrichment)
    db.flush()

    # Persist geocode result
    geocode = GeocodeResult(
        parse_result_id=row.id,
        enrichment_result_id=enrichment.id,
        provider_name=geo_provider,
        status="complete" if lat else "partial",
        latitude=lat,
        longitude=lon,
        result_payload=geocode_payload,
        prompt_tokens=pt4,
        completion_tokens=ct4,
        estimated_cost=cost4,
    )
    db.add(geocode)

    # Generate and store summary
    summary_text = generate_summary(
        raw_address=raw_address,
        parsed_components=dict(row.parsed_components),
        enriched_components=components,
        lat=lat,
        lon=lon,
        confidence_label=confidence_label,
        steps_ran=steps_ran,
    )
    enrichment.llm_summary = summary_text

    db.commit()

    total_cost = round(sum(s.estimated_cost for s in steps), 6)

    return EnrichResponse(
        parse_result_id=row.id,
        enrichment_result_id=enrichment.id,
        geocode_result_id=geocode.id,
        enriched_components=components,
        is_complete=is_complete,
        confidence_label=confidence_label,
        latitude=lat,
        longitude=lon,
        steps=steps,
        total_estimated_cost=total_cost,
        created_at=enrichment.created_at,
    )

