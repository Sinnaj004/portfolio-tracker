import requests
import os
import yfinance as yf
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Asset, AssetPrice
from datetime import datetime
from uuid import UUID
from sqlalchemy import Numeric
import time

class AssetService:
    def __init__(self):
        self.openfigi_url = "https://api.openfigi.com/v2/mapping"
        self.openfigi_key = os.getenv("OPENFIGI_API_KEY")


    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)

            # Wir erzwingen eine Session mit einem User-Agent
            session = requests.Session()
            session.headers.update({
                                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            ticker.session = session

            # Versuch es mit 'fast_info'
            price = ticker.fast_info.last_price

            # Falls fast_info immer noch zickt, nimm den Ausweichweg:
            if not price:
                data = ticker.history(period="1d")
                if not data.empty:
                    price = data['Close'].iloc[-1]

            return float(price) if price else None
        except Exception as e:
            print(f"yfinance Price Error für {symbol}: {e}")
            return None

    # --- Stammdaten-Suche ---
    def search_external_asset(self, symbol: Optional[str] = None, isin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        query = isin if isin else symbol
        if not query:
            return None

        # 1. Schritt: Stammdaten via OpenFIGI
        external_data = self._get_openfigi_data(symbol, isin)
        if not external_data:
            return None

        # 2. Schritt: Preis über die neue separate Funktion holen
        ticker_symbol = external_data["symbol"]
        live_price = self.get_current_price(ticker_symbol)
        if live_price is not None:
            external_data["current_price"] = live_price

        # 3. Schritt: Falls ISIN fehlt, via yfinance suchen
        if not external_data.get("isin"):
            yf_isin = self._get_isin_via_yfinance(ticker_symbol)
            if yf_isin:
                external_data["isin"] = yf_isin

        return external_data

    # --- Private Hilfsmethoden ---
    def _get_openfigi_data(self, symbol, isin):
        job = {"idType": "ID_ISIN", "idValue": isin} if isin else {"idType": "TICKER", "idValue": symbol, "exchCode": "US"}
        try:
            headers = {'Content-Type': 'application/json'}
            if self.openfigi_key: headers['X-OPENFIGI-APIKEY'] = self.openfigi_key

            response = requests.post(self.openfigi_url, json=[job], headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data[0]:
                    res = data[0]["data"][0]
                    return {
                        "symbol": res.get("ticker").upper(),
                        "name": res.get("name"),
                        "asset_type": res.get("securityType", "equity").lower(),
                        "currency": "USD",
                        "isin": isin,
                        "current_price": 0.0
                    }
        except Exception as e:
            print(f"OpenFIGI Error: {e}")
        return None

    def _get_isin_via_yfinance(self, symbol: str) -> Optional[str]:
        try:
            search = yf.Search(symbol, max_results=1)
            if search.quotes:
                return search.quotes[0].get("isincode")
        except:
            pass
        return None

    def update_all_assets_prices(self, db: Session):
        """Holt für alle bekannten Assets die aktuellen Kurse und speichert sie."""
        assets = db.query(Asset).all()
        updated_count = 0

        print(f"DEBUG: Starte globales Preis-Update für {len(assets)} Assets...")

        for asset in assets:
            try:
                # 1. API nach aktuellem Preis fragen
                new_price = self.get_current_price(asset.symbol)

                if new_price is not None:
                    # 2. Neuen Preis in die Historie schreiben
                    price_entry = AssetPrice(
                        asset_id=asset.id,
                        price=new_price,
                        timestamp=datetime.now()
                    )
                    db.add(price_entry)

                    # 3. Zeitstempel im Asset-Stamm hintelegen
                    asset.last_api_update = datetime.now()
                    updated_count += 1
                    print(f"DEBUG: {asset.symbol} aktualisiert: {new_price}")

                # Kurze Pause, um API-Limits (Rate Limiting) zu respektieren
                time.sleep(0.5)

            except Exception as e:
                print(f"FEHLER: Konnte {asset.symbol} nicht aktualisieren: {e}")
                continue

        db.commit()
        return updated_count


asset_service = AssetService()