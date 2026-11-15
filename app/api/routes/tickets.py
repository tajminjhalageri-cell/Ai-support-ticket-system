import secrets
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Ticket
from app.schemas.ticket import TicketCreate, TicketList, TicketRead, TicketUpdate

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def require_delete_key(
    x_delete_api_key: Annotated[str | None, Header()] = None,
) -> None:
    configured_key = settings.ticket_delete_api_key
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ticket deletion is not configured",
        )
    if x_delete_api_key is None or not secrets.compare_digest(
        x_delete_api_key, configured_key
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid delete API key is required",
        )


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: DatabaseSession) -> Ticket:
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=TicketList)
def list_tickets(
    db: DatabaseSession,
    q: Annotated[str | None, Query(max_length=200)] = None,
    status_filter: Annotated[
        Literal["open", "in_progress", "resolved", "closed"] | None,
        Query(alias="status"),
    ] = None,
    priority: Literal["low", "medium", "high", "critical"] | None = None,
    sort_by: Literal["created_at", "updated_at", "title", "status", "priority"] = (
        "created_at"
    ),
    sort_order: Literal["asc", "desc"] = "desc",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TicketList:
    statement = select(Ticket)
    count_statement = select(func.count()).select_from(Ticket)
    filters = []

    if q:
        search = f"%{q.strip()}%"
        filters.append(
            or_(Ticket.title.ilike(search), Ticket.description.ilike(search))
        )
    if status_filter:
        filters.append(Ticket.status == status_filter)
    if priority:
        filters.append(Ticket.priority == priority)

    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)

    sort_column = getattr(Ticket, sort_by)
    ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tickets = db.scalars(statement.order_by(ordering).offset(skip).limit(limit)).all()
    total = db.scalar(count_statement) or 0

    return TicketList(items=tickets, total=total, skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: DatabaseSession) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return ticket


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int, payload: TicketUpdate, db: DatabaseSession
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_delete_key)],
)
def delete_ticket(ticket_id: int, db: DatabaseSession) -> Response:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
