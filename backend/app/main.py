from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine, Base
from .api.v1 import auth, portfolios, portfolio_item, assets, dashboard, transactions
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger  # Neu für saubere Trigger
from .db.session import SessionLocal
from datetime import datetime, timezone  # timezone importiert
from .services.asset_service import asset_service

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)


def scheduled_price_update():
    # Wir brauchen eine eigene Session für den Hintergrund-Thread
    db = SessionLocal()
    try:
        # UTC Zeit für den Print-Log
        now_utc = datetime.now(timezone.utc)
        print(f"[{now_utc}] Automatischer Update-Job startet...")
        asset_service.update_all_assets_prices(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # Dem Scheduler explizit sagen, dass er in UTC arbeiten soll
    scheduler = BackgroundScheduler(timezone="UTC")

    # Job hinzufügen: Interval 30 Min, Startzeit ist JETZT in UTC
    scheduler.add_job(
        scheduled_price_update,
        trigger=IntervalTrigger(minutes=30),
        next_run_time=datetime.now(timezone.utc)
    )

    scheduler.start()
    yield
    # --- SHUTDOWN ---
    scheduler.shutdown()


app = FastAPI(title="Portfolio Tracker API", lifespan=lifespan)

# --- CORS KONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(portfolios.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(portfolio_item.router, prefix="/api/v1/portfolio_item", tags=["Portfolio Item"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(transactions.router, prefix="/api/v1/portfolio", tags=["Portfolio"])



@app.get("/")
def health_check():
    # Auch im Health-Check ist UTC eine gute Info
    return {
        "status": "online",
        "database": "connected and initialized",
        "server_time_utc": datetime.now(timezone.utc)
    }