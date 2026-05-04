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
from.services.snapshot_service import portfolio_service
from apscheduler.triggers.cron import CronTrigger
import logging

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


def scheduled_portfolio_snapshots():
    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        print(f"[{now_utc}] 📸 Starte automatische Portfolio-Snapshots...")

        all_portfolios = portfolio_service.get_all_portfolios(db)

        for p in all_portfolios:
            portfolio_service.create_portfolio_snapshot(db, portfolio_id=p.id)

        print(f"[{now_utc}] ✅ Alle Snapshots erfolgreich erstellt.")
    except Exception as e:
        print(f"🚨 Fehler beim Snapshot-Job: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Scheduler initialisieren
    scheduler = BackgroundScheduler(timezone="UTC")

    # 2. Preis-Update (Alle 30 Min)
    scheduler.add_job(
        scheduled_price_update,
        trigger=IntervalTrigger(minutes=30),
        next_run_time=datetime.now(timezone.utc),
        id="price_update_task"
    )

    # 3. Snapshot-Job (Täglich)
    # Wir fügen 'next_run_time=datetime.now(timezone.utc)' hinzu,
    # damit er SOFORT beim Start einmal läuft zum Testen!
    scheduler.add_job(
        scheduled_portfolio_snapshots,
        trigger=CronTrigger(hour=23, minute=59),
        next_run_time=datetime.now(timezone.utc),
        id="daily_snapshot_task"
    )

    scheduler.start()
    print("🚀 APScheduler gestartet: Preis-Updates (30m) und Daily Snapshots aktiv.")

    yield

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