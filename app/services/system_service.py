from sqlalchemy.orm import Session
from app.models.models import SystemLog, Dispute, DisputeStatus
from app.schemas.schemas import SystemLogCreate, DisputeCreate, DisputeUpdate
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== SYSTEM LOGS ====================

def create_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> SystemLog:
    """Cria log de auditoria"""
    db_log = SystemLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        log_metadata=metadata
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_logs(
    db: Session,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[SystemLog]:
    """Lista logs com filtro opcional por usuário"""
    query = db.query(SystemLog)
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    return query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()


def get_recent_suspicious_activities(db: Session, limit: int = 50) -> List[SystemLog]:
    """Lista atividades suspeitas recentes"""
    return db.query(SystemLog)\
        .filter(SystemLog.action.ilike('%suspeita%'))\
        .order_by(SystemLog.created_at.desc())\
        .limit(limit)\
        .all()


# ==================== DISPUTES ====================

def create_dispute(db: Session, reporter_id: int, dispute: DisputeCreate) -> Dispute:
    """Cria disputa/denúncia"""
    # Verifica se não está denunciando a si mesmo
    if reporter_id == dispute.reported_user_id:
        raise ValueError("Você não pode denunciar a si mesmo")
    
    db_dispute = Dispute(
        order_id=dispute.order_id,
        reporter_id=reporter_id,
        reported_user_id=dispute.reported_user_id,
        reason=dispute.reason,
        status=DisputeStatus.OPEN
    )
    
    db.add(db_dispute)
    db.commit()
    db.refresh(db_dispute)
    
    # Cria log
    create_log(
        db,
        action=f"Disputa criada contra usuário {dispute.reported_user_id}",
        user_id=reporter_id,
        metadata={"dispute_id": db_dispute.id, "reason": dispute.reason}
    )
    
    # Se houver order_id, marca escrow como disputa
    if dispute.order_id:
        from app.services import order_service
        try:
            order_service.mark_escrow_as_dispute(db, dispute.order_id)
        except:
            pass  # Escrow já pode estar em outro estado
    
    return db_dispute


def get_dispute(db: Session, dispute_id: int) -> Optional[Dispute]:
    """Busca disputa por ID"""
    return db.query(Dispute).filter(Dispute.id == dispute_id).first()


def get_disputes(
    db: Session,
    status: Optional[DisputeStatus] = None,
    reported_user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dispute]:
    """Lista disputas com filtros"""
    query = db.query(Dispute)
    
    if status:
        query = query.filter(Dispute.status == status)
    
    if reported_user_id:
        query = query.filter(Dispute.reported_user_id == reported_user_id)
    
    return query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()


def get_open_disputes(db: Session, skip: int = 0, limit: int = 100) -> List[Dispute]:
    """Lista disputas abertas"""
    return get_disputes(db, status=DisputeStatus.OPEN, skip=skip, limit=limit)


def get_user_disputes(
    db: Session,
    user_id: int,
    as_reporter: bool = True,
    skip: int = 0,
    limit: int = 100
) -> List[Dispute]:
    """Lista disputas de um usuário"""
    query = db.query(Dispute)
    
    if as_reporter:
        query = query.filter(Dispute.reporter_id == user_id)
    else:
        query = query.filter(Dispute.reported_user_id == user_id)
    
    return query.order_by(Dispute.created_at.desc()).offset(skip).limit(limit).all()


def update_dispute(
    db: Session,
    dispute_id: int,
    dispute_update: DisputeUpdate
) -> Optional[Dispute]:
    """Atualiza disputa (admin)"""
    db_dispute = get_dispute(db, dispute_id)
    if not db_dispute:
        return None
    
    update_data = dispute_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_dispute, field, value)
    
    # Se está resolvendo, marca data
    if 'status' in update_data and update_data['status'] == DisputeStatus.RESOLVED:
        db_dispute.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_dispute)
    
    # Cria log
    create_log(
        db,
        action=f"Disputa {dispute_id} atualizada",
        metadata={"dispute_id": dispute_id, "updates": update_data}
    )
    
    return db_dispute


def resolve_dispute(
    db: Session,
    dispute_id: int,
    admin_notes: str,
    refund_buyer: bool = False
) -> Optional[Dispute]:
    """Resolve disputa com decisão"""
    db_dispute = get_dispute(db, dispute_id)
    if not db_dispute:
        return None
    
    db_dispute.status = DisputeStatus.RESOLVED
    db_dispute.admin_notes = admin_notes
    db_dispute.resolved_at = datetime.utcnow()
    
    # Se decidir reembolsar
    if refund_buyer and db_dispute.order_id:
        from app.services import order_service
        order_service.refund_order(db, db_dispute.order_id)
    
    # Se não reembolsar, libera para vendedor
    elif db_dispute.order_id:
        from app.services import order_service
        try:
            order_service.release_escrow_to_seller(db, db_dispute.order_id)
        except:
            pass  # Pode já ter sido liberado
    
    db.commit()
    db.refresh(db_dispute)
    
    # Cria log
    create_log(
        db,
        action=f"Disputa {dispute_id} resolvida",
        metadata={
            "dispute_id": dispute_id,
            "refund_buyer": refund_buyer,
            "admin_notes": admin_notes
        }
    )
    
    return db_dispute


def get_user_reputation_impact(db: Session, user_id: int) -> Dict[str, Any]:
    """Analisa impacto de disputas na reputação"""
    total_disputes = db.query(Dispute)\
        .filter(Dispute.reported_user_id == user_id)\
        .count()
    
    resolved_against = db.query(Dispute)\
        .filter(
            Dispute.reported_user_id == user_id,
            Dispute.status == DisputeStatus.RESOLVED,
            Dispute.admin_notes.ilike('%procedente%')
        )\
        .count()
    
    return {
        "total_disputes": total_disputes,
        "resolved_against": resolved_against,
        "reputation_penalty": resolved_against * -5.0
    }
