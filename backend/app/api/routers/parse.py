from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, exists, func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.llm.summarize import generate_summary, score_confidence
from app.models.enrichment_result import EnrichmentResult
from app.models.geocode_result import GeocodeResult
from app.models.parse_result import ParseResult
from app.models.raw_input import RawInput
from app.schemas.enrich import ParseSummaryResponse
from app.schemas.parse import (
    InputListItem,
    InputsListResponse,
    ParseListItem,
    ParseListResponse,
    ParseCreateRequest,
    ParseResultResponse,
)

router = APIRouter(tags=["parse"])

REQUIRED_COMPONENT_KEYS = ["street_line", "city", "state", "postal_code"]


def _build_parse_stub(raw_address: str, country_hint: str | None) -> tuple[dict[str, str | None], bool, float]:
    parts = [segment.strip() for segment in raw_address.split(",") if segment.strip()]

    street_line = parts[0] if len(parts) > 0 else None
    city = parts[1] if len(parts) > 1 else None

    state = None
    postal_code = None
    if len(parts) > 2:
        state_zip_tokens = parts[2].split()
        if state_zip_tokens:
            state = state_zip_tokens[0]
        if len(state_zip_tokens) > 1:
            postal_code = state_zip_tokens[-1]

    country = country_hint or (parts[3] if len(parts) > 3 else None)

    parsed_components: dict[str, str | None] = {
        "street_line": street_line,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
    }

    complete = all(parsed_components.get(key) for key in REQUIRED_COMPONENT_KEYS)
    confidence_score = 0.75 if complete else 0.4
    return parsed_components, complete, confidence_score


def _build_parse_summary_maps(db: Session, parse_ids: list[UUID]) -> dict[UUID, dict[str, int | str | None]]:
    if not parse_ids:
        return {}

    enrichment_counts_rows = db.execute(
        select(EnrichmentResult.parse_result_id, func.count(EnrichmentResult.id))
        .where(EnrichmentResult.parse_result_id.in_(parse_ids))
        .group_by(EnrichmentResult.parse_result_id)
    ).all()
    enrichment_counts = {row[0]: int(row[1]) for row in enrichment_counts_rows}

    geocode_counts_rows = db.execute(
        select(GeocodeResult.parse_result_id, func.count(GeocodeResult.id))
        .where(GeocodeResult.parse_result_id.in_(parse_ids))
        .group_by(GeocodeResult.parse_result_id)
    ).all()
    geocode_counts = {row[0]: int(row[1]) for row in geocode_counts_rows}

    latest_enrichment_rows = db.execute(
        select(EnrichmentResult.parse_result_id, EnrichmentResult.status)
        .where(EnrichmentResult.parse_result_id.in_(parse_ids))
        .order_by(EnrichmentResult.parse_result_id, EnrichmentResult.created_at.desc())
        .distinct(EnrichmentResult.parse_result_id)
    ).all()
    latest_enrichment_status = {row[0]: row[1] for row in latest_enrichment_rows}

    latest_geocode_rows = db.execute(
        select(GeocodeResult.parse_result_id, GeocodeResult.status)
        .where(GeocodeResult.parse_result_id.in_(parse_ids))
        .order_by(GeocodeResult.parse_result_id, GeocodeResult.created_at.desc())
        .distinct(GeocodeResult.parse_result_id)
    ).all()
    latest_geocode_status = {row[0]: row[1] for row in latest_geocode_rows}

    return {
        parse_id: {
            "enrichment_count": enrichment_counts.get(parse_id, 0),
            "geocode_count": geocode_counts.get(parse_id, 0),
            "latest_enrichment_status": latest_enrichment_status.get(parse_id),
            "latest_geocode_status": latest_geocode_status.get(parse_id),
        }
        for parse_id in parse_ids
    }


def _build_input_summary_maps(
    db: Session,
    raw_input_ids: list[UUID],
) -> dict[UUID, dict[str, int | bool]]:
    if not raw_input_ids:
        return {}

    parse_count_rows = db.execute(
        select(ParseResult.raw_input_id, func.count(ParseResult.id))
        .where(ParseResult.raw_input_id.in_(raw_input_ids))
        .group_by(ParseResult.raw_input_id)
    ).all()
    parse_counts = {row[0]: int(row[1]) for row in parse_count_rows}

    enrichment_count_rows = db.execute(
        select(ParseResult.raw_input_id, func.count(EnrichmentResult.id))
        .join(EnrichmentResult, EnrichmentResult.parse_result_id == ParseResult.id)
        .where(ParseResult.raw_input_id.in_(raw_input_ids))
        .group_by(ParseResult.raw_input_id)
    ).all()
    enrichment_counts = {row[0]: int(row[1]) for row in enrichment_count_rows}

    geocode_count_rows = db.execute(
        select(ParseResult.raw_input_id, func.count(GeocodeResult.id))
        .join(GeocodeResult, GeocodeResult.parse_result_id == ParseResult.id)
        .where(ParseResult.raw_input_id.in_(raw_input_ids))
        .group_by(ParseResult.raw_input_id)
    ).all()
    geocode_counts = {row[0]: int(row[1]) for row in geocode_count_rows}

    return {
        raw_input_id: {
            "parse_result_count": parse_counts.get(raw_input_id, 0),
            "enrichment_result_count": enrichment_counts.get(raw_input_id, 0),
            "geocode_result_count": geocode_counts.get(raw_input_id, 0),
            "has_enrichment": enrichment_counts.get(raw_input_id, 0) > 0,
            "has_geocode": geocode_counts.get(raw_input_id, 0) > 0,
        }
        for raw_input_id in raw_input_ids
    }


@router.post("/parse", response_model=ParseResultResponse, status_code=status.HTTP_201_CREATED)
def create_parse(
    payload: ParseCreateRequest,
    db: Session = Depends(get_db),
) -> ParseResult:
    parsed_components, is_complete, confidence_score = _build_parse_stub(
        raw_address=payload.raw_address,
        country_hint=payload.country_hint,
    )

    raw_input = RawInput(
        raw_address=payload.raw_address,
        input_source=payload.input_source,
        country_hint=payload.country_hint,
    )
    db.add(raw_input)
    db.flush()

    parse_result = ParseResult(
        raw_input_id=raw_input.id,
        parser_name="stub",
        parsed_components=parsed_components,
        is_complete=is_complete,
        confidence_score=confidence_score,
    )
    db.add(parse_result)
    db.commit()

    query = (
        select(ParseResult)
        .options(
            selectinload(ParseResult.raw_input),
            selectinload(ParseResult.enrichment_results),
            selectinload(ParseResult.geocode_results),
        )
        .where(ParseResult.id == parse_result.id)
    )
    created_result = db.scalar(query)
    if created_result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Created parse result not found")

    return created_result


@router.get("/parse/{parse_id}", response_model=ParseResultResponse)
def get_parse(parse_id: UUID, db: Session = Depends(get_db)) -> ParseResult:
    query = (
        select(ParseResult)
        .options(
            selectinload(ParseResult.raw_input),
            selectinload(ParseResult.enrichment_results),
            selectinload(ParseResult.geocode_results),
        )
        .where(ParseResult.id == parse_id)
    )
    parse_result = db.scalar(query)
    if parse_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse result not found")

    return parse_result


@router.get("/parses", response_model=ParseListResponse)
def get_parses(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    parser_name: str | None = Query(default=None, min_length=1, max_length=100),
    is_complete: bool | None = Query(default=None),
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    max_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    has_enrichment: bool | None = Query(default=None),
    has_geocode: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ParseListResponse:
    filters = []
    if parser_name is not None:
        filters.append(ParseResult.parser_name == parser_name.strip())
    if is_complete is not None:
        filters.append(ParseResult.is_complete == is_complete)
    if min_confidence is not None:
        filters.append(ParseResult.confidence_score >= min_confidence)
    if max_confidence is not None:
        filters.append(ParseResult.confidence_score <= max_confidence)
    if has_enrichment is not None:
        enrichment_exists = exists(select(1).where(EnrichmentResult.parse_result_id == ParseResult.id))
        filters.append(enrichment_exists if has_enrichment else ~enrichment_exists)
    if has_geocode is not None:
        geocode_exists = exists(select(1).where(GeocodeResult.parse_result_id == ParseResult.id))
        filters.append(geocode_exists if has_geocode else ~geocode_exists)

    base_query = select(ParseResult).join(RawInput, ParseResult.raw_input_id == RawInput.id)
    if filters:
        base_query = base_query.where(and_(*filters))

    total_query = select(func.count()).select_from(base_query.order_by(None).subquery())
    total = db.scalar(total_query)
    total_count = int(total or 0)

    rows = db.scalars(
        base_query.options(
            selectinload(ParseResult.raw_input),
        )
        .order_by(ParseResult.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    parse_summary_by_id = _build_parse_summary_maps(db, [row.id for row in rows])

    items = [
        ParseListItem(
            id=row.id,
            raw_input_id=row.raw_input_id,
            parser_name=row.parser_name,
            is_complete=row.is_complete,
            confidence_score=row.confidence_score,
            created_at=row.created_at,
            raw_address=row.raw_input.raw_address,
            input_source=row.raw_input.input_source,
            country_hint=row.raw_input.country_hint,
            enrichment_result_count=int(parse_summary_by_id.get(row.id, {}).get("enrichment_count", 0)),
            geocode_result_count=int(parse_summary_by_id.get(row.id, {}).get("geocode_count", 0)),
            latest_enrichment_status=parse_summary_by_id.get(row.id, {}).get("latest_enrichment_status"),
            latest_geocode_status=parse_summary_by_id.get(row.id, {}).get("latest_geocode_status"),
        )
        for row in rows
    ]

    return ParseListResponse(items=items, total=total_count, limit=limit, offset=offset)


@router.get("/inputs", response_model=InputsListResponse)
def get_inputs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    input_source: str | None = Query(default=None, min_length=1, max_length=100),
    country_hint: str | None = Query(default=None, min_length=1, max_length=100),
    has_parse_results: bool | None = Query(default=None),
    has_enrichment: bool | None = Query(default=None),
    has_geocode: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> InputsListResponse:
    filters = []
    if input_source is not None:
        filters.append(RawInput.input_source == input_source.strip())
    if country_hint is not None:
        filters.append(RawInput.country_hint == country_hint.strip())
    if has_parse_results is not None:
        parse_exists = exists(select(1).where(ParseResult.raw_input_id == RawInput.id))
        filters.append(parse_exists if has_parse_results else ~parse_exists)
    if has_enrichment is not None:
        enrichment_exists = exists(
            select(1)
            .select_from(ParseResult)
            .join(EnrichmentResult, EnrichmentResult.parse_result_id == ParseResult.id)
            .where(ParseResult.raw_input_id == RawInput.id)
        )
        filters.append(enrichment_exists if has_enrichment else ~enrichment_exists)
    if has_geocode is not None:
        geocode_exists = exists(
            select(1)
            .select_from(ParseResult)
            .join(GeocodeResult, GeocodeResult.parse_result_id == ParseResult.id)
            .where(ParseResult.raw_input_id == RawInput.id)
        )
        filters.append(geocode_exists if has_geocode else ~geocode_exists)

    base_query = select(RawInput)
    if filters:
        base_query = base_query.where(and_(*filters))

    total = db.scalar(select(func.count()).select_from(base_query.order_by(None).subquery()))
    total_count = int(total or 0)

    rows = db.scalars(
        base_query
        .order_by(RawInput.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    input_summary_by_id = _build_input_summary_maps(db, [row.id for row in rows])

    items = [
        InputListItem(
            id=row.id,
            raw_address=row.raw_address,
            input_source=row.input_source,
            country_hint=row.country_hint,
            created_at=row.created_at,
            parse_result_count=int(input_summary_by_id.get(row.id, {}).get("parse_result_count", 0)),
            enrichment_result_count=int(input_summary_by_id.get(row.id, {}).get("enrichment_result_count", 0)),
            geocode_result_count=int(input_summary_by_id.get(row.id, {}).get("geocode_result_count", 0)),
            has_enrichment=bool(input_summary_by_id.get(row.id, {}).get("has_enrichment", False)),
            has_geocode=bool(input_summary_by_id.get(row.id, {}).get("has_geocode", False)),
        )
        for row in rows
    ]

    return InputsListResponse(items=items, total=total_count, limit=limit, offset=offset)


@router.get("/parse/{parse_id}/summary", response_model=ParseSummaryResponse)
def get_parse_summary(parse_id: UUID, db: Session = Depends(get_db)) -> ParseSummaryResponse:
    row = db.scalar(
        select(ParseResult)
        .options(
            selectinload(ParseResult.raw_input),
            selectinload(ParseResult.enrichment_results),
            selectinload(ParseResult.geocode_results),
        )
        .where(ParseResult.id == parse_id)
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse result not found")

    # Use cached summary if enrichment has already run
    enrichment = row.enrichment_results[-1] if row.enrichment_results else None
    if enrichment and enrichment.llm_summary:
        return ParseSummaryResponse(
            parse_result_id=parse_id,
            summary=enrichment.llm_summary,
            confidence_label=enrichment.confidence_label,
            generated_at=enrichment.created_at,
        )

    geocode = row.geocode_results[-1] if row.geocode_results else None
    lat = geocode.latitude if geocode else None
    lon = geocode.longitude if geocode else None
    enriched = enrichment.enriched_components if enrichment else row.parsed_components
    confidence_label = enrichment.confidence_label if enrichment else None

    if confidence_label is None:
        confidence_label, _, _ = score_confidence(
            row.raw_input.raw_address,
            dict(row.parsed_components),
            dict(enriched),
            lat is not None,
        )

    summary = generate_summary(
        raw_address=row.raw_input.raw_address,
        parsed_components=dict(row.parsed_components),
        enriched_components=dict(enriched),
        lat=lat,
        lon=lon,
        confidence_label=confidence_label or "low",
        steps_ran=[1] if not enrichment else [1, 2, 3, 4],
    )

    return ParseSummaryResponse(
        parse_result_id=parse_id,
        summary=summary,
        confidence_label=confidence_label,
        generated_at=datetime.now(timezone.utc),
    )
