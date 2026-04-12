import requests
import os
import yfinance as yf
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Asset, AssetPrice
from datetime import datetime, timedelta
from uuid import UUID
import time


class AssetService:
    def __init__(self):
        self.openfigi_url = "https://api.openfigi.com/v2/mapping"
        self.openfigi_key = os.getenv("OPENFIGI_API_KEY")

        # Currency cache
        self.exchange_cache = {}
        self.cache_duration = 15

    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            ticker.session = session

            # Versuch 1: fast_info (schnell)
            price = ticker.fast_info.last_price

            # Versuch 2: History Fallback (zuverlässiger)
            if not price:
                data = ticker.history(period="1d")
                if not data.empty:
                    price = data['Close'].iloc[-1]

            return float(price) if price else None
        except Exception as e:
            print(f"yfinance Price Error für {symbol}: {e}")
            return None

    def search_external_asset(self, symbol: Optional[str] = None, isin: Optional[str] = None) -> Optional[
        Dict[str, Any]]:
        query = isin if isin else symbol
        if not query:
            return None

        # 1. Schritt: yfinance Suche (Priorität wegen besserer regionaler Ticker)
        external_data = self._get_yfinance_metadata(query)

        # 2. Schritt: Falls yfinance nichts liefert -> OpenFIGI
        if not external_data:
            print(f"DEBUG: yfinance kein Treffer für {query}, versuche OpenFIGI...")
            external_data = self._get_openfigi_data(symbol, isin)

        if not external_data:
            return None

        # 3. Schritt: Preis und Währung finalisieren
        ticker_symbol = external_data["symbol"]

        # Nur wenn die Daten von OpenFIGI kamen, verifizieren wir die Währung nochmal via yfinance
        # (da OpenFIGI oft USD als Standard liefert)
        if external_data.get("source") == "openfigi":
            try:
                yf_ticker = yf.Ticker(ticker_symbol)
                yf_currency = yf_ticker.info.get("currency")
                if yf_currency:
                    external_data["currency"] = yf_currency.upper()
            except:
                pass

        live_price = self.get_current_price(ticker_symbol)
        if live_price is not None:
            external_data["current_price"] = live_price

        # 4. Schritt: Falls ISIN immer noch fehlt
        if not external_data.get("isin"):
            yf_isin = self._get_isin_via_yfinance(ticker_symbol)
            if yf_isin:
                external_data["isin"] = yf_isin

        return external_data

    # --- Private Hilfsmethoden ---

    def _get_openfigi_data(self, symbol, isin):
        exch_code = "US"
        job = {"idType": "ID_ISIN", "idValue": isin} if isin else {"idType": "TICKER", "idValue": symbol,
                                                                   "exchCode": exch_code}

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
                        "current_price": 0.0,
                        "source": "openfigi"
                    }
        except Exception as e:
            print(f"OpenFIGI Error: {e}")
        return None

    def _get_yfinance_metadata(self, query: str) -> Optional[Dict[str, Any]]:
        """Optimierte Metadaten-Suche mit Fokus auf .DE Ticker bei deutschen ISINs."""
        try:
            target_ticker = query

            # Speziallogik für deutsche ISINs
            if len(query) == 12 and query.upper().startswith("DE"):
                search = yf.Search(query, max_results=5)
                for quote in search.quotes:
                    symbol = quote.get("symbol", "")
                    if symbol.endswith(".DE"):
                        target_ticker = symbol
                        break
                if target_ticker == query and search.quotes:
                    target_ticker = search.quotes[0].get("symbol")

            ticker = yf.Ticker(target_ticker)
            info = ticker.info

            if info and 'symbol' in info:
                return {
                    "symbol": info.get("symbol").upper(),
                    "name": info.get("longName") or info.get("shortName"),
                    "asset_type": info.get("quoteType", "equity").lower(),
                    "currency": info.get("currency", "USD").upper(),
                    "isin": info.get("isin") or (query if len(query) == 12 else None),
                    "current_price": 0.0,
                    "source": "yfinance"
                }
        except Exception as e:
            print(f"yfinance Metadata Error: {e}")
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
        assets = db.query(Asset).all()
        updated_count = 0
        for asset in assets:
            try:
                new_price = self.get_current_price(asset.symbol)
                if new_price is not None:
                    price_entry = AssetPrice(
                        asset_id=asset.id,
                        price=new_price,
                        timestamp=datetime.now()
                    )
                    db.add(price_entry)
                    asset.last_api_update = datetime.now()
                    updated_count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"Update Fehler {asset.symbol}: {e}")
                continue
        db.commit()
        return updated_count

    def get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        if from_curr == to_curr:
            return 1.0

        pair = f"{from_curr}{to_curr}=X".upper()
        now = datetime.now()

        # 1. Prüfen, ob der Kurs im Cache ist UND ob er noch aktuell ist
        if pair in self.exchange_cache:
            rate, timestamp = self.exchange_cache[pair]
            if now - timestamp < timedelta(minutes=self.cache_duration):
                return rate

        # 2. Wenn nicht im Cache oder abgelaufen -> Neu laden
        try:
            ticker = yf.Ticker(pair)
            rate = ticker.fast_info.last_price

            if not rate:
                data = ticker.history(period="1d")
                rate = data['Close'].iloc[-1] if not data.empty else 1.0

            # 3. Mit aktuellem Zeitstempel speichern
            self.exchange_cache[pair] = (float(rate), now)
            return float(rate)

        except Exception as e:
            print(f"Wechselkurs-Fehler für {pair}: {e}")
            # Bei Fehlern: Falls wir einen alten Kurs im Cache haben, nutzen wir den als Fallback
            if pair in self.exchange_cache:
                return self.exchange_cache[pair][0]
            return 1.0

    def convert_price(self, price: float, from_currency: str, to_currency: str) -> float:
        rate = self.get_exchange_rate(from_currency.upper(), to_currency.upper())
        return price * rate

asset_service = AssetService()