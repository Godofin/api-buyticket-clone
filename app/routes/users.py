from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse,
    UserDocumentCreate, UserDocumentResponse
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Cria novo usuário"""
    # Verifica email
    if user_service.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Verifica CPF
    if user_service.get_user_by_cpf(db, user.cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF já cadastrado"
        )
    
    return user_service.create_user(db, user)


@router.get("/", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista usuários"""
    return user_service.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Busca usuário por ID"""
    db_user = user_service.get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return db_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Atualiza usuário"""
    db_user = user_service.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return db_user


@router.post("/{user_id}/verify-phone", response_model=UserResponse)
def verify_phone(user_id: int, db: Session = Depends(get_db)):
    """Marca telefone como verificado"""
    db_user = user_service.verify_phone(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return db_user


# ==================== DOCUMENTOS ====================

@router.post("/{user_id}/documents", response_model=UserDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    user_id: int,
    document: UserDocumentCreate,
    db: Session = Depends(get_db)
):
    """Upload de documento para verificação KYC"""
    # Verifica se usuário existe
    if not user_service.get_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return user_service.create_user_document(db, user_id, document)


@router.get("/{user_id}/documents", response_model=List[UserDocumentResponse])
def list_user_documents(user_id: int, db: Session = Depends(get_db)):
    """Lista documentos de um usuário"""
    return user_service.get_user_documents(db, user_id)


@router.post("/documents/{document_id}/approve", response_model=UserDocumentResponse)
def approve_document(document_id: int, db: Session = Depends(get_db)):
    """Aprova documento (ADMIN)"""
    db_document = user_service.approve_document(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado"
        )
    return db_document


@router.post("/documents/{document_id}/reject", response_model=UserDocumentResponse)
def reject_document(document_id: int, reason: str, db: Session = Depends(get_db)):
    """Rejeita documento (ADMIN)"""
    db_document = user_service.reject_document(db, document_id, reason)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado"
        )
    return db_document
