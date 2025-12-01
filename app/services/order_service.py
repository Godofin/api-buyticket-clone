from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.models import Order, PaymentStatus, EscrowStatus, Listing
from app.schemas.schemas import OrderCreate, SellerStats, BuyerStats
from app.services import listing_service
from typing import Optional, List
from datetime import datetime
import secrets


PLATFORM_FEE_PERCENTAGE = 0.05  # 5% de taxa


def generate_payment_id() -> str:
    """Gera ID único de pagamento"""
    return f"PAY-{secrets.token_urlsafe(12)}"


def create_order(db: Session, buyer_id: int, order: OrderCreate) -> Order:
    """Cria pedido com escrow"""
    # Busca listing
    listing = listing_service.get_listing(db, order.listing_id)
    
    if not listing:
        raise ValueError("Anúncio não encontrado")
    
    from app.models.models import ListingStatus
    if listing.status != ListingStatus.ACTIVE:
        raise ValueError("Este anúncio não está disponível")
    
    if listing.seller_id == buyer_id:
        raise ValueError("Você não pode comprar seu próprio anúncio")
    
    # Reserva o listing
    listing_service.reserve_listing(db, listing.id)
    
    # Calcula valores
    amount = listing.price_asked
    platform_fee = amount * PLATFORM_FEE_PERCENTAGE
    total_amount = amount + platform_fee
    
    # Cria order com escrow HELD
    db_order = Order(
        buyer_id=buyer_id,
        listing_id=listing.id,
        total_amount=total_amount,
        platform_fee=platform_fee,
        payment_status=PaymentStatus.PENDING,
        escrow_status=EscrowStatus.HELD,  # Dinheiro retido
        payment_method=order.payment_method,
        payment_id=generate_payment_id()
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Busca order por ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def get_user_orders(
    db: Session,
    user_id: int,
    as_buyer: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """Lista orders de um usuário"""
    if as_buyer:
        query = db.query(Order).filter(Order.buyer_id == user_id)
    else:
        # Busca através do listing
        query = db.query(Order).join(Listing).filter(Listing.seller_id == user_id)
    
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def complete_payment(db: Session, order_id: int) -> Optional[Order]:
    """Completa pagamento (dinheiro ainda em escrow)"""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    if db_order.payment_status != PaymentStatus.PENDING:
        raise ValueError("Este pedido não está pendente")
    
    db_order.payment_status = PaymentStatus.PAID
    db_order.completed_at = datetime.utcnow()
    
    # Marca listing como vendido
    listing_service.mark_as_sold(db, db_order.listing_id)
    
    db.commit()
    db.refresh(db_order)
    return db_order


def release_escrow_to_seller(db: Session, order_id: int) -> Optional[Order]:
    """Libera dinheiro do escrow para o vendedor"""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    if db_order.payment_status != PaymentStatus.PAID:
        raise ValueError("Pagamento ainda não foi completado")
    
    if db_order.escrow_status != EscrowStatus.HELD:
        raise ValueError("Escrow já foi processado")
    
    db_order.escrow_status = EscrowStatus.RELEASED_TO_SELLER
    
    # Atualiza reputação do vendedor
    listing = listing_service.get_listing(db, db_order.listing_id)
    if listing:
        from app.services import user_service
        user_service.update_reputation(db, listing.seller_id, 1.0)
    
    db.commit()
    db.refresh(db_order)
    return db_order


def mark_escrow_as_dispute(db: Session, order_id: int) -> Optional[Order]:
    """Marca escrow como em disputa"""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    if db_order.escrow_status != EscrowStatus.HELD:
        raise ValueError("Escrow já foi processado")
    
    db_order.escrow_status = EscrowStatus.DISPUTE
    
    db.commit()
    db.refresh(db_order)
    return db_order


def cancel_order(db: Session, order_id: int, user_id: int) -> Optional[Order]:
    """Cancela pedido e libera listing"""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    # Verifica permissão
    listing = listing_service.get_listing(db, db_order.listing_id)
    if not listing:
        return None
    
    if db_order.buyer_id != user_id and listing.seller_id != user_id:
        raise PermissionError("Você não tem permissão para cancelar este pedido")
    
    if db_order.payment_status == PaymentStatus.PAID:
        raise ValueError("Pedidos pagos não podem ser cancelados (abra uma disputa)")
    
    db_order.payment_status = PaymentStatus.REFUNDED
    
    # Libera listing
    listing_service.release_reservation(db, db_order.listing_id)
    
    db.commit()
    db.refresh(db_order)
    return db_order


def refund_order(db: Session, order_id: int) -> Optional[Order]:
    """Reembolsa pedido (admin)"""
    db_order = get_order(db, order_id)
    
    if not db_order:
        return None
    
    db_order.payment_status = PaymentStatus.REFUNDED
    db_order.escrow_status = EscrowStatus.HELD  # Mantém retido até processar reembolso
    
    # Libera listing
    listing_service.release_reservation(db, db_order.listing_id)
    
    db.commit()
    db.refresh(db_order)
    return db_order


# ==================== STATISTICS ====================

def get_seller_statistics(db: Session, seller_id: int) -> SellerStats:
    """Estatísticas do vendedor"""
    from app.models.models import ListingStatus
    
    total_listings = db.query(func.count(Listing.id))\
        .filter(Listing.seller_id == seller_id)\
        .scalar() or 0
    
    active_listings = db.query(func.count(Listing.id))\
        .filter(and_(Listing.seller_id == seller_id, Listing.status == ListingStatus.ACTIVE))\
        .scalar() or 0
    
    sold_listings = db.query(func.count(Listing.id))\
        .filter(and_(Listing.seller_id == seller_id, Listing.status == ListingStatus.SOLD))\
        .scalar() or 0
    
    # Receita liberada
    total_revenue = db.query(func.sum(Order.total_amount - Order.platform_fee))\
        .join(Listing)\
        .filter(and_(
            Listing.seller_id == seller_id,
            Order.payment_status == PaymentStatus.PAID,
            Order.escrow_status == EscrowStatus.RELEASED_TO_SELLER
        ))\
        .scalar() or 0.0
    
    # Reputação
    from app.services import user_service
    user = user_service.get_user(db, seller_id)
    reputation_score = user.reputation_score if user else 0.0
    
    return SellerStats(
        total_listings=total_listings,
        active_listings=active_listings,
        sold_listings=sold_listings,
        total_revenue=float(total_revenue),
        reputation_score=reputation_score
    )


def get_buyer_statistics(db: Session, buyer_id: int) -> BuyerStats:
    """Estatísticas do comprador"""
    total_purchases = db.query(func.count(Order.id))\
        .filter(Order.buyer_id == buyer_id)\
        .scalar() or 0
    
    total_spent = db.query(func.sum(Order.total_amount))\
        .filter(and_(
            Order.buyer_id == buyer_id,
            Order.payment_status == PaymentStatus.PAID
        ))\
        .scalar() or 0.0
    
    pending_orders = db.query(func.count(Order.id))\
        .filter(and_(
            Order.buyer_id == buyer_id,
            Order.payment_status == PaymentStatus.PENDING
        ))\
        .scalar() or 0
    
    completed_orders = db.query(func.count(Order.id))\
        .filter(and_(
            Order.buyer_id == buyer_id,
            Order.payment_status == PaymentStatus.PAID
        ))\
        .scalar() or 0
    
    return BuyerStats(
        total_purchases=total_purchases,
        total_spent=float(total_spent),
        pending_orders=pending_orders,
        completed_orders=completed_orders
    )
