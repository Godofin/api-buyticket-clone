from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Ticket, Event, TicketStatus
from app.schemas.schemas import TicketCreate, TicketUpdate
from typing import Optional, List
import secrets


def generate_verification_code() -> str:
    """Gera um código de verificação único para o ingresso"""
    return secrets.token_urlsafe(16)


def create_ticket(db: Session, ticket: TicketCreate, seller_id: int) -> Ticket:
    """Cria um novo ingresso para venda"""
    # Valida se o preço não excede 110% do original
    max_price = ticket.original_price * 1.10
    if ticket.selling_price > max_price:
        raise ValueError(f"Preço de venda não pode exceder 110% do preço original")
    
    db_ticket = Ticket(
        event_id=ticket.event_id,
        seller_id=seller_id,
        section=ticket.section,
        row=ticket.row,
        seat_number=ticket.seat_number,
        original_price=ticket.original_price,
        selling_price=ticket.selling_price,
        proof_of_purchase=ticket.proof_of_purchase,
        verification_code=generate_verification_code(),
        status=TicketStatus.AVAILABLE
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Busca um ingresso por ID"""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = None,
    status: Optional[TicketStatus] = None,
    seller_id: Optional[int] = None
) -> List[Ticket]:
    """Lista ingressos com filtros opcionais"""
    query = db.query(Ticket)
    
    if event_id:
        query = query.filter(Ticket.event_id == event_id)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if seller_id:
        query = query.filter(Ticket.seller_id == seller_id)
    
    return query.offset(skip).limit(limit).all()


def get_available_tickets(
    db: Session,
    event_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Ticket]:
    """Lista ingressos disponíveis para compra"""
    query = db.query(Ticket).filter(Ticket.status == TicketStatus.AVAILABLE)
    
    if event_id:
        query = query.filter(Ticket.event_id == event_id)
    
    return query.order_by(Ticket.selling_price.asc()).offset(skip).limit(limit).all()


def get_seller_tickets(
    db: Session,
    seller_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Ticket]:
    """Lista todos os ingressos de um vendedor"""
    return db.query(Ticket)\
        .filter(Ticket.seller_id == seller_id)\
        .order_by(Ticket.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate, seller_id: int) -> Optional[Ticket]:
    """Atualiza informações de um ingresso"""
    db_ticket = get_ticket(db, ticket_id)
    
    if not db_ticket:
        return None
    
    # Verifica se o usuário é o dono do ingresso
    if db_ticket.seller_id != seller_id:
        raise PermissionError("Você não tem permissão para editar este ingresso")
    
    # Não permite editar ingressos vendidos
    if db_ticket.status == TicketStatus.SOLD:
        raise ValueError("Não é possível editar ingressos já vendidos")
    
    update_data = ticket_update.dict(exclude_unset=True)
    
    # Valida preço se estiver sendo atualizado
    if 'selling_price' in update_data:
        max_price = db_ticket.original_price * 1.10
        if update_data['selling_price'] > max_price:
            raise ValueError(f"Preço de venda não pode exceder 110% do preço original")
    
    for field, value in update_data.items():
        setattr(db_ticket, field, value)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def cancel_ticket(db: Session, ticket_id: int, seller_id: int) -> Optional[Ticket]:
    """Cancela um ingresso (remove da venda)"""
    db_ticket = get_ticket(db, ticket_id)
    
    if not db_ticket:
        return None
    
    if db_ticket.seller_id != seller_id:
        raise PermissionError("Você não tem permissão para cancelar este ingresso")
    
    if db_ticket.status == TicketStatus.SOLD:
        raise ValueError("Não é possível cancelar ingressos já vendidos")
    
    db_ticket.status = TicketStatus.CANCELLED
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def reserve_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Reserva um ingresso temporariamente durante o processo de compra"""
    db_ticket = get_ticket(db, ticket_id)
    
    if not db_ticket:
        return None
    
    if db_ticket.status != TicketStatus.AVAILABLE:
        raise ValueError("Este ingresso não está disponível para compra")
    
    db_ticket.status = TicketStatus.RESERVED
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def mark_ticket_as_sold(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Marca um ingresso como vendido"""
    db_ticket = get_ticket(db, ticket_id)
    
    if not db_ticket:
        return None
    
    db_ticket.status = TicketStatus.SOLD
    db.commit()
    db.refresh(db_ticket)
    return db_ticket
