from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.schemas import (
    DisputeCreate, DisputeUpdate, DisputeResponse,
    SystemLogResponse, DisputeStatus
)
from app.services import system_service

router = APIRouter(prefix="/admin", tags=["admin"])


# ==================== DISPUTES ====================

@router.post("/disputes", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
def create_dispute(
    dispute: DisputeCreate,
    reporter_id: int = Query(..., description="ID do denunciante"),
    db: Session = Depends(get_db)
):
    """Cria disputa/denúncia"""
    try:
        return system_service.create_dispute(db, reporter_id, dispute)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/disputes", response_model=List[DisputeResponse])
def list_disputes(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DisputeStatus] = Query(None, alias="status", description="Filtrar por status"),
    reported_user_id: Optional[int] = Query(None, description="Filtrar por usuário denunciado"),
    db: Session = Depends(get_db)
):
    """Lista disputas (ADMIN)"""
    return system_service.get_disputes(
        db,
        status=status_filter,
        reported_user_id=reported_user_id,
        skip=skip,
        limit=limit
    )


@router.get("/disputes/open", response_model=List[DisputeResponse])
def list_open_disputes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista disputas abertas (ADMIN)"""
    return system_service.get_open_disputes(db, skip=skip, limit=limit)


@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
def get_dispute(dispute_id: int, db: Session = Depends(get_db)):
    """Busca disputa por ID"""
    db_dispute = system_service.get_dispute(db, dispute_id)
    if not db_dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disputa não encontrada"
        )
    return db_dispute


@router.get("/disputes/user/{user_id}/reported", response_model=List[DisputeResponse])
def list_user_disputes_reported(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista disputas feitas por um usuário"""
    return system_service.get_user_disputes(db, user_id, as_reporter=True, skip=skip, limit=limit)


@router.get("/disputes/user/{user_id}/received", response_model=List[DisputeResponse])
def list_user_disputes_received(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista disputas contra um usuário"""
    return system_service.get_user_disputes(db, user_id, as_reporter=False, skip=skip, limit=limit)


@router.put("/disputes/{dispute_id}", response_model=DisputeResponse)
def update_dispute(
    dispute_id: int,
    dispute_update: DisputeUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza disputa (ADMIN)"""
    db_dispute = system_service.update_dispute(db, dispute_id, dispute_update)
    if not db_dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disputa não encontrada"
        )
    return db_dispute


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
def resolve_dispute(
    dispute_id: int,
    admin_notes: str = Query(..., description="Notas do admin"),
    refund_buyer: bool = Query(False, description="Reembolsar comprador?"),
    db: Session = Depends(get_db)
):
    """Resolve disputa com decisão (ADMIN)"""
    db_dispute = system_service.resolve_dispute(db, dispute_id, admin_notes, refund_buyer)
    if not db_dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disputa não encontrada"
        )
    return db_dispute


# ==================== SYSTEM LOGS ====================

@router.get("/logs", response_model=List[SystemLogResponse])
def list_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filtrar por usuário"),
    db: Session = Depends(get_db)
):
    """Lista logs de auditoria (ADMIN)"""
    return system_service.get_logs(db, user_id=user_id, skip=skip, limit=limit)


@router.get("/logs/suspicious", response_model=List[SystemLogResponse])
def list_suspicious_activities(limit: int = 50, db: Session = Depends(get_db)):
    """Lista atividades suspeitas recentes (ADMIN)"""
    return system_service.get_recent_suspicious_activities(db, limit=limit)


@router.get("/users/{user_id}/reputation-impact")
def get_user_reputation_impact(user_id: int, db: Session = Depends(get_db)):
    """Analisa impacto de disputas na reputação (ADMIN)"""
    return system_service.get_user_reputation_impact(db, user_id)
