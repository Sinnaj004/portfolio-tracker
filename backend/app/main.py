from fastapi import FastAPI
from .db.session import engine, Base
from .models import models # Wichtig für die Registrierung der Models
from .api.v1 import auth
from .api.v1 import portfolios
from .schemas import portfolio

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker API")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(portfolios.router, prefix="/api/v1/portfolio", tags=["Portfolio"])

@app.get("/")
def health_check():
    return {"status": "online", "database": "connected and initialized"}