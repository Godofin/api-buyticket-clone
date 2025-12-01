from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


# ==================== ENUMS ====================

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class EscrowStatus(str, Enum):
    HELD = "HELD"
    RELEASED_TO_SELLER = "RELEASED_TO_SELLER"
    DISPUTE = "DISPUTE"


class ChatStatus(str, Enum):
    OPEN = "OPEN"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    full_name: str
    cpf: str = Field(..., min_length=11, max_length=14)
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: int
    phone_verified: bool
    identity_verified: bool
    role: UserRole
    reputation_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== USER DOCUMENT SCHEMAS ====================

class UserDocumentCreate(BaseModel):
    document_type: str
    front_image_url: Optional[str] = None
    back_image_url: Optional[str] = None
    selfie_url: Optional[str] = None


class UserDocumentResponse(BaseModel):
    id: int
    user_id: int
    document_type: str
    status: DocumentStatus
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== EVENT SCHEMAS ====================

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: datetime
    venue: str
    image_banner_url: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    venue: Optional[str] = None
    image_banner_url: Optional[str] = None
    is_active: Optional[bool] = None


class EventResponse(EventBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== EVENT TICKET MASTER SCHEMAS ====================

class EventTicketMasterBase(BaseModel):
    event_id: int
    category_name: str
    face_value: float = Field(..., gt=0)


class EventTicketMasterCreate(EventTicketMasterBase):
    pass


class EventTicketMasterResponse(EventTicketMasterBase):
    id: int
    created_at: datetime
    max_allowed_price: Optional[float] = None  # Calculado: face_value * 1.20

    class Config:
        from_attributes = True


# ==================== LISTING SCHEMAS ====================

class ListingBase(BaseModel):
    event_ticket_master_id: int
    price_asked: float = Field(..., gt=0)
    description: Optional[str] = None


class ListingCreate(ListingBase):
    ticket_proof_image_url: Optional[str] = None
    ticket_file_url: Optional[str] = None


class ListingUpdate(BaseModel):
    price_asked: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    status: Optional[ListingStatus] = None


class ListingResponse(ListingBase):
    id: int
    seller_id: int
    status: ListingStatus
    ticket_proof_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListingDetailResponse(ListingResponse):
    seller: Optional[UserResponse] = None
    ticket_master: Optional[EventTicketMasterResponse] = None


# ==================== ORDER SCHEMAS ====================

class OrderCreate(BaseModel):
    listing_id: int
    payment_method: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    listing_id: int
    total_amount: float
    platform_fee: float
    payment_status: PaymentStatus
    escrow_status: EscrowStatus
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    listing: Optional[ListingResponse] = None
    buyer: Optional[UserResponse] = None


# ==================== CHAT SCHEMAS ====================

class ChatRoomCreate(BaseModel):
    listing_id: int


class ChatRoomResponse(BaseModel):
    id: int
    listing_id: int
    buyer_id: int
    seller_id: int
    status: ChatStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    message_text: str
    message_type: MessageType = MessageType.TEXT


class ChatMessageResponse(BaseModel):
    id: int
    chat_room_id: int
    sender_id: int
    message_text: str
    message_type: MessageType
    is_read: bool
    flagged_by_system: bool
    flagged_reason: Optional[str] = None
    sent_at: datetime

    class Config:
        from_attributes = True


# ==================== DISPUTE SCHEMAS ====================

class DisputeCreate(BaseModel):
    order_id: Optional[int] = None
    reported_user_id: int
    reason: str


class DisputeUpdate(BaseModel):
    status: Optional[DisputeStatus] = None
    admin_notes: Optional[str] = None


class DisputeResponse(BaseModel):
    id: int
    order_id: Optional[int] = None
    reporter_id: int
    reported_user_id: int
    reason: str
    status: DisputeStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== SYSTEM LOG SCHEMAS ====================

class SystemLogCreate(BaseModel):
    action: str
    ip_address: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    ip_address: Optional[str] = None
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== STATISTICS SCHEMAS ====================

class SellerStats(BaseModel):
    total_listings: int
    active_listings: int
    sold_listings: int
    total_revenue: float
    reputation_score: float


class BuyerStats(BaseModel):
    total_purchases: int
    total_spent: float
    pending_orders: int
    completed_orders: int
