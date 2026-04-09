# 🛠 Technologie-Stack & Architektur-Entscheidungen

Dieses Dokument dient als zentrale Referenz für die verwendeten Technologien im Portfolio-Tracker und erklärt, welche Komponente welche Aufgabe übernimmt.

---

## 🏗 Kern-Infrastruktur

| Komponente | Technologie | Verantwortung |
| :--- | :--- | :--- |
| **Container** | **Docker** | Isolation der Anwendung. Garantiert, dass die Software auf Linux (Dein System), Windows und dem späteren Server exakt gleich läuft. |
| **Orchestrierung** | **Docker Compose** | Verbindet Backend, Datenbank und Cache in einem gemeinsamen Netzwerk. |
| **Backend API** | **FastAPI (Python)** | Schnelle, moderne API-Schnittstelle. Verarbeitet die Logik und dient als Single Source of Truth für Web und iOS. |
| **Datenbank** | **PostgreSQL** | Speichert alle relationalen und sicherheitskritischen Daten (User, Portfolios, Transaktionen). |
| **Zeitreihen-Daten** | **TimescaleDB** | Eine PostgreSQL-Extension, die Millionen von historischen Preisdaten effizient speichert und abfragbar macht. |
| **Caching** | **Redis** | Blitzschneller Zwischenspeicher, um die Last auf die Datenbank und externe Finanz-APIs zu reduzieren. |

---

## 📂 Architektur-Entscheidungen (ADRs)

### 1. Von Parquet zu TimescaleDB
* **Ursprüngliche Idee:** Speicherung von Kursdaten in `.parquet` Dateien.
* **Entscheidung:** Nutzung von **TimescaleDB** innerhalb von PostgreSQL.
* **Grund:** Parquet ist super für statische Analyse, aber wir brauchen ein System, das ständig neue Kurse einspeist. TimescaleDB erlaubt uns, normales SQL zu nutzen, ist aber für Zeitreihendaten optimiert (hybride Tabellen).

### 2. API-First Ansatz mit FastAPI
* **Entscheidung:** Fokus auf eine strikte Trennung von Backend und Frontend.
* **Grund:** Da später eine **iOS-App** folgen soll, muss das Backend eine reine API sein. FastAPI liefert automatisch eine Dokumentation (Swagger), die uns beim Bau der App hilft.

### 3. Hybrides Such-Konzept für Assets
* **Logik:** Cache (Redis) ➔ Datenbank (Postgres) ➔ Externe API.
* **Grund:** Kostenersparnis und Geschwindigkeit. Wir fragen externe Datenanbieter nur ab, wenn wir ein Asset wirklich noch nie gesehen haben.

---

## 📋 Software-Anforderungen für Entwicklung
* **IDE:** PyCharm (mit .env & Docker Plugins).
* **Datenbank-Management:** DBeaver oder das eingebaute Database-Tool in PyCharm (zum Visualisieren der Tabellen).
* **Modellierung:** [dbdiagram.io](https://dbdiagram.io) für das ER-Modell.

---

## 🚀 Zukünftige Erweiterungen
* **Frontend:** Next.js (React) für eine schnelle Web-Erfahrung.
* **Mobile:** Native iOS App (Swift/SwiftUI), die dieselbe FastAPI-Schnittstelle nutzt.