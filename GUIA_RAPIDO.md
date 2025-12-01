# 🎫 Guia Rápido - Ticket Marketplace API

## 🚀 Como Usar

### 1️⃣ Acesso Online (Já está rodando!)

A API está disponível em: **https://8000-iad9bc6kfpdckpa1p4w0o-fc4aaf32.manusvm.computer**

Acesse a documentação interativa: **https://8000-iad9bc6kfpdckpa1p4w0o-fc4aaf32.manusvm.computer/docs**

### 2️⃣ Rodar Localmente

```bash
# 1. Instalar dependências
pip3 install -r requirements.txt

# 2. Iniciar servidor
uvicorn app.main:app --reload

# 3. Acessar em http://localhost:8000/docs
```

## 📱 Principais Fluxos

### 🛒 Fluxo do Comprador

**1. Criar conta de comprador**
```bash
POST /users/
{
  "email": "comprador@email.com",
  "name": "Maria Silva",
  "cpf": "12345678901",
  "role": "buyer"
}
```

**2. Buscar ingressos disponíveis**
```bash
GET /tickets/available
```

**3. Ver detalhes de um ingresso**
```bash
GET /tickets/{ticket_id}
```

**4. Comprar ingresso**
```bash
POST /transactions/?buyer_id={seu_id}
{
  "ticket_id": 1,
  "payment_method": "credit_card"
}
```

**5. Completar pagamento**
```bash
POST /transactions/{transaction_id}/complete
```

**6. Ver suas compras**
```bash
GET /transactions/user/{seu_id}/purchases
```

### 💰 Fluxo do Vendedor

**1. Criar conta de vendedor**
```bash
POST /users/
{
  "email": "vendedor@email.com",
  "name": "João Santos",
  "cpf": "98765432100",
  "role": "seller"
}
```

**2. Listar ingresso para venda**
```bash
POST /tickets/?seller_id={seu_id}
{
  "event_id": 1,
  "section": "Pista",
  "seat_number": "A15",
  "original_price": 100.00,
  "selling_price": 105.00
}
```

**3. Ver seus ingressos**
```bash
GET /tickets/seller/{seu_id}
```

**4. Atualizar preço**
```bash
PUT /tickets/{ticket_id}?seller_id={seu_id}
{
  "selling_price": 108.00
}
```

**5. Ver suas vendas**
```bash
GET /transactions/user/{seu_id}/sales
```

**6. Ver estatísticas**
```bash
GET /transactions/stats/seller/{seu_id}
```

## 🛡️ Proteção Anti-Cambismo

### ✅ O que a API faz:

- **Limita preço de revenda**: Máximo 110% do valor original
- **Valida automaticamente**: Rejeita preços abusivos
- **Gera código único**: Cada ingresso tem verificação
- **Rastreia histórico**: Todas transações são registradas

### ❌ Exemplo de tentativa bloqueada:

```bash
# Isso será REJEITADO
POST /tickets/?seller_id=1
{
  "original_price": 100.00,
  "selling_price": 150.00  # 50% acima - BLOQUEADO!
}

# Resposta: "Preço não pode exceder 110% do original"
```

## 📊 Recursos Principais

### Para Eventos
- ✅ Criar eventos
- ✅ Buscar por categoria
- ✅ Filtrar por data
- ✅ Buscar por nome/local

### Para Ingressos
- ✅ Listar para venda
- ✅ Buscar disponíveis
- ✅ Filtrar por evento
- ✅ Atualizar informações
- ✅ Cancelar anúncio

### Para Transações
- ✅ Comprar ingresso
- ✅ Completar pagamento
- ✅ Cancelar compra
- ✅ Ver histórico
- ✅ Estatísticas detalhadas

## 💡 Dicas

### 1. Use a documentação interativa (Swagger)
Acesse `/docs` para testar todos os endpoints visualmente

### 2. Sempre verifique o status
```bash
GET /health  # Verifica se API está funcionando
```

### 3. IDs são sequenciais
- Primeiro usuário: ID 1
- Primeiro evento: ID 1
- Primeiro ingresso: ID 1

### 4. Taxa da plataforma
- 5% sobre o valor do ingresso
- Calculada automaticamente
- Adicionada ao total do comprador

## 🔍 Exemplos Práticos

### Cenário Completo

```bash
# 1. Criar vendedor
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email":"vendedor@test.com","name":"João","cpf":"111","role":"seller"}'
# Retorna: {"id": 1, ...}

# 2. Criar comprador
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email":"comprador@test.com","name":"Maria","cpf":"222","role":"buyer"}'
# Retorna: {"id": 2, ...}

# 3. Criar evento
curl -X POST "http://localhost:8000/events/" \
  -H "Content-Type: application/json" \
  -d '{"name":"Show","venue":"Arena","event_date":"2024-12-31T20:00:00"}'
# Retorna: {"id": 1, ...}

# 4. Vendedor lista ingresso
curl -X POST "http://localhost:8000/tickets/?seller_id=1" \
  -H "Content-Type: application/json" \
  -d '{"event_id":1,"original_price":100,"selling_price":105}'
# Retorna: {"id": 1, "status": "available", ...}

# 5. Comprador busca ingressos
curl "http://localhost:8000/tickets/available"
# Retorna: [{"id": 1, "selling_price": 105, ...}]

# 6. Comprador compra
curl -X POST "http://localhost:8000/transactions/?buyer_id=2" \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":1,"payment_method":"credit_card"}'
# Retorna: {"id": 1, "status": "pending", "total_amount": 110.25, ...}

# 7. Completar pagamento
curl -X POST "http://localhost:8000/transactions/1/complete"
# Retorna: {"status": "completed", ...}
```

## 📦 Estrutura do Projeto

```
ticket-marketplace/
├── app/
│   ├── models/models.py          # Banco de dados
│   ├── schemas/schemas.py        # Validações
│   ├── routes/                   # Endpoints
│   │   ├── users.py
│   │   ├── events.py
│   │   ├── tickets.py
│   │   └── transactions.py
│   ├── services/                 # Lógica de negócio
│   │   ├── user_service.py
│   │   ├── event_service.py
│   │   ├── ticket_service.py
│   │   └── transaction_service.py
│   ├── database.py               # Configuração DB
│   └── main.py                   # App principal
├── example_usage.py              # Script de teste
├── requirements.txt              # Dependências
└── README.md                     # Documentação completa
```

## ❓ Perguntas Frequentes

**Q: Como rodar localmente?**
A: `uvicorn app.main:app --reload`

**Q: Onde fica o banco de dados?**
A: SQLite em `ticket_marketplace.db` (criado automaticamente)

**Q: Como testar tudo de uma vez?**
A: `python3 example_usage.py`

**Q: Posso vender por mais de 110%?**
A: Não, a API bloqueia automaticamente

**Q: Como ver a documentação?**
A: Acesse `/docs` ou `/redoc`

## 🎯 Próximos Passos

1. ✅ API está funcionando
2. ✅ Proteção anti-cambismo implementada
3. ✅ Testes passando
4. 📝 Adicionar autenticação JWT
5. 💳 Integrar gateway de pagamento
6. 📧 Sistema de notificações
7. 🖼️ Upload de comprovantes

---

**Desenvolvido com FastAPI + SQLAlchemy + Pydantic**
