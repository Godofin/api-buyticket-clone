# 📊 Diagrama da Estrutura do Banco de Dados

## Relacionamentos

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │◄──┐
│ full_name       │   │
│ cpf (UNIQUE)    │   │
│ email (UNIQUE)  │   │
│ password_hash   │   │
│ phone_verified  │   │
│ identity_verified│  │
│ role            │   │
│ reputation_score│   │
└─────────────────┘   │
         │            │
         │            │
         ▼            │
┌─────────────────┐   │
│ user_documents  │   │
├─────────────────┤   │
│ id (PK)         │   │
│ user_id (FK)────┼───┘
│ document_type   │
│ front_image_url │
│ back_image_url  │
│ selfie_url      │
│ status          │
└─────────────────┘


┌─────────────────────┐
│      events         │
├─────────────────────┤
│ id (PK)             │◄──┐
│ title               │   │
│ description         │   │
│ event_date          │   │
│ venue               │   │
│ image_banner_url    │   │
│ is_active           │   │
└─────────────────────┘   │
                          │
                          │
┌─────────────────────────┤
│ event_tickets_master    │ ⭐ TABELA MESTRA
├─────────────────────────┤
│ id (PK)                 │◄──┐
│ event_id (FK)───────────┼───┘
│ category_name           │
│ face_value              │ 💰 Valor oficial
└─────────────────────────┘
         │
         │
         ▼
┌─────────────────────────┐
│      listings           │
├─────────────────────────┤
│ id (PK)                 │
│ seller_id (FK) ─────────┼──► users
│ event_ticket_master_id ─┼──► event_tickets_master
│ price_asked             │ ⚠️  Validado: <= face_value * 1.20
│ ticket_proof_image_url  │
│ ticket_file_url         │
│ status                  │
│ description             │
└─────────────────────────┘
         │
         │
         ▼
┌─────────────────────────┐
│       orders            │
├─────────────────────────┤
│ id (PK)                 │
│ buyer_id (FK) ──────────┼──► users
│ listing_id (FK) ────────┼──► listings
│ total_amount            │
│ platform_fee            │
│ payment_status          │
│ escrow_status           │ 🔒 HELD → RELEASED_TO_SELLER
└─────────────────────────┘


┌─────────────────────────┐
│      chat_rooms         │
├─────────────────────────┤
│ id (PK)                 │◄──┐
│ listing_id (FK) ────────┼──► listings
│ buyer_id (FK) ──────────┼──► users
│ seller_id (FK) ─────────┼──► users
│ status                  │
└─────────────────────────┘
         │
         │
         ▼
┌─────────────────────────┐
│    chat_messages        │
├─────────────────────────┤
│ id (PK)                 │
│ chat_room_id (FK) ──────┼───┘
│ sender_id (FK) ─────────┼──► users
│ message_text            │
│ message_type            │
│ is_read                 │
│ flagged_by_system       │ ⚠️  Moderação automática
│ flagged_reason          │
└─────────────────────────┘


┌─────────────────────────┐
│     system_logs         │
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK) ───────────┼──► users
│ action                  │
│ ip_address              │
│ log_metadata (JSON)     │
└─────────────────────────┘


┌─────────────────────────┐
│      disputes           │
├─────────────────────────┤
│ id (PK)                 │
│ order_id (FK) ──────────┼──► orders
│ reporter_id (FK) ───────┼──► users
│ reported_user_id (FK) ──┼──► users
│ reason                  │
│ status                  │
│ admin_notes             │
└─────────────────────────┘
```

## Fluxo de Dados

### 1. Criação de Evento (Admin)
```
Admin → events → event_tickets_master (define face_value)
```

### 2. Vendedor Lista Ingresso
```
Vendedor → user_documents (KYC) → listings
                                    ↓
                            Valida: price_asked <= face_value * 1.20
```

### 3. Chat
```
Comprador → chat_rooms → chat_messages
                            ↓
                    Moderação automática
                    (flagged_by_system)
```

### 4. Compra com Escrow
```
Comprador → orders (escrow_status = HELD)
              ↓
         Pagamento confirmado
              ↓
         Ingresso liberado
              ↓
    Comprador confirma recebimento
              ↓
    escrow_status = RELEASED_TO_SELLER
```

### 5. Disputa
```
Usuário → disputes → Admin resolve
                        ↓
            Reembolso ou Libera escrow
```

## Índices Importantes

```sql
-- Performance
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_event ON listings(event_ticket_master_id);
CREATE INDEX idx_orders_buyer ON orders(buyer_id);
CREATE INDEX idx_orders_escrow ON orders(escrow_status);
CREATE INDEX idx_chat_messages_flagged ON chat_messages(flagged_by_system);

-- Unicidade
CREATE UNIQUE INDEX idx_users_cpf ON users(cpf);
CREATE UNIQUE INDEX idx_users_email ON users(email);
```

## Constraints Importantes

```sql
-- Validação de preço (implementada no backend)
CHECK (listings.price_asked <= (
    SELECT face_value * 1.20 
    FROM event_tickets_master 
    WHERE id = listings.event_ticket_master_id
))

-- Status válidos
CHECK (listings.status IN ('ACTIVE', 'RESERVED', 'SOLD', 'CANCELLED'))
CHECK (orders.payment_status IN ('PENDING', 'PAID', 'REFUNDED'))
CHECK (orders.escrow_status IN ('HELD', 'RELEASED_TO_SELLER', 'DISPUTE'))
```
