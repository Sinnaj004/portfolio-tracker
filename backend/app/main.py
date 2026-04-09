from fastapi import FastAPI
import os

app = FastAPI(title="Portfolio Tracker API")

@app.get("/")
def read_root():
    # Test: Liest er die Variable aus der .env?
    db_name = os.getenv("POSTGRES_DB", "Nicht gefunden")
    return {
        "status": "online",
        "database_connected_to": db_name,
        "message": "Willkommen bei deinem Portfolio Tracker!"
    }