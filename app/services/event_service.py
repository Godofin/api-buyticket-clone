from sqlalchemy.orm import Session
from app.models.models import Event, EventTicketMaster
from app.schemas.schemas import EventCreate, EventUpdate, EventTicketMasterCreate
from typing import Optional, List
from datetime import datetime


# ==================== EVENTS ====================

def create_event(db: Session, event: EventCreate) -> Event:
    """Cria um novo evento"""
    db_event = Event(
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        venue=event.venue,
        image_banner_url=event.image_banner_url
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_event(db: Session, event_id: int) -> Optional[Event]:
    """Busca evento por ID"""
    return db.query(Event).filter(Event.id == event_id).first()


def get_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True
) -> List[Event]:
    """Lista eventos com filtros"""
    query = db.query(Event)
    
    if active_only:
        query = query.filter(Event.is_active == True)
    
    if search:
        query = query.filter(
            (Event.title.ilike(f"%{search}%")) |
            (Event.venue.ilike(f"%{search}%"))
        )
    
    return query.order_by(Event.event_date.asc()).offset(skip).limit(limit).all()


def get_upcoming_events(db: Session, skip: int = 0, limit: int = 100) -> List[Event]:
    """Lista eventos futuros"""
    now = datetime.utcnow()
    return db.query(Event)\
        .filter(Event.is_active == True)\
        .filter(Event.event_date > now)\
        .order_by(Event.event_date.asc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_event(db: Session, event_id: int, event_update: EventUpdate) -> Optional[Event]:
    """Atualiza evento"""
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    
    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event


def deactivate_event(db: Session, event_id: int) -> Optional[Event]:
    """Desativa evento"""
    db_event = get_event(db, event_id)
    if not db_event:
        return None
    
    db_event.is_active = False
    db.commit()
    db.refresh(db_event)
    return db_event


# ==================== EVENT TICKET MASTER ====================

def create_ticket_master(db: Session, ticket_master: EventTicketMasterCreate) -> EventTicketMaster:
    """Cria categoria de ingresso com preço oficial"""
    db_ticket_master = EventTicketMaster(
        event_id=ticket_master.event_id,
        category_name=ticket_master.category_name,
        face_value=ticket_master.face_value
    )
    db.add(db_ticket_master)
    db.commit()
    db.refresh(db_ticket_master)
    return db_ticket_master


def get_ticket_master(db: Session, ticket_master_id: int) -> Optional[EventTicketMaster]:
    """Busca ticket master por ID"""
    return db.query(EventTicketMaster).filter(EventTicketMaster.id == ticket_master_id).first()


def get_ticket_masters_by_event(db: Session, event_id: int) -> List[EventTicketMaster]:
    """Lista todas as categorias de ingresso de um evento"""
    return db.query(EventTicketMaster)\
        .filter(EventTicketMaster.event_id == event_id)\
        .all()


def get_max_allowed_price(db: Session, ticket_master_id: int) -> Optional[float]:
    """Calcula o preço máximo permitido (face_value * 1.20)"""
    ticket_master = get_ticket_master(db, ticket_master_id)
    if not ticket_master:
        return None
    
    return ticket_master.face_value * 1.20
