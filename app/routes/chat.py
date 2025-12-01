from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.schemas import (
    ChatRoomCreate, ChatRoomResponse,
    ChatMessageCreate, ChatMessageResponse
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


# ==================== CHAT ROOMS ====================

@router.post("/rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
def create_chat_room(
    chat_room: ChatRoomCreate,
    buyer_id: int = Query(..., description="ID do comprador"),
    db: Session = Depends(get_db)
):
    """Cria sala de chat entre comprador e vendedor"""
    try:
        return chat_service.create_chat_room(db, buyer_id, chat_room)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/rooms/{chat_room_id}", response_model=ChatRoomResponse)
def get_chat_room(chat_room_id: int, db: Session = Depends(get_db)):
    """Busca sala de chat por ID"""
    db_chat_room = chat_service.get_chat_room(db, chat_room_id)
    if not db_chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat não encontrado"
        )
    return db_chat_room


@router.get("/rooms/user/{user_id}", response_model=List[ChatRoomResponse])
def list_user_chat_rooms(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista chats de um usuário"""
    return chat_service.get_user_chat_rooms(db, user_id, skip=skip, limit=limit)


@router.post("/rooms/{chat_room_id}/archive", response_model=ChatRoomResponse)
def archive_chat_room(chat_room_id: int, db: Session = Depends(get_db)):
    """Arquiva chat"""
    db_chat_room = chat_service.archive_chat_room(db, chat_room_id)
    if not db_chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat não encontrado"
        )
    return db_chat_room


@router.post("/rooms/{chat_room_id}/block", response_model=ChatRoomResponse)
def block_chat_room(chat_room_id: int, db: Session = Depends(get_db)):
    """Bloqueia chat (ADMIN)"""
    db_chat_room = chat_service.block_chat_room(db, chat_room_id)
    if not db_chat_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat não encontrado"
        )
    return db_chat_room


# ==================== CHAT MESSAGES ====================

@router.post("/rooms/{chat_room_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    chat_room_id: int,
    message: ChatMessageCreate,
    sender_id: int = Query(..., description="ID do remetente"),
    db: Session = Depends(get_db)
):
    """Envia mensagem (com moderação automática)"""
    try:
        return chat_service.send_message(db, chat_room_id, sender_id, message)
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


@router.get("/rooms/{chat_room_id}/messages", response_model=List[ChatMessageResponse])
def list_chat_messages(
    chat_room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista mensagens de um chat"""
    return chat_service.get_chat_messages(db, chat_room_id, skip=skip, limit=limit)


@router.post("/rooms/{chat_room_id}/mark-read")
def mark_messages_as_read(
    chat_room_id: int,
    user_id: int = Query(..., description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """Marca mensagens como lidas"""
    count = chat_service.mark_messages_as_read(db, chat_room_id, user_id)
    return {"marked_as_read": count}


@router.get("/messages/flagged", response_model=List[ChatMessageResponse])
def list_flagged_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista mensagens flagadas (ADMIN)"""
    return chat_service.get_flagged_messages(db, skip=skip, limit=limit)


@router.get("/user/{user_id}/unread-count")
def get_unread_count(user_id: int, db: Session = Depends(get_db)):
    """Conta mensagens não lidas"""
    count = chat_service.get_unread_count(db, user_id)
    return {"unread_count": count}
