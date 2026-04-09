from fastapi import FastAPI
from .db.session import engine, Base
from .models import models # Wichtig für die Registrierung der Models

# Erstellt alle Tabellen in Postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker API")

@app.get("/")
def health_check():
    return {"status": "online", "database": "connected and initialized"}