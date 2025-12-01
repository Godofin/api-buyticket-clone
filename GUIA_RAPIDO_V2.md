# 🚀 Guia Rápido - Ticket Marketplace API v2.0

## Início Rápido

### 1. Instalação

```bash
# Clonar/extrair projeto
cd ticket-marketplace

# Instalar dependências
pip3 install -r requirements.txt

# Iniciar servidor
uvicorn app.main:app --reload

# Acessar documentação interativa
http://localhost:8000/docs
```

### 2. Testar Tudo

```bash
# Executar script de teste completo
python3 test_new_api.py

# Você verá todos os recursos sendo testados:
# ✓ KYC, ✓ Regra 20%, ✓ Chat, ✓ Escrow, ✓ Disputas
```

## 📋 Fluxo Básico

### Passo 1: Admin Cria Evento

```bash
curl -X POST "http://localhost:8000/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Rock in Rio 2025",
    "description": "Festival de rock",
    "event_date": "2025-09-15T20:00:00",
    "venue": "Cidade do Rock - RJ",
    "image_banner_url": "https://example.com/banner.jpg"
  }'
```

### Passo 2: Admin Define Preços Oficiais

```bash
curl -X POST "http://localhost:8000/events/ticket-masters" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "category_name": "Pista Premium",
    "face_value": 500.00
  }'

# Retorna: max_allowed_price = 600.00 (120%)
```

### Passo 3: Vendedor Lista Ingresso

```bash
# Primeiro: Upload documento (KYC)
curl -X POST "http://localhost:8000/users/2/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "CNH",
    "front_image_url": "https://example.com/cnh_frente.jpg",
    "selfie_url": "https://example.com/selfie.jpg"
  }'

# Admin aprova
curl -X POST "http://localhost:8000/users/documents/1/approve"

# Lista ingresso (validado!)
curl -X POST "http://localhost:8000/listings/?seller_id=2" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ticket_master_id": 1,
    "price_asked": 550.00,
    "description": "Não posso mais ir"
  }'
```

### Passo 4: Comprador Conversa

```bash
# Cria chat
curl -X POST "http://localhost:8000/chat/rooms?buyer_id=3" \
  -H "Content-Type: application/json" \
  -d '{"listing_id": 1}'

# Envia mensagem
curl -X POST "http://localhost:8000/chat/rooms/1/messages?sender_id=3" \
  -H "Content-Type: application/json" \
  -d '{
    "message_text": "O ingresso ainda está disponível?",
    "message_type": "TEXT"
  }'
```

### Passo 5: Compra com Escrow

```bash
# Cria pedido ($ vai para escrow)
curl -X POST "http://localhost:8000/orders/?buyer_id=3" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": 1,
    "payment_method": "credit_card"
  }'

# Completa pagamento
curl -X POST "http://localhost:8000/orders/1/complete-payment"

# Libera escrow para vendedor
curl -X POST "http://localhost:8000/orders/1/release-escrow"
```

## 🔑 Endpoints Essenciais

### Usuários
- `POST /users/` - Criar usuário
- `POST /users/{id}/verify-phone` - Verificar telefone
- `POST /users/{id}/documents` - Upload documento KYC

### Eventos (Admin)
- `POST /events/` - Criar evento
- `POST /events/ticket-masters` - Definir preço oficial
- `GET /events/{id}/ticket-masters` - Ver categorias

### Listings
- `POST /listings/?seller_id={id}` - Listar ingresso
- `GET /listings/active` - Ver disponíveis
- `GET /listings/active?event_id={id}` - Filtrar por evento

### Chat
- `POST /chat/rooms?buyer_id={id}` - Criar chat
- `POST /chat/rooms/{id}/messages?sender_id={id}` - Enviar mensagem
- `GET /chat/messages/flagged` - Ver suspeitas (admin)

### Orders
- `POST /orders/?buyer_id={id}` - Criar pedido
- `POST /orders/{id}/complete-payment` - Pagar
- `POST /orders/{id}/release-escrow` - Liberar $

### Admin
- `GET /admin/disputes` - Ver disputas
- `POST /admin/disputes/{id}/resolve` - Resolver
- `GET /admin/logs` - Ver logs

## 🛡️ Validações Automáticas

### Regra dos 20%
```python
# ❌ BLOQUEADO
price_asked = 400.00  # face_value = 300.00 (33% acima)
# Erro: "Preço excede o limite de 120%"

# ✅ PERMITIDO
price_asked = 350.00  # face_value = 300.00 (16% acima)
```

### Moderação de Chat
```python
# ⚠️ FLAGADO
"Me passa seu WhatsApp"  # flagged_by_system = True

# ✅ NORMAL
"O ingresso ainda está disponível?"  # flagged_by_system = False
```

## 📊 Consultas Úteis

### Estatísticas Vendedor
```bash
GET /orders/stats/seller/2
{
  "total_listings": 5,
  "sold_listings": 3,
  "total_revenue": 1050.00,
  "reputation_score": 3.0
}
```

### Estatísticas Comprador
```bash
GET /orders/stats/buyer/3
{
  "total_purchases": 2,
  "total_spent": 735.00,
  "completed_orders": 2
}
```

### Mensagens Não Lidas
```bash
GET /chat/user/3/unread-count
{
  "unread_count": 5
}
```

## 🔍 Troubleshooting

### Erro: "Preço excede o limite"
- Verifique o `face_value` do ticket_master
- Máximo permitido: `face_value * 1.20`

### Erro: "Email já cadastrado"
- CPF e email devem ser únicos
- Use valores diferentes para cada usuário

### Erro: "Chat não encontrado"
- Crie o chat room antes de enviar mensagens
- Use `POST /chat/rooms` primeiro

### Erro: "Você não faz parte deste chat"
- Apenas buyer e seller podem enviar mensagens
- Verifique o `sender_id`

## 📚 Documentação Completa

- **README_V2.md**: Documentação técnica completa
- **test_new_api.py**: Exemplos de uso de todos os endpoints
- **/docs**: Swagger UI interativo
- **/redoc**: Documentação alternativa

## 🎯 Próximos Passos

1. Implementar autenticação JWT
2. Integrar gateway de pagamento real
3. Adicionar notificações por email/SMS
4. Upload real de arquivos para S3
5. Dashboard admin com gráficos

---

**Dúvidas?** Consulte a documentação em `/docs` ou execute `python3 test_new_api.py` para ver exemplos práticos!
