from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, PortfolioItem, User
from app.schemas.PortfolioSummary import PortfolioSummary
from app.services.asset_service import asset_service

router = APIRouter()


@router.get("/summary", response_model=List[PortfolioSummary])
def get_dashboard_summary(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Alle Portfolios des Users inkl. Items und Assets in einer Abfrage laden
    portfolios = db.query(Portfolio).options(
        joinedload(Portfolio.items).joinedload(PortfolioItem.asset)
    ).filter(Portfolio.user_id == current_user.id).all()

    summary_list = []

    for portfolio in portfolios:
        total_value = Decimal("0.00")
        total_invested = Decimal("0.00")
        portfolio_curr = (portfolio.currency or "EUR").upper()

        for item in portfolio.items:
            # 1. Investiertes Kapital (bereits in Portfolio-Währung gespeichert!)
            qty = Decimal(str(item.quantity))
            avg_price = Decimal(str(item.avg_cost_price))
            total_invested += qty * avg_price

            # 2. Aktueller Marktwert (muss live umgerechnet werden)
            asset_curr = (item.asset.currency or "EUR").upper()

            try:
                # Wechselkurs holen (Asset -> Portfolio)
                current_rate = Decimal(str(asset_service.get_exchange_rate(asset_curr, portfolio_curr)))

                # Letzten Preis aus der DB nutzen (latest_price_record ist ein Property/Relation)
                latest_record = item.asset.latest_price_record
                price_in_asset_curr = Decimal(str(latest_record.price)) if latest_record else Decimal("0.00")

                # Zum Gesamtwert addieren (Menge * Preis * Kurs)
                total_value += qty * (price_in_asset_curr * current_rate)
            except Exception:
                # Fallback: Wenn Kurs oder Preis fehlt, nehmen wir den Einstandswert für den Wert
                total_value += qty * avg_price

        # 3. Berechnungen finalisieren
        profit_abs = total_value - total_invested
        profit_pct = Decimal("0.00")
        if total_invested > 0:
            profit_pct = (profit_abs / total_invested) * 100

        summary_list.append(PortfolioSummary(
            id=portfolio.id,
            name=portfolio.name,
            currency=portfolio_curr,
            total_value=total_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_invested=total_invested.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            profit_loss_abs=profit_abs.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            profit_loss_pct=profit_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            item_count=len(portfolio.items)
        ))

    return summary_list