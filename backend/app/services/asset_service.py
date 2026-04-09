import yfinance as yf
from typing import Optional, Dict, Any

class AssetService:
    @staticmethod
    def search_external_asset(
        symbol: Optional[str] = None,
        isin: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sucht extern nach Asset-Metadaten.
        Gibt ein Dictionary mit Daten zurück oder None.
        """
        search_query = isin if isin else symbol
        if not search_query:
            return None

        try:
            # yfinance Suche
            ticker_info = yf.Ticker(search_query)
            info = ticker_info.info

            # Wenn yfinance nichts Sinnvolles zurückgibt (z.B. kein 'name' oder 'longName')
            if not info or 'longName' not in info:
                return None

            return {
                "symbol": info.get("symbol", symbol).upper(),
                "name": info.get("longName") or info.get("shortName"),
                "asset_type": info.get("quoteType", "UNKNOWN").lower(),
                "currency": info.get("currency", "USD"),
                "isin": isin # yfinance liefert ISINs leider oft unzuverlässig
            }
        except Exception as e:
            print(f"Fehler bei der externen Suche: {e}")
            return None

asset_service = AssetService()