from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.schemas import TicketCreate, TicketUpdate, TicketResponse
from app.services import ticket_service
from app.models.models import TicketStatus

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Cria um novo ingresso para venda"""
    try:
        return ticket_service.create_ticket(db, ticket, seller_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[TicketResponse])
def list_tickets(
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    status_filter: Optional[TicketStatus] = Query(None, alias="status", description="Filtrar por status"),
    seller_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    db: Session = Depends(get_db)
):
    """Lista ingressos com filtros opcionais"""
    return ticket_service.get_tickets(
        db,
        skip=skip,
        limit=limit,
        event_id=event_id,
        status=status_filter,
        seller_id=seller_id
    )


@router.get("/available", response_model=List[TicketResponse])
def list_available_tickets(
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    db: Session = Depends(get_db)
):
    """Lista ingressos disponíveis para compra"""
    return ticket_service.get_available_tickets(db, event_id=event_id, skip=skip, limit=limit)


@router.get("/seller/{seller_id}", response_model=List[TicketResponse])
def list_seller_tickets(
    seller_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos os ingressos de um vendedor"""
    return ticket_service.get_seller_tickets(db, seller_id, skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Busca um ingresso específico por ID"""
    db_ticket = ticket_service.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingresso não encontrado"
        )
    return db_ticket


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Atualiza informações de um ingresso"""
    try:
        db_ticket = ticket_service.update_ticket(db, ticket_id, ticket_update, seller_id)
        if not db_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingresso não encontrado"
            )
        return db_ticket
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
def cancel_ticket(
    ticket_id: int,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Cancela um ingresso (remove da venda)"""
    try:
        db_ticket = ticket_service.cancel_ticket(db, ticket_id, seller_id)
        if not db_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingresso não encontrado"
            )
        return db_ticket
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
