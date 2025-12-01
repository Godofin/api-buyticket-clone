from sqlalchemy.orm import Session
from app.models.models import User, UserDocument
from app.schemas.schemas import UserCreate, UserUpdate, UserDocumentCreate
from typing import Optional, List
import hashlib


def hash_password(password: str) -> str:
    """Hash simples de senha (em produção usar bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(db: Session, user: UserCreate) -> User:
    """Cria um novo usuário"""
    db_user = User(
        full_name=user.full_name,
        cpf=user.cpf,
        email=user.email,
        password_hash=hash_password(user.password),
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Busca usuário por ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_cpf(db: Session, cpf: str) -> Optional[User]:
    """Busca usuário por CPF"""
    return db.query(User).filter(User.cpf == cpf).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Lista usuários"""
    return db.query(User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Atualiza usuário"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_phone(db: Session, user_id: int) -> Optional[User]:
    """Marca telefone como verificado"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.phone_verified = True
    db.commit()
    db.refresh(db_user)
    return db_user


def update_reputation(db: Session, user_id: int, score_change: float) -> Optional[User]:
    """Atualiza reputation score"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.reputation_score += score_change
    db.commit()
    db.refresh(db_user)
    return db_user


# ==================== USER DOCUMENTS ====================

def create_user_document(db: Session, user_id: int, document: UserDocumentCreate) -> UserDocument:
    """Cria documento de verificação"""
    db_document = UserDocument(
        user_id=user_id,
        document_type=document.document_type,
        front_image_url=document.front_image_url,
        back_image_url=document.back_image_url,
        selfie_url=document.selfie_url
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_user_documents(db: Session, user_id: int) -> List[UserDocument]:
    """Lista documentos de um usuário"""
    return db.query(UserDocument).filter(UserDocument.user_id == user_id).all()


def approve_document(db: Session, document_id: int) -> Optional[UserDocument]:
    """Aprova documento e marca usuário como verificado"""
    from app.models.models import DocumentStatus
    
    db_document = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not db_document:
        return None
    
    db_document.status = DocumentStatus.APPROVED
    
    # Marca usuário como identity_verified
    db_user = get_user(db, db_document.user_id)
    if db_user:
        db_user.identity_verified = True
    
    db.commit()
    db.refresh(db_document)
    return db_document


def reject_document(db: Session, document_id: int, reason: str) -> Optional[UserDocument]:
    """Rejeita documento"""
    from app.models.models import DocumentStatus
    
    db_document = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not db_document:
        return None
    
    db_document.status = DocumentStatus.REJECTED
    db_document.rejection_reason = reason
    
    db.commit()
    db.refresh(db_document)
    return db_document
