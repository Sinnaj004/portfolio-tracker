# Schlankes Python-Image als Basis
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten für PostgreSQL installieren
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Requirements kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den Rest des Codes kopieren
COPY . .

# Startbefehl (wird in docker-compose überschrieben, ist aber gut als Fallback)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]