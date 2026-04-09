from fastapi import FastAPI
from .db.session import engine, Base
from .models import models # Wichtig für die Registrierung der Models
from .api.v1 import auth

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker API")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
def health_check():
    return {"status": "online", "database": "connected and initialized"}