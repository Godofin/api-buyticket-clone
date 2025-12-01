from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import OrderCreate, OrderResponse, OrderDetailResponse, SellerStats, BuyerStats
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    buyer_id: int = Query(..., description="ID do comprador"),
    db: Session = Depends(get_db)
):
    """Cria pedido (dinheiro em escrow)"""
    try:
        return order_service.create_order(db, buyer_id, order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Busca pedido por ID"""
    db_order = order_service.get_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    return db_order


@router.get("/user/{user_id}/purchases", response_model=List[OrderResponse])
def list_user_purchases(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista compras de um usuário"""
    return order_service.get_user_orders(db, user_id, as_buyer=True, skip=skip, limit=limit)


@router.get("/user/{user_id}/sales", response_model=List[OrderResponse])
def list_user_sales(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista vendas de um usuário"""
    return order_service.get_user_orders(db, user_id, as_buyer=False, skip=skip, limit=limit)


@router.post("/{order_id}/complete-payment", response_model=OrderResponse)
def complete_payment(order_id: int, db: Session = Depends(get_db)):
    """Completa pagamento (dinheiro ainda em escrow)"""
    try:
        db_order = order_service.complete_payment(db, order_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        return db_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/release-escrow", response_model=OrderResponse)
def release_escrow(order_id: int, db: Session = Depends(get_db)):
    """Libera dinheiro do escrow para vendedor"""
    try:
        db_order = order_service.release_escrow_to_seller(db, order_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        return db_order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    user_id: int = Query(..., description="ID do usuário (comprador ou vendedor)"),
    db: Session = Depends(get_db)
):
    """Cancela pedido"""
    try:
        db_order = order_service.cancel_order(db, order_id, user_id)
        if not db_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido não encontrado"
            )
        return db_order
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


@router.post("/{order_id}/refund", response_model=OrderResponse)
def refund_order(order_id: int, db: Session = Depends(get_db)):
    """Reembolsa pedido (ADMIN)"""
    db_order = order_service.refund_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    return db_order


# ==================== STATISTICS ====================

@router.get("/stats/seller/{seller_id}", response_model=SellerStats)
def get_seller_statistics(seller_id: int, db: Session = Depends(get_db)):
    """Estatísticas do vendedor"""
    return order_service.get_seller_statistics(db, seller_id)


@router.get("/stats/buyer/{buyer_id}", response_model=BuyerStats)
def get_buyer_statistics(buyer_id: int, db: Session = Depends(get_db)):
    """Estatísticas do comprador"""
    return order_service.get_buyer_statistics(db, buyer_id)
