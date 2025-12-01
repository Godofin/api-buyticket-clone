# 🎫 Ticket Marketplace API v2.0

API completa para marketplace de compra e venda de ingressos com **proteção anti-cambismo** baseada na estrutura de tabelas fornecida.

## 🆕 Novidades da Versão 2.0

### ✅ Recursos Implementados

#### 1. **Sistema de KYC (Know Your Customer)**
- Upload de documentos (RG, CNH) com frente, verso e selfie
- Aprovação/rejeição por administrador
- Verificação de identidade obrigatória para vendedores
- Verificação de telefone por SMS

#### 2. **Regra dos 20% (Limite de 120%)**
- Tabela mestra de preços (`event_tickets_master`)
- Validação automática no backend
- Preço máximo de revenda: **120% do valor original**
- Bloqueio de tentativas de preços abusivos

#### 3. **Chat com Moderação Automática**
- Sistema de mensagens entre comprador e vendedor
- Detecção automática de palavras suspeitas:
  - Pix, WhatsApp, Telegram, "fora do app"
  - Números de telefone e emails
  - Tentativas de negociação externa
- Painel admin para visualizar mensagens flagadas

#### 4. **Sistema de Escrow**
- Dinheiro retido até confirmação da transação
- Estados: `HELD` → `RELEASED_TO_SELLER` ou `DISPUTE`
- Proteção para comprador e vendedor
- Liberação automática após confirmação

#### 5. **Sistema de Disputas**
- Denúncias entre usuários
- Resolução por administrador
- Reembolso automático quando procedente
- Impacto na reputação do usuário

#### 6. **Logs de Auditoria**
- Registro de todas as ações importantes
- Rastreamento de atividades suspeitas
- Metadados em JSON para análise detalhada

#### 7. **Sistema de Reputação**
- Pontuação baseada em vendas bem-sucedidas
- Penalidades por disputas procedentes
- Visível para compradores

## 📊 Estrutura do Banco de Dados

### Módulo 1: Usuários e Segurança
- **`users`**: Dados principais, CPF único, verificações
- **`user_documents`**: Documentos para KYC

### Módulo 2: Eventos e Preços
- **`events`**: Informações dos eventos
- **`event_tickets_master`**: **TABELA MESTRA** com preços oficiais

### Módulo 3: Marketplace
- **`listings`**: Anúncios de venda (validados contra ticket_master)
- **`orders`**: Pedidos com escrow

### Módulo 4: Chat e Moderação
- **`chat_rooms`**: Salas de conversa
- **`chat_messages`**: Mensagens com flag automática

### Módulo 5: Auditoria
- **`system_logs`**: Logs de ações
- **`disputes`**: Disputas e denúncias

## 🚀 Como Usar

### Instalação

```bash
# Instalar dependências
pip3 install -r requirements.txt

# Iniciar servidor
uvicorn app.main:app --reload

# Acessar documentação
http://localhost:8000/docs
```

### Testar

```bash
# Executar script de teste completo
python3 test_new_api.py
```

## 📖 Fluxo Completo

### 1️⃣ Preparação (Admin)

```bash
# Admin cria evento
POST /events/
{
  "title": "Rock in Rio 2025",
  "venue": "Cidade do Rock",
  "event_date": "2025-09-15T20:00:00"
}

# Admin define categorias e preços oficiais
POST /events/ticket-masters
{
  "event_id": 1,
  "category_name": "Pista Premium - Lote 1",
  "face_value": 500.00
}
# Retorna: max_allowed_price = 600.00 (120%)
```

### 2️⃣ Vendedor Lista Ingresso

```bash
# Vendedor faz upload de documento
POST /users/{user_id}/documents
{
  "document_type": "CNH",
  "front_image_url": "...",
  "selfie_url": "..."
}

# Admin aprova
POST /users/documents/{doc_id}/approve

# Vendedor lista ingresso
POST /listings/?seller_id=2
{
  "event_ticket_master_id": 1,
  "price_asked": 550.00,  # 10% acima - OK!
  "description": "Não posso mais ir"
}
```

### 3️⃣ Comprador Busca e Conversa

```bash
# Busca ingressos disponíveis
GET /listings/active

# Cria chat com vendedor
POST /chat/rooms?buyer_id=3
{
  "listing_id": 1
}

# Envia mensagem
POST /chat/rooms/1/messages?sender_id=3
{
  "message_text": "O ingresso ainda está disponível?"
}
```

### 4️⃣ Compra com Escrow

```bash
# Cria pedido (dinheiro vai para escrow)
POST /orders/?buyer_id=3
{
  "listing_id": 1,
  "payment_method": "credit_card"
}
# Retorna: escrow_status = "HELD"

# Completa pagamento
POST /orders/1/complete-payment
# Ingresso é liberado para comprador

# Comprador confirma recebimento
POST /orders/1/release-escrow
# Dinheiro é liberado para vendedor
```

### 5️⃣ Disputas (se necessário)

```bash
# Comprador abre disputa
POST /admin/disputes?reporter_id=3
{
  "order_id": 1,
  "reported_user_id": 2,
  "reason": "Ingresso não foi enviado"
}

# Admin resolve
POST /admin/disputes/1/resolve?refund_buyer=true
{
  "admin_notes": "Procedente. Reembolsando comprador."
}
```

## 🛡️ Proteções Implementadas

### Contra Cambismo
- ✅ Limite de 120% validado no backend
- ✅ Preços oficiais em tabela mestra
- ✅ Impossível burlar pelo frontend

### Contra Fraudes
- ✅ KYC obrigatório para vendedores
- ✅ CPF único por usuário
- ✅ Verificação de telefone
- ✅ Sistema de reputação

### Contra Negociação Externa
- ✅ Moderação automática de chat
- ✅ Detecção de palavras suspeitas
- ✅ Painel admin para monitoramento

### Proteção Financeira
- ✅ Sistema de escrow
- ✅ Dinheiro retido até confirmação
- ✅ Reembolso em disputas procedentes

## 📡 Endpoints Principais

### Usuários e KYC
- `POST /users/` - Criar usuário
- `POST /users/{id}/documents` - Upload documento
- `POST /users/documents/{id}/approve` - Aprovar (admin)

### Eventos e Preços
- `POST /events/` - Criar evento (admin)
- `POST /events/ticket-masters` - Definir preço oficial (admin)
- `GET /events/{id}/ticket-masters` - Ver categorias

### Listings
- `POST /listings/?seller_id={id}` - Listar ingresso (valida 20%)
- `GET /listings/active` - Buscar disponíveis
- `PUT /listings/{id}?seller_id={id}` - Atualizar

### Orders e Escrow
- `POST /orders/?buyer_id={id}` - Criar pedido
- `POST /orders/{id}/complete-payment` - Pagar
- `POST /orders/{id}/release-escrow` - Liberar para vendedor

### Chat
- `POST /chat/rooms?buyer_id={id}` - Criar chat
- `POST /chat/rooms/{id}/messages?sender_id={id}` - Enviar mensagem
- `GET /chat/messages/flagged` - Ver suspeitas (admin)

### Admin
- `GET /admin/disputes` - Listar disputas
- `POST /admin/disputes/{id}/resolve` - Resolver
- `GET /admin/logs` - Ver logs de auditoria

## 🔍 Exemplos de Validação

### Tentativa de Preço Abusivo (BLOQUEADO)

```bash
POST /listings/?seller_id=2
{
  "event_ticket_master_id": 1,  # face_value = 300.00
  "price_asked": 400.00          # 33% acima
}

# Resposta: 400 Bad Request
{
  "detail": "Preço excede o limite permitido. 
             Valor original: R$ 300.00, 
             Máximo permitido (120%): R$ 360.00"
}
```

### Mensagem Suspeita (FLAGADA)

```bash
POST /chat/rooms/1/messages?sender_id=2
{
  "message_text": "Me passa seu WhatsApp"
}

# Resposta: 201 Created
{
  "flagged_by_system": true,
  "flagged_reason": "Palavra suspeita detectada: 'whatsapp'"
}
```

## 📈 Estatísticas

```bash
# Vendedor
GET /orders/stats/seller/2
{
  "total_listings": 5,
  "sold_listings": 3,
  "total_revenue": 1050.00,
  "reputation_score": 3.0
}

# Comprador
GET /orders/stats/buyer/3
{
  "total_purchases": 2,
  "total_spent": 735.00,
  "completed_orders": 2
}
```

## 🗂️ Estrutura do Projeto

```
ticket-marketplace/
├── app/
│   ├── models/
│   │   └── models.py              # 10 tabelas completas
│   ├── schemas/
│   │   └── schemas.py             # Validações Pydantic
│   ├── routes/
│   │   ├── users.py               # Usuários e KYC
│   │   ├── events.py              # Eventos e ticket masters
│   │   ├── listings.py            # Anúncios
│   │   ├── orders.py              # Pedidos e escrow
│   │   ├── chat.py                # Chat moderado
│   │   └── admin.py               # Disputas e logs
│   ├── services/
│   │   ├── user_service.py        # Lógica de usuários
│   │   ├── event_service.py       # Lógica de eventos
│   │   ├── listing_service.py     # Validação de 20%
│   │   ├── order_service.py       # Escrow
│   │   ├── chat_service.py        # Moderação
│   │   └── system_service.py      # Disputas e logs
│   ├── database.py                # SQLAlchemy + SQLite
│   └── main.py                    # FastAPI app
├── test_new_api.py                # Teste completo
├── requirements.txt
└── README_V2.md
```

## 🔐 Segurança

- Senhas com hash SHA256 (em produção usar bcrypt)
- CPF único por usuário
- Email único por usuário
- Validação de propriedade antes de editar
- Logs de todas as ações importantes

## 🎯 Próximos Passos

- [ ] Autenticação JWT
- [ ] Gateway de pagamento real (Stripe, PagSeguro)
- [ ] Notificações por email/SMS
- [ ] Upload real de arquivos (S3)
- [ ] Liberação automática de escrow após X dias
- [ ] Dashboard admin com gráficos
- [ ] Rate limiting
- [ ] Migração para PostgreSQL

## 📝 Licença

Projeto educacional para demonstração de conceitos de API REST com FastAPI.

---

**Desenvolvido com FastAPI + SQLAlchemy + Pydantic**  
**Versão 2.0 - Estrutura completa anti-cambismo**
