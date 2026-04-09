from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Die URL nutzt den Service-Namen 'db' aus deiner docker-compose.yml
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@db:5432/{os.getenv('POSTGRES_DB')}"

# Der Engine ist der Startpunkt für SQLAlchemy
engine = create_engine(DATABASE_URL)

# SessionLocal ist die Fabrik für Datenbank-Sitzungen
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Davon erben später alle unsere Tabellen-Klassen
Base = declarative_base()
