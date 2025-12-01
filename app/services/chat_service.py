from sqlalchemy.orm import Session
from app.models.models import ChatRoom, ChatMessage, ChatStatus, MessageType
from app.schemas.schemas import ChatRoomCreate, ChatMessageCreate
from typing import Optional, List
import re


# Palavras suspeitas para moderação automática
SUSPICIOUS_KEYWORDS = [
    'pix', 'whatsapp', 'zap', 'telegram', 'fora do app',
    'transferencia', 'deposito', 'conta bancaria', 'cpf',
    'email', '@', 'telefone', 'celular', 'numero',
    'direto', 'particular', 'pessoal', 'contato'
]


def detect_suspicious_content(message_text: str) -> tuple[bool, Optional[str]]:
    """Detecta conteúdo suspeito na mensagem"""
    message_lower = message_text.lower()
    
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in message_lower:
            return True, f"Palavra suspeita detectada: '{keyword}'"
    
    # Detecta padrões de telefone
    phone_pattern = r'\b\d{2,3}[-.\s]?\d{4,5}[-.\s]?\d{4}\b'
    if re.search(phone_pattern, message_text):
        return True, "Número de telefone detectado"
    
    # Detecta padrões de email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, message_text):
        return True, "Email detectado"
    
    return False, None


# ==================== CHAT ROOMS ====================

def create_chat_room(db: Session, buyer_id: int, chat_room: ChatRoomCreate) -> ChatRoom:
    """Cria sala de chat entre comprador e vendedor"""
    from app.services import listing_service
    
    listing = listing_service.get_listing(db, chat_room.listing_id)
    if not listing:
        raise ValueError("Anúncio não encontrado")
    
    if listing.seller_id == buyer_id:
        raise ValueError("Você não pode criar chat com você mesmo")
    
    # Verifica se já existe chat room
    existing_room = db.query(ChatRoom).filter(
        ChatRoom.listing_id == chat_room.listing_id,
        ChatRoom.buyer_id == buyer_id
    ).first()
    
    if existing_room:
        return existing_room
    
    db_chat_room = ChatRoom(
        listing_id=chat_room.listing_id,
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        status=ChatStatus.OPEN
    )
    
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)
    return db_chat_room


def get_chat_room(db: Session, chat_room_id: int) -> Optional[ChatRoom]:
    """Busca chat room por ID"""
    return db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()


def get_user_chat_rooms(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ChatRoom]:
    """Lista chat rooms de um usuário"""
    return db.query(ChatRoom).filter(
        (ChatRoom.buyer_id == user_id) | (ChatRoom.seller_id == user_id)
    ).order_by(ChatRoom.created_at.desc()).offset(skip).limit(limit).all()


def archive_chat_room(db: Session, chat_room_id: int) -> Optional[ChatRoom]:
    """Arquiva chat room"""
    db_chat_room = get_chat_room(db, chat_room_id)
    if not db_chat_room:
        return None
    
    db_chat_room.status = ChatStatus.ARCHIVED
    db.commit()
    db.refresh(db_chat_room)
    return db_chat_room


def block_chat_room(db: Session, chat_room_id: int) -> Optional[ChatRoom]:
    """Bloqueia chat room (admin)"""
    db_chat_room = get_chat_room(db, chat_room_id)
    if not db_chat_room:
        return None
    
    db_chat_room.status = ChatStatus.BLOCKED
    db.commit()
    db.refresh(db_chat_room)
    return db_chat_room


# ==================== CHAT MESSAGES ====================

def send_message(
    db: Session,
    chat_room_id: int,
    sender_id: int,
    message: ChatMessageCreate
) -> ChatMessage:
    """Envia mensagem com moderação automática"""
    # Verifica se chat room existe e está aberto
    chat_room = get_chat_room(db, chat_room_id)
    if not chat_room:
        raise ValueError("Chat não encontrado")
    
    if chat_room.status == ChatStatus.BLOCKED:
        raise ValueError("Este chat está bloqueado")
    
    # Verifica se sender é participante
    if sender_id not in [chat_room.buyer_id, chat_room.seller_id]:
        raise PermissionError("Você não faz parte deste chat")
    
    # Moderação automática
    is_flagged, flag_reason = detect_suspicious_content(message.message_text)
    
    db_message = ChatMessage(
        chat_room_id=chat_room_id,
        sender_id=sender_id,
        message_text=message.message_text,
        message_type=message.message_type,
        flagged_by_system=is_flagged,
        flagged_reason=flag_reason
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Se mensagem foi flagged, pode criar log de auditoria
    if is_flagged:
        from app.services import system_service
        system_service.create_log(
            db,
            user_id=sender_id,
            action=f"Mensagem suspeita no chat {chat_room_id}",
            metadata={"reason": flag_reason, "message_id": db_message.id}
        )
    
    return db_message


def get_chat_messages(
    db: Session,
    chat_room_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ChatMessage]:
    """Lista mensagens de um chat"""
    return db.query(ChatMessage)\
        .filter(ChatMessage.chat_room_id == chat_room_id)\
        .order_by(ChatMessage.sent_at.asc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def mark_messages_as_read(db: Session, chat_room_id: int, user_id: int) -> int:
    """Marca mensagens como lidas"""
    chat_room = get_chat_room(db, chat_room_id)
    if not chat_room:
        return 0
    
    # Marca como lidas as mensagens que o usuário recebeu
    updated = db.query(ChatMessage)\
        .filter(
            ChatMessage.chat_room_id == chat_room_id,
            ChatMessage.sender_id != user_id,
            ChatMessage.is_read == False
        )\
        .update({"is_read": True})
    
    db.commit()
    return updated


def get_flagged_messages(db: Session, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
    """Lista mensagens flagadas pelo sistema (para admin)"""
    return db.query(ChatMessage)\
        .filter(ChatMessage.flagged_by_system == True)\
        .order_by(ChatMessage.sent_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_unread_count(db: Session, user_id: int) -> int:
    """Conta mensagens não lidas de um usuário"""
    # Busca chat rooms do usuário
    chat_rooms = get_user_chat_rooms(db, user_id)
    chat_room_ids = [room.id for room in chat_rooms]
    
    if not chat_room_ids:
        return 0
    
    return db.query(ChatMessage)\
        .filter(
            ChatMessage.chat_room_id.in_(chat_room_ids),
            ChatMessage.sender_id != user_id,
            ChatMessage.is_read == False
        )\
        .count()
