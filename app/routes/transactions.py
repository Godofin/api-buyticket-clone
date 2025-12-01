from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionDetailResponse,
    SellerStats,
    BuyerStats
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate,
    buyer_id: int = Query(..., description="ID do comprador"),
    db: Session = Depends(get_db)
):
    """Cria uma nova transação de compra"""
    try:
        return transaction_service.create_transaction(db, transaction, buyer_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Busca uma transação específica por ID"""
    db_transaction = transaction_service.get_transaction(db, transaction_id)
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada"
        )
    return db_transaction


@router.get("/user/{user_id}/purchases", response_model=List[TransactionResponse])
def list_user_purchases(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista compras de um usuário"""
    return transaction_service.get_user_transactions(
        db, user_id, as_buyer=True, skip=skip, limit=limit
    )


@router.get("/user/{user_id}/sales", response_model=List[TransactionResponse])
def list_user_sales(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista vendas de um usuário"""
    return transaction_service.get_user_transactions(
        db, user_id, as_buyer=False, skip=skip, limit=limit
    )


@router.post("/{transaction_id}/complete", response_model=TransactionResponse)
def complete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Completa uma transação (simula pagamento aprovado)"""
    try:
        db_transaction = transaction_service.complete_transaction(db, transaction_id)
        if not db_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        return db_transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{transaction_id}/cancel", response_model=TransactionResponse)
def cancel_transaction(
    transaction_id: int,
    user_id: int = Query(..., description="ID do usuário (comprador ou vendedor)"),
    db: Session = Depends(get_db)
):
    """Cancela uma transação pendente"""
    try:
        db_transaction = transaction_service.cancel_transaction(db, transaction_id, user_id)
        if not db_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )
        return db_transaction
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


@router.get("/stats/seller/{seller_id}", response_model=SellerStats)
def get_seller_statistics(seller_id: int, db: Session = Depends(get_db)):
    """Retorna estatísticas de vendas de um vendedor"""
    return transaction_service.get_seller_statistics(db, seller_id)


@router.get("/stats/buyer/{buyer_id}", response_model=BuyerStats)
def get_buyer_statistics(buyer_id: int, db: Session = Depends(get_db)):
    """Retorna estatísticas de compras de um comprador"""
    return transaction_service.get_buyer_statistics(db, buyer_id)
