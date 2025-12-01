from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.schemas import ListingCreate, ListingUpdate, ListingResponse, ListingDetailResponse
from app.services import listing_service
from app.models.models import ListingStatus

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing: ListingCreate,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Cria anúncio de venda (valida regra dos 20%)"""
    try:
        return listing_service.create_listing(db, seller_id, listing)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ListingResponse])
def list_listings(
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    status_filter: Optional[ListingStatus] = Query(None, alias="status", description="Filtrar por status"),
    seller_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    db: Session = Depends(get_db)
):
    """Lista anúncios com filtros"""
    return listing_service.get_listings(
        db,
        skip=skip,
        limit=limit,
        event_id=event_id,
        status=status_filter,
        seller_id=seller_id
    )


@router.get("/active", response_model=List[ListingResponse])
def list_active_listings(
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    db: Session = Depends(get_db)
):
    """Lista apenas anúncios ativos"""
    return listing_service.get_active_listings(db, event_id=event_id, skip=skip, limit=limit)


@router.get("/seller/{seller_id}", response_model=List[ListingResponse])
def list_seller_listings(
    seller_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista anúncios de um vendedor"""
    return listing_service.get_seller_listings(db, seller_id, skip=skip, limit=limit)


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Busca anúncio por ID"""
    db_listing = listing_service.get_listing(db, listing_id)
    if not db_listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado"
        )
    return db_listing


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    listing_update: ListingUpdate,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Atualiza anúncio (valida regra dos 20%)"""
    try:
        db_listing = listing_service.update_listing(db, listing_id, seller_id, listing_update)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Anúncio não encontrado"
            )
        return db_listing
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


@router.post("/{listing_id}/cancel", response_model=ListingResponse)
def cancel_listing(
    listing_id: int,
    seller_id: int = Query(..., description="ID do vendedor"),
    db: Session = Depends(get_db)
):
    """Cancela anúncio"""
    try:
        db_listing = listing_service.cancel_listing(db, listing_id, seller_id)
        if not db_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Anúncio não encontrado"
            )
        return db_listing
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
