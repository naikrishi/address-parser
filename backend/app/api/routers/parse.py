from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.parse_result import ParseResult
from app.models.raw_input import RawInput
from app.schemas.parse import (
    InputListItem,
    InputsListResponse,
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
        .options(selectinload(ParseResult.raw_input))
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
        .options(selectinload(ParseResult.raw_input))
        .where(ParseResult.id == parse_id)
    )
    parse_result = db.scalar(query)
    if parse_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parse result not found")

    return parse_result


@router.get("/inputs", response_model=InputsListResponse)
def get_inputs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> InputsListResponse:
    total = db.scalar(select(func.count(RawInput.id)))
    total_count = int(total or 0)

    query = (
        select(RawInput)
        .options(selectinload(RawInput.parse_results))
        .order_by(RawInput.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.scalars(query).all()

    items = [
        InputListItem(
            id=row.id,
            raw_address=row.raw_address,
            input_source=row.input_source,
            country_hint=row.country_hint,
            created_at=row.created_at,
            parse_result_count=len(row.parse_results),
        )
        for row in rows
    ]

    return InputsListResponse(items=items, total=total_count, limit=limit, offset=offset)
