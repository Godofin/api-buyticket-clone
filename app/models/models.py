from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# ==================== ENUMS ====================

class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class DocumentStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ListingStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class EscrowStatus(enum.Enum):
    HELD = "HELD"
    RELEASED_TO_SELLER = "RELEASED_TO_SELLER"
    DISPUTE = "DISPUTE"


class ChatStatus(enum.Enum):
    OPEN = "OPEN"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"


class MessageType(enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class DisputeStatus(enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


# ==================== MÓDULO 1: USUÁRIOS E SEGURANÇA ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone = Column(String)
    phone_verified = Column(Boolean, default=False)
    identity_verified = Column(Boolean, default=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), default=UserRole.USER)
    reputation_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("UserDocument", back_populates="user")
    listings = relationship("Listing", back_populates="seller", foreign_keys="Listing.seller_id")
    orders_as_buyer = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    chat_rooms_as_buyer = relationship("ChatRoom", back_populates="buyer", foreign_keys="ChatRoom.buyer_id")
    chat_rooms_as_seller = relationship("ChatRoom", back_populates="seller", foreign_keys="ChatRoom.seller_id")
    messages_sent = relationship("ChatMessage", back_populates="sender", foreign_keys="ChatMessage.sender_id")
    logs = relationship("SystemLog", back_populates="user")
    disputes_reported = relationship("Dispute", back_populates="reporter", foreign_keys="Dispute.reporter_id")
    disputes_received = relationship("Dispute", back_populates="reported_user", foreign_keys="Dispute.reported_user_id")


class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False)  # RG, CNH, etc
    front_image_url = Column(String)
    back_image_url = Column(String)
    selfie_url = Column(String)
    status = Column(SQLEnum(DocumentStatus, values_callable=lambda obj: [e.value for e in obj]), default=DocumentStatus.PENDING)
    rejection_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")


# ==================== MÓDULO 2: EVENTOS E PREÇOS ====================

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False)
    venue = Column(String, nullable=False)
    image_banner_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket_masters = relationship("EventTicketMaster", back_populates="event")


class EventTicketMaster(Base):
    """Tabela MESTRA de preços - A verdade única para validação dos 20%"""
    __tablename__ = "event_tickets_master"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    category_name = Column(String, nullable=False)  # Ex: "Pista Premium - Lote 1"
    face_value = Column(Float, nullable=False)  # Valor original impresso no ingresso
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="ticket_masters")
    listings = relationship("Listing", back_populates="ticket_master")


# ==================== MÓDULO 3: VENDAS (MARKETPLACE) ====================

class Listing(Base):
    """Anúncios de venda de ingressos"""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_ticket_master_id = Column(Integer, ForeignKey("event_tickets_master.id"), nullable=False)
    price_asked = Column(Float, nullable=False)  # Validado: <= face_value * 1.20
    ticket_proof_image_url = Column(String)  # Imagem com código de barras borrado
    ticket_file_url = Column(String)  # PDF original (liberado após pagamento)
    status = Column(SQLEnum(ListingStatus, values_callable=lambda obj: [e.value for e in obj]), default=ListingStatus.ACTIVE)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seller = relationship("User", back_populates="listings", foreign_keys=[seller_id])
    ticket_master = relationship("EventTicketMaster", back_populates="listings")
    orders = relationship("Order", back_populates="listing")
    chat_rooms = relationship("ChatRoom", back_populates="listing")


class Order(Base):
    """Pedidos/Transações"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    total_amount = Column(Float, nullable=False)  # Preço + taxas
    platform_fee = Column(Float, default=0.0)
    payment_status = Column(SQLEnum(PaymentStatus, values_callable=lambda obj: [e.value for e in obj]), default=PaymentStatus.PENDING)
    escrow_status = Column(SQLEnum(EscrowStatus, values_callable=lambda obj: [e.value for e in obj]), default=EscrowStatus.HELD)
    payment_method = Column(String)
    payment_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    buyer = relationship("User", back_populates="orders_as_buyer", foreign_keys=[buyer_id])
    listing = relationship("Listing", back_populates="orders")
    disputes = relationship("Dispute", back_populates="order")


# ==================== MÓDULO 4: CHAT E MODERAÇÃO ====================

class ChatRoom(Base):
    """Salas de chat entre comprador e vendedor"""
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ChatStatus, values_callable=lambda obj: [e.value for e in obj]), default=ChatStatus.OPEN)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    listing = relationship("Listing", back_populates="chat_rooms")
    buyer = relationship("User", back_populates="chat_rooms_as_buyer", foreign_keys=[buyer_id])
    seller = relationship("User", back_populates="chat_rooms_as_seller", foreign_keys=[seller_id])
    messages = relationship("ChatMessage", back_populates="chat_room")


class ChatMessage(Base):
    """Mensagens do chat com moderação automática"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType, values_callable=lambda obj: [e.value for e in obj]), default=MessageType.TEXT)
    is_read = Column(Boolean, default=False)
    flagged_by_system = Column(Boolean, default=False)  # Detecta palavras suspeitas
    flagged_reason = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent", foreign_keys=[sender_id])


# ==================== MÓDULO 5: AUDITORIA E LOGS ====================

class SystemLog(Base):
    """Logs de auditoria do sistema"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    ip_address = Column(String)
    log_metadata = Column(JSON)  # Detalhes técnicos em JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="logs")


class Dispute(Base):
    """Disputas e denúncias"""
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Opcional
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(DisputeStatus, values_callable=lambda obj: [e.value for e in obj]), default=DisputeStatus.OPEN)
    admin_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    order = relationship("Order", back_populates="disputes")
    reporter = relationship("User", back_populates="disputes_reported", foreign_keys=[reporter_id])
    reported_user = relationship("User", back_populates="disputes_received", foreign_keys=[reported_user_id])
