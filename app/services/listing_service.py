from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Listing, ListingStatus
from app.schemas.schemas import ListingCreate, ListingUpdate
from app.services import event_service
from typing import Optional, List


def validate_price(db: Session, ticket_master_id: int, price_asked: float) -> bool:
    """Valida se o preço pedido está dentro do limite de 20%"""
    max_price = event_service.get_max_allowed_price(db, ticket_master_id)
    if max_price is None:
        return False
    
    return price_asked <= max_price


def create_listing(db: Session, seller_id: int, listing: ListingCreate) -> Listing:
    """Cria anúncio de venda com validação de preço"""
    # Validação da regra dos 20%
    if not validate_price(db, listing.event_ticket_master_id, listing.price_asked):
        ticket_master = event_service.get_ticket_master(db, listing.event_ticket_master_id)
        max_price = ticket_master.face_value * 1.20 if ticket_master else 0
        raise ValueError(
            f"Preço excede o limite permitido. "
            f"Valor original: R$ {ticket_master.face_value:.2f}, "
            f"Máximo permitido (120%): R$ {max_price:.2f}"
        )
    
    db_listing = Listing(
        seller_id=seller_id,
        event_ticket_master_id=listing.event_ticket_master_id,
        price_asked=listing.price_asked,
        ticket_proof_image_url=listing.ticket_proof_image_url,
        ticket_file_url=listing.ticket_file_url,
        description=listing.description,
        status=ListingStatus.ACTIVE
    )
    
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


def get_listing(db: Session, listing_id: int) -> Optional[Listing]:
    """Busca listing por ID"""
    return db.query(Listing).filter(Listing.id == listing_id).first()


def get_listings(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = None,
    status: Optional[ListingStatus] = None,
    seller_id: Optional[int] = None
) -> List[Listing]:
    """Lista listings com filtros"""
    query = db.query(Listing)
    
    if event_id:
        # Join com ticket_master para filtrar por evento
        from app.models.models import EventTicketMaster
        query = query.join(EventTicketMaster).filter(EventTicketMaster.event_id == event_id)
    
    if status:
        query = query.filter(Listing.status == status)
    
    if seller_id:
        query = query.filter(Listing.seller_id == seller_id)
    
    return query.order_by(Listing.created_at.desc()).offset(skip).limit(limit).all()


def get_active_listings(
    db: Session,
    event_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Listing]:
    """Lista apenas listings ativos"""
    return get_listings(
        db,
        skip=skip,
        limit=limit,
        event_id=event_id,
        status=ListingStatus.ACTIVE
    )


def get_seller_listings(db: Session, seller_id: int, skip: int = 0, limit: int = 100) -> List[Listing]:
    """Lista todos os listings de um vendedor"""
    return get_listings(db, skip=skip, limit=limit, seller_id=seller_id)


def update_listing(
    db: Session,
    listing_id: int,
    seller_id: int,
    listing_update: ListingUpdate
) -> Optional[Listing]:
    """Atualiza listing com validação de propriedade e preço"""
    db_listing = get_listing(db, listing_id)
    
    if not db_listing:
        return None
    
    # Verifica propriedade
    if db_listing.seller_id != seller_id:
        raise PermissionError("Você não tem permissão para editar este anúncio")
    
    # Não permite editar listings vendidos
    if db_listing.status == ListingStatus.SOLD:
        raise ValueError("Não é possível editar anúncios já vendidos")
    
    update_data = listing_update.dict(exclude_unset=True)
    
    # Valida novo preço se estiver sendo atualizado
    if 'price_asked' in update_data:
        if not validate_price(db, db_listing.event_ticket_master_id, update_data['price_asked']):
            ticket_master = event_service.get_ticket_master(db, db_listing.event_ticket_master_id)
            max_price = ticket_master.face_value * 1.20 if ticket_master else 0
            raise ValueError(f"Preço excede o limite de 120% (máximo: R$ {max_price:.2f})")
    
    for field, value in update_data.items():
        setattr(db_listing, field, value)
    
    db.commit()
    db.refresh(db_listing)
    return db_listing


def cancel_listing(db: Session, listing_id: int, seller_id: int) -> Optional[Listing]:
    """Cancela um listing"""
    db_listing = get_listing(db, listing_id)
    
    if not db_listing:
        return None
    
    if db_listing.seller_id != seller_id:
        raise PermissionError("Você não tem permissão para cancelar este anúncio")
    
    if db_listing.status == ListingStatus.SOLD:
        raise ValueError("Não é possível cancelar anúncios já vendidos")
    
    db_listing.status = ListingStatus.CANCELLED
    db.commit()
    db.refresh(db_listing)
    return db_listing


def reserve_listing(db: Session, listing_id: int) -> Optional[Listing]:
    """Reserva um listing durante compra"""
    db_listing = get_listing(db, listing_id)
    
    if not db_listing:
        return None
    
    if db_listing.status != ListingStatus.ACTIVE:
        raise ValueError("Este anúncio não está disponível")
    
    db_listing.status = ListingStatus.RESERVED
    db.commit()
    db.refresh(db_listing)
    return db_listing


def mark_as_sold(db: Session, listing_id: int) -> Optional[Listing]:
    """Marca listing como vendido"""
    db_listing = get_listing(db, listing_id)
    
    if not db_listing:
        return None
    
    db_listing.status = ListingStatus.SOLD
    db.commit()
    db.refresh(db_listing)
    return db_listing


def release_reservation(db: Session, listing_id: int) -> Optional[Listing]:
    """Libera reserva de um listing"""
    db_listing = get_listing(db, listing_id)
    
    if not db_listing:
        return None
    
    if db_listing.status == ListingStatus.RESERVED:
        db_listing.status = ListingStatus.ACTIVE
        db.commit()
        db.refresh(db_listing)
    
    return db_listing
