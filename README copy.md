# Ticket Marketplace API

API completa para marketplace de compra e venda de ingressos com proteção anti-cambismo.

## 📋 Características

### Proteção Anti-Cambismo
- **Limite de revenda**: Ingressos só podem ser revendidos por até 110% do valor original
- **Código de verificação**: Cada ingresso recebe um código único
- **Comprovante de compra**: Sistema para anexar prova de compra original
- **Rastreabilidade**: Histórico completo de transações

### Funcionalidades Principais

#### Para Vendedores
- Listar ingressos para venda
- Definir preços (respeitando limite de 110%)
- Acompanhar vendas e receita
- Gerenciar ingressos listados
- Cancelar anúncios

#### Para Compradores
- Buscar ingressos disponíveis
- Filtrar por evento, preço, seção
- Visualizar detalhes completos
- Comprar com segurança
- Acompanhar histórico de compras

## 🏗️ Arquitetura

```
ticket-marketplace/
├── app/
│   ├── models/
│   │   └── models.py          # Modelos SQLAlchemy
│   ├── schemas/
│   │   └── schemas.py         # Schemas Pydantic
│   ├── routes/
│   │   ├── users.py           # Rotas de usuários
│   │   ├── events.py          # Rotas de eventos
│   │   ├── tickets.py         # Rotas de ingressos
│   │   └── transactions.py    # Rotas de transações
│   ├── services/
│   │   ├── user_service.py    # Lógica de negócio - usuários
│   │   ├── event_service.py   # Lógica de negócio - eventos
│   │   ├── ticket_service.py  # Lógica de negócio - ingressos
│   │   └── transaction_service.py  # Lógica de negócio - transações
│   ├── database.py            # Configuração do banco
│   └── main.py                # Aplicação principal
├── requirements.txt           # Dependências
├── example_usage.py          # Script de exemplo
└── README.md                 # Documentação
```

## 🚀 Instalação e Execução

### 1. Instalar Dependências

```bash
pip3 install -r requirements.txt
```

### 2. Iniciar a API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

### 3. Acessar Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 Modelos de Dados

### User (Usuário)
- **id**: ID único
- **email**: Email único
- **name**: Nome completo
- **cpf**: CPF único
- **phone**: Telefone
- **role**: Papel (buyer, seller, both)
- **is_verified**: Status de verificação

### Event (Evento)
- **id**: ID único
- **name**: Nome do evento
- **description**: Descrição
- **venue**: Local
- **event_date**: Data do evento
- **category**: Categoria

### Ticket (Ingresso)
- **id**: ID único
- **event_id**: ID do evento
- **seller_id**: ID do vendedor
- **section**: Setor
- **row**: Fileira
- **seat_number**: Número do assento
- **original_price**: Preço original
- **selling_price**: Preço de venda (máx 110% do original)
- **status**: Status (available, reserved, sold, cancelled)
- **verification_code**: Código de verificação único

### Transaction (Transação)
- **id**: ID único
- **ticket_id**: ID do ingresso
- **buyer_id**: ID do comprador
- **seller_id**: ID do vendedor
- **amount**: Valor do ingresso
- **platform_fee**: Taxa da plataforma (5%)
- **total_amount**: Valor total
- **status**: Status (pending, completed, cancelled, refunded)

## 🔌 Endpoints Principais

### Usuários
- `POST /users/` - Criar usuário
- `GET /users/` - Listar usuários
- `GET /users/{user_id}` - Buscar usuário
- `PUT /users/{user_id}` - Atualizar usuário
- `POST /users/{user_id}/verify` - Verificar usuário

### Eventos
- `POST /events/` - Criar evento
- `GET /events/` - Listar eventos
- `GET /events/upcoming` - Listar eventos futuros
- `GET /events/{event_id}` - Buscar evento
- `PUT /events/{event_id}` - Atualizar evento

### Ingressos
- `POST /tickets/?seller_id={id}` - Criar ingresso
- `GET /tickets/` - Listar ingressos
- `GET /tickets/available` - Listar ingressos disponíveis
- `GET /tickets/seller/{seller_id}` - Ingressos do vendedor
- `GET /tickets/{ticket_id}` - Buscar ingresso
- `PUT /tickets/{ticket_id}?seller_id={id}` - Atualizar ingresso
- `POST /tickets/{ticket_id}/cancel?seller_id={id}` - Cancelar ingresso

### Transações
- `POST /transactions/?buyer_id={id}` - Criar transação
- `GET /transactions/{transaction_id}` - Buscar transação
- `GET /transactions/user/{user_id}/purchases` - Compras do usuário
- `GET /transactions/user/{user_id}/sales` - Vendas do usuário
- `POST /transactions/{transaction_id}/complete` - Completar transação
- `POST /transactions/{transaction_id}/cancel?user_id={id}` - Cancelar transação
- `GET /transactions/stats/seller/{seller_id}` - Estatísticas do vendedor
- `GET /transactions/stats/buyer/{buyer_id}` - Estatísticas do comprador

## 🧪 Testando a API

### Opção 1: Script de Exemplo

Execute o script de exemplo que testa todos os fluxos:

```bash
python3 example_usage.py
```

### Opção 2: Swagger UI

Acesse http://localhost:8000/docs e teste diretamente na interface interativa.

### Opção 3: cURL

```bash
# Criar usuário vendedor
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendedor@example.com",
    "name": "João Vendedor",
    "cpf": "12345678901",
    "role": "seller"
  }'

# Criar evento
curl -X POST "http://localhost:8000/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Show de Rock",
    "venue": "Estádio Municipal",
    "event_date": "2024-12-31T20:00:00",
    "category": "Show"
  }'

# Listar ingressos disponíveis
curl -X GET "http://localhost:8000/tickets/available"
```

## 💡 Fluxos de Uso

### Fluxo do Vendedor

1. **Criar conta** como vendedor
2. **Listar ingresso** informando preço original e preço de venda
3. **Aguardar comprador**
4. **Receber pagamento** quando transação for completada
5. **Acompanhar estatísticas** de vendas

### Fluxo do Comprador

1. **Criar conta** como comprador
2. **Buscar eventos** e ingressos disponíveis
3. **Visualizar detalhes** do ingresso
4. **Iniciar transação** de compra
5. **Completar pagamento**
6. **Receber ingresso** com código de verificação

## 🛡️ Regras de Negócio

### Proteção Anti-Cambismo
- Preço de venda não pode exceder 110% do preço original
- Validação automática no backend
- Rejeição de tentativas de preços abusivos

### Gestão de Status
- Ingressos começam como "available"
- Ficam "reserved" durante compra
- Tornam-se "sold" após pagamento
- Podem ser "cancelled" pelo vendedor

### Taxas
- Taxa da plataforma: 5% sobre o valor do ingresso
- Calculada automaticamente nas transações

## 🔒 Segurança

- Validação de CPF único por usuário
- Validação de email único
- Verificação de propriedade antes de editar/cancelar
- Códigos de verificação únicos para cada ingresso
- Proteção contra auto-compra

## 📈 Estatísticas

### Para Vendedores
- Total de ingressos listados
- Ingressos vendidos
- Ingressos disponíveis
- Receita total
- Transações pendentes

### Para Compradores
- Total de compras
- Total gasto
- Transações pendentes
- Transações completadas

## 🗄️ Banco de Dados

O projeto usa **SQLite** para facilitar testes locais. O arquivo do banco (`ticket_marketplace.db`) é criado automaticamente na primeira execução.

Para produção, é recomendado migrar para PostgreSQL ou MySQL alterando a string de conexão em `app/database.py`.

## 🔧 Tecnologias

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para Python
- **Pydantic**: Validação de dados
- **Uvicorn**: Servidor ASGI
- **SQLite**: Banco de dados (desenvolvimento)

## 📝 Próximos Passos

- [ ] Implementar autenticação JWT
- [ ] Integrar gateway de pagamento real
- [ ] Adicionar upload de comprovantes
- [ ] Implementar notificações por email
- [ ] Adicionar sistema de avaliações
- [ ] Criar painel administrativo
- [ ] Implementar busca avançada
- [ ] Adicionar filtros por faixa de preço

## 📄 Licença

Este projeto é um exemplo educacional para demonstração de conceitos de API REST com FastAPI.
