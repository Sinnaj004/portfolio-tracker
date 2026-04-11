from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- NEU
from .db.session import engine, Base
from .models import models
from .api.v1 import auth, portfolios, portfolio_item
from .schemas import portfolio

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker API")

# --- CORS KONFIGURATION (NEU) ---
# Erlaubt deinem React-Frontend, auf die API zuzugreifen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # URL deines Vite/React Frontends
    allow_credentials=True,
    allow_methods=["*"], # Erlaubt GET, POST, PUT, DELETE, etc.
    allow_headers=["*"], # Erlaubt alle Header (wichtig für Auth-Tokens)
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(portfolios.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(portfolio_item.router, prefix="/api/v1/portfolio_item", tags=["Portfolio Item"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected and initialized"}