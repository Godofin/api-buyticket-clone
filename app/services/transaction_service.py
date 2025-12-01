from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.models import Transaction, Ticket, TransactionStatus, TicketStatus
from app.schemas.schemas import TransactionCreate, SellerStats, BuyerStats
from app.services import ticket_service
from typing import Optional, List
from datetime import datetime
import secrets


PLATFORM_FEE_PERCENTAGE = 0.05  # 5% de taxa da plataforma


def generate_payment_id() -> str:
    """Gera um ID único para o pagamento"""
    return f"PAY-{secrets.token_urlsafe(12)}"


def create_transaction(db: Session, transaction: TransactionCreate, buyer_id: int) -> Transaction:
    """Cria uma nova transação de compra"""
    # Busca o ingresso
    ticket = ticket_service.get_ticket(db, transaction.ticket_id)
    
    if not ticket:
        raise ValueError("Ingresso não encontrado")
    
    if ticket.status != TicketStatus.AVAILABLE:
        raise ValueError("Este ingresso não está disponível para compra")
    
    if ticket.seller_id == buyer_id:
        raise ValueError("Você não pode comprar seu próprio ingresso")
    
    # Reserva o ingresso
    ticket_service.reserve_ticket(db, ticket.id)
    
    # Calcula valores
    amount = ticket.selling_price
    platform_fee = amount * PLATFORM_FEE_PERCENTAGE
    total_amount = amount + platform_fee
    
    # Cria a transação
    db_transaction = Transaction(
        ticket_id=ticket.id,
        buyer_id=buyer_id,
        seller_id=ticket.seller_id,
        amount=amount,
        platform_fee=platform_fee,
        total_amount=total_amount,
        status=TransactionStatus.PENDING,
        payment_method=transaction.payment_method,
        payment_id=generate_payment_id()
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Busca uma transação por ID"""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_user_transactions(
    db: Session,
    user_id: int,
    as_buyer: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[Transaction]:
    """Lista transações de um usuário (como comprador ou vendedor)"""
    if as_buyer:
        query = db.query(Transaction).filter(Transaction.buyer_id == user_id)
    else:
        query = db.query(Transaction).filter(Transaction.seller_id == user_id)
    
    return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()


def complete_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    """Completa uma transação (simula pagamento aprovado)"""
    db_transaction = get_transaction(db, transaction_id)
    
    if not db_transaction:
        return None
    
    if db_transaction.status != TransactionStatus.PENDING:
        raise ValueError("Esta transação não está pendente")
    
    # Atualiza status da transação
    db_transaction.status = TransactionStatus.COMPLETED
    db_transaction.completed_at = datetime.utcnow()
    
    # Marca o ingresso como vendido
    ticket_service.mark_ticket_as_sold(db, db_transaction.ticket_id)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def cancel_transaction(db: Session, transaction_id: int, user_id: int) -> Optional[Transaction]:
    """Cancela uma transação pendente"""
    db_transaction = get_transaction(db, transaction_id)
    
    if not db_transaction:
        return None
    
    # Verifica se o usuário tem permissão (comprador ou vendedor)
    if db_transaction.buyer_id != user_id and db_transaction.seller_id != user_id:
        raise PermissionError("Você não tem permissão para cancelar esta transação")
    
    if db_transaction.status != TransactionStatus.PENDING:
        raise ValueError("Apenas transações pendentes podem ser canceladas")
    
    # Atualiza status da transação
    db_transaction.status = TransactionStatus.CANCELLED
    
    # Libera o ingresso novamente
    ticket = ticket_service.get_ticket(db, db_transaction.ticket_id)
    if ticket:
        ticket.status = TicketStatus.AVAILABLE
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_seller_statistics(db: Session, seller_id: int) -> SellerStats:
    """Retorna estatísticas de vendas de um vendedor"""
    from app.models.models import Ticket
    
    # Total de ingressos listados
    total_tickets = db.query(func.count(Ticket.id))\
        .filter(Ticket.seller_id == seller_id)\
        .scalar()
    
    # Ingressos vendidos
    tickets_sold = db.query(func.count(Ticket.id))\
        .filter(and_(Ticket.seller_id == seller_id, Ticket.status == TicketStatus.SOLD))\
        .scalar()
    
    # Ingressos disponíveis
    tickets_available = db.query(func.count(Ticket.id))\
        .filter(and_(Ticket.seller_id == seller_id, Ticket.status == TicketStatus.AVAILABLE))\
        .scalar()
    
    # Receita total (transações completadas)
    total_revenue = db.query(func.sum(Transaction.amount))\
        .filter(and_(
            Transaction.seller_id == seller_id,
            Transaction.status == TransactionStatus.COMPLETED
        ))\
        .scalar() or 0.0
    
    # Transações pendentes
    pending_transactions = db.query(func.count(Transaction.id))\
        .filter(and_(
            Transaction.seller_id == seller_id,
            Transaction.status == TransactionStatus.PENDING
        ))\
        .scalar()
    
    return SellerStats(
        total_tickets_listed=total_tickets or 0,
        tickets_sold=tickets_sold or 0,
        tickets_available=tickets_available or 0,
        total_revenue=float(total_revenue),
        pending_transactions=pending_transactions or 0
    )


def get_buyer_statistics(db: Session, buyer_id: int) -> BuyerStats:
    """Retorna estatísticas de compras de um comprador"""
    # Total de compras
    total_purchases = db.query(func.count(Transaction.id))\
        .filter(Transaction.buyer_id == buyer_id)\
        .scalar()
    
    # Total gasto (transações completadas)
    total_spent = db.query(func.sum(Transaction.total_amount))\
        .filter(and_(
            Transaction.buyer_id == buyer_id,
            Transaction.status == TransactionStatus.COMPLETED
        ))\
        .scalar() or 0.0
    
    # Transações pendentes
    pending_transactions = db.query(func.count(Transaction.id))\
        .filter(and_(
            Transaction.buyer_id == buyer_id,
            Transaction.status == TransactionStatus.PENDING
        ))\
        .scalar()
    
    # Transações completadas
    completed_transactions = db.query(func.count(Transaction.id))\
        .filter(and_(
            Transaction.buyer_id == buyer_id,
            Transaction.status == TransactionStatus.COMPLETED
        ))\
        .scalar()
    
    return BuyerStats(
        total_purchases=total_purchases or 0,
        total_spent=float(total_spent),
        pending_transactions=pending_transactions or 0,
        completed_transactions=completed_transactions or 0
    )
