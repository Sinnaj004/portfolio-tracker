from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from decimal import Decimal
from app.models.models import Portfolio, PortfolioItem, Asset, AssetPrice, PortfolioValue
from app.services.asset_service import asset_service



class PortfolioService:
    def create_portfolio_snapshot(self, db: Session, portfolio_id: UUID):
        # 1. Portfolio und Items holen
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            print(f"Fehler: Portfolio {portfolio_id} nicht gefunden!")
            return None

        portfolio_items = db.query(PortfolioItem).filter(PortfolioItem.portfolio_id == portfolio_id).all()
        portfolio_curr = (portfolio.currency or "EUR").upper()

        total_actual_value = Decimal("0.0")
        total_invested_amount = Decimal("0.0")

        for item in portfolio_items:
            # 2. Den aktuellsten Preis suchen (in Asset-Währung!)
            price_record = db.query(AssetPrice) \
                .filter(AssetPrice.asset_id == item.asset_id) \
                .order_by(desc(AssetPrice.timestamp)) \
                .first()

            if not price_record:
                print(f"Warnung: Kein Preis für Asset {item.asset_id} gefunden!")
                continue

            # 3. Währungsumrechnung
            asset_curr = (item.asset.currency or "EUR").upper()

            try:
                # Wir holen den aktuellen Kurs von Asset-Währung zu Portfolio-Währung
                exchange_rate = Decimal(str(asset_service.get_exchange_rate(asset_curr, portfolio_curr)))
            except Exception as e:
                print(f"Warnung: Wechselkursfehler für {asset_curr}->{portfolio_curr}: {e}")
                exchange_rate = Decimal("1.0")

            # 4. Werte berechnen
            # Preis (Asset-Währung) * Kurs = Preis (Portfolio-Währung)
            current_price_portfolio_curr = Decimal(str(price_record.price)) * exchange_rate

            quantity = Decimal(str(item.quantity))
            avg_cost = Decimal(str(item.avg_cost_price))  # Ist bereits in Portfolio-Währung gespeichert

            item_actual = current_price_portfolio_curr * quantity
            item_invested = avg_cost * quantity

            # 5. Auf Gesamtsumme addieren
            total_actual_value += item_actual
            total_invested_amount += item_invested

        # 6. Snapshot speichern
        new_snapshot = PortfolioValue(
            portfolio_id=portfolio_id,
            actual_value=total_actual_value,
            invested_amount=total_invested_amount
            # timestamp wird durch den default im Model (UTC) automatisch gesetzt
        )

        db.add(new_snapshot)
        db.commit()
        db.refresh(new_snapshot)

        return new_snapshot

    def get_all_portfolios(self, db: Session, ):
        return db.query(Portfolio).all()

portfolio_service = PortfolioService()