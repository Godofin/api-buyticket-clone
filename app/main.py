from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import users, events, listings, orders, chat, admin

# Cria a aplicação FastAPI
app = FastAPI(
    title="Ticket Marketplace API v2",
    description="""
    API completa para marketplace de ingressos com proteção anti-cambismo.
    
    ## Principais Recursos:
    
    * **Sistema de KYC**: Verificação de identidade com documentos
    * **Regra dos 20%**: Preço máximo de revenda limitado a 120% do valor original
    * **Chat Moderado**: Detecção automática de tentativas de negociação externa
    * **Sistema de Escrow**: Dinheiro retido até confirmação da transação
    * **Disputas**: Sistema completo de denúncias e resolução
    * **Auditoria**: Logs detalhados de todas as ações
    * **Reputação**: Sistema de pontuação para vendedores
    
    ## Fluxo Principal:
    
    1. **Admin** cria evento e categorias de ingressos (ticket masters) com preços oficiais
    2. **Vendedor** lista ingresso respeitando limite de 120%
    3. **Comprador** busca e inicia chat com vendedor
    4. **Comprador** cria pedido (dinheiro vai para escrow)
    5. **Sistema** libera ingresso para comprador
    6. **Comprador** confirma recebimento ou aguarda prazo
    7. **Sistema** libera dinheiro do escrow para vendedor
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    """Inicializa o banco de dados ao iniciar a aplicação"""
    init_db()


@app.get("/")
def root():
    """Endpoint raiz da API"""
    return {
        "message": "Bem-vindo ao Ticket Marketplace API v2",
        "version": "2.0.0",
        "features": [
            "Sistema de KYC com verificação de documentos",
            "Regra dos 20% (máximo 120% do valor original)",
            "Chat com moderação automática",
            "Sistema de escrow para pagamentos",
            "Disputas e resolução de conflitos",
            "Logs de auditoria completos",
            "Sistema de reputação"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Endpoint de verificação de saúde da API"""
    return {
        "status": "healthy",
        "version": "2.0.0"
    }
