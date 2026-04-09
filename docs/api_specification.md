# 📡 API-Spezifikation (v1)

Dieses Dokument definiert die Endpunkte, Eingabeparameter und Antwortformate. Alle Endpunkte liefern, sofern nicht anders angegeben, Daten im **JSON-Format** zurück.

---

## 🔐 Authentifizierung & Benutzer
Basis-Pfad: `/api/v1/auth`

| Methode | Endpunkt | Beschreibung | Schutz |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Erstellt einen neuen User-Account. | Öffentlich |
| `POST` | `/login` | Authentifiziert den User & gibt ein JWT-Token zurück. | Öffentlich |
| `GET` | `/me` | Gibt die Daten des aktuell eingeloggten Users zurück. | JWT erforderlich |

---

## 📊 Portfolio-Management
Basis-Pfad: `/api/v1/portfolios`

| Methode | Endpunkt | Beschreibung | Schutz |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Listet alle Portfolios des Users auf. | JWT |
| `POST` | `/` | Erstellt ein neues Portfolio (z.B. "Krypto"). | JWT |
| `GET` | `/{id}` | Detailansicht eines Portfolios inkl. aller Items. | JWT (Besitzer) |
| `DELETE`| `/{id}` | Löscht ein Portfolio. | JWT (Besitzer) |

---

## 🔍 Asset-Suche & Markt-Daten
Basis-Pfad: `/api/v1/assets`

### `GET /search`
Sucht global nach Aktien, Krypto oder ETFs.
* **Query Params:** `q` (String, Suchbegriff)
* **Logik:** 1. Check Redis Cache.
    2. Check Lokale DB.
    3. Fallback: Externer API-Call (z.B. Yahoo Finance).
* **Response:** Liste von Objekten mit `symbol`, `name`, `type`, `currency`.

---

## 🛠 Admin-Schnittstellen
Basis-Pfad: `/api/v1/admin`

| Methode | Endpunkt | Beschreibung | Schutz |
| :--- | :--- | :--- | :--- |
| `GET` | `/stats` | Systemweite Statistiken (User-Anzahl, API-Last). | Admin Only |
| `POST` | `/assets/sync` | Erzwingt ein Update der historischen Kurse. | Admin Only |

---

## ⚠️ Fehlerbehandlung
Die API nutzt Standard-HTTP-Statuscodes:
* `200 OK` / `201 Created` - Erfolg.
* `400 Bad Request` - Validierungsfehler (Pydantic).
* `401 Unauthorized` - Token fehlt oder ist ungültig.
* `403 Forbidden` - Zugriff verweigert (z.B. kein Admin).
* `404 Not Found` - Ressource existiert nicht.