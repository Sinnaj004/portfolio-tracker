from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine, Base
from .api.v1 import auth, portfolios, portfolio_item, assets, dashboard
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from .db.session import SessionLocal
from datetime import datetime
from .services.asset_service import asset_service

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)

def scheduled_price_update():
    # Wir brauchen eine eigene Session für den Hintergrund-Thread
    db = SessionLocal()
    try:
        print(f"[{datetime.now()}] Automatischer Update-Job startet...")
        asset_service.update_all_assets_prices(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    scheduler = BackgroundScheduler()
    # Beispiel: Alle 30 Minuten
    scheduler.add_job(scheduled_price_update, 'interval', minutes=30, next_run_time=datetime.now())
    scheduler.start()
    yield
    # --- SHUTDOWN ---
    scheduler.shutdown()

app = FastAPI(title="Portfolio Tracker API", lifespan=lifespan)

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
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/")
def health_check():
    return {"status": "online", "database": "connected and initialized"}

