from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.schemas import (
    EventCreate, EventUpdate, EventResponse,
    EventTicketMasterCreate, EventTicketMasterResponse
)
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


# ==================== EVENTS ====================

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Cria novo evento (ADMIN)"""
    return event_service.create_event(db, event)


@router.get("/", response_model=List[EventResponse])
def list_events(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Buscar por título ou local"),
    active_only: bool = Query(True, description="Apenas eventos ativos"),
    db: Session = Depends(get_db)
):
    """Lista eventos"""
    return event_service.get_events(db, skip=skip, limit=limit, search=search, active_only=active_only)


@router.get("/upcoming", response_model=List[EventResponse])
def list_upcoming_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista eventos futuros"""
    return event_service.get_upcoming_events(db, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Busca evento por ID"""
    db_event = event_service.get_event(db, event_id)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    return db_event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    """Atualiza evento (ADMIN)"""
    db_event = event_service.update_event(db, event_id, event_update)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    return db_event


@router.post("/{event_id}/deactivate", response_model=EventResponse)
def deactivate_event(event_id: int, db: Session = Depends(get_db)):
    """Desativa evento (ADMIN)"""
    db_event = event_service.deactivate_event(db, event_id)
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    return db_event


# ==================== TICKET MASTERS ====================

@router.post("/ticket-masters", response_model=EventTicketMasterResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_master(ticket_master: EventTicketMasterCreate, db: Session = Depends(get_db)):
    """Cria categoria de ingresso com preço oficial (ADMIN)"""
    # Verifica se evento existe
    if not event_service.get_event(db, ticket_master.event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    db_ticket_master = event_service.create_ticket_master(db, ticket_master)
    
    # Adiciona campo calculado
    response = EventTicketMasterResponse.from_orm(db_ticket_master)
    response.max_allowed_price = db_ticket_master.face_value * 1.20
    
    return response


@router.get("/ticket-masters/{ticket_master_id}", response_model=EventTicketMasterResponse)
def get_ticket_master(ticket_master_id: int, db: Session = Depends(get_db)):
    """Busca ticket master por ID"""
    db_ticket_master = event_service.get_ticket_master(db, ticket_master_id)
    if not db_ticket_master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria de ingresso não encontrada"
        )
    
    response = EventTicketMasterResponse.from_orm(db_ticket_master)
    response.max_allowed_price = db_ticket_master.face_value * 1.20
    
    return response


@router.get("/{event_id}/ticket-masters", response_model=List[EventTicketMasterResponse])
def list_event_ticket_masters(event_id: int, db: Session = Depends(get_db)):
    """Lista categorias de ingresso de um evento"""
    ticket_masters = event_service.get_ticket_masters_by_event(db, event_id)
    
    responses = []
    for tm in ticket_masters:
        response = EventTicketMasterResponse.from_orm(tm)
        response.max_allowed_price = tm.face_value * 1.20
        responses.append(response)
    
    return responses
