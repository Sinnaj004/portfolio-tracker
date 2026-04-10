import requests
import os
import yfinance as yf
from typing import Optional, Dict, Any


class AssetService:
    def __init__(self):
        self.openfigi_url = "https://api.openfigi.com/v2/mapping"
        self.openfigi_key = os.getenv("OPENFIGI_API_KEY")

    def search_external_asset(self, symbol: Optional[str] = None, isin: Optional[str] = None) -> Optional[
        Dict[str, Any]]:
        query = isin if isin else symbol
        if not query:
            return None

        # 1. Schritt: OpenFIGI für saubere Stammdaten (Name, Ticker)
        external_data = self._get_openfigi_data(symbol, isin)

        if not external_data:
            return None

        # 2. Schritt: Wenn ISIN noch fehlt, via yfinance nachhelfen
        if not external_data.get("isin"):
            print(f"DEBUG: OpenFIGI hat keine ISIN für {external_data['symbol']} geliefert. Versuche yfinance...")
            yf_isin = self._get_isin_via_yfinance(external_data["symbol"])
            if yf_isin:
                external_data["isin"] = yf_isin
                print(f"DEBUG: yfinance hat ISIN gefunden: {yf_isin}")

        return external_data

    def _get_openfigi_data(self, symbol, isin):
        job = {"idType": "ID_ISIN", "idValue": isin} if isin else {"idType": "TICKER", "idValue": symbol,
                                                                   "exchCode": "US"}
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
                        "isin": isin  # Falls wir mit ISIN gesucht haben, geben wir sie zurück
                    }
        except Exception as e:
            print(f"OpenFIGI Error: {e}")
        return None

    def _get_isin_via_yfinance(self, symbol: str) -> Optional[str]:
        try:
            # yf.Search ist oft besser für ISINs als .info
            search = yf.Search(symbol, max_results=1)
            if search.quotes:
                return search.quotes[0].get("isincode")
        except:
            pass
        return None


asset_service = AssetService()