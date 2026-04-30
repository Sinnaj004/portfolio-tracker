from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone # timezone hinzugefügt

from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioValue
from app.schemas.portfolio import PortfolioCreate, PortfolioOut, PortfolioPerformanceEntry
from app.services.snapshot_service import create_portfolio_snapshot

router = APIRouter()

@router.post("/", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id, Portfolio.name == portfolio.name).first()

    if existing_portfolio:
        raise HTTPException(status_code=400, detail="Portfolioname already exists")

    new_portfolio = Portfolio(name=portfolio.name, user_id=current_user.id, description=portfolio.description, currency=portfolio.currency)
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio


@router.post("/{portfolio_id}/snapshot", status_code=status.HTTP_201_CREATED)
def trigger_portfolio_snapshot(
        portfolio_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Sicherheit: Gehört das Portfolio dem User?
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio nicht gefunden")

    # 2. Snapshot erstellen
    try:
        snapshot = create_portfolio_snapshot(db, portfolio_id=portfolio_id)
        return {
            "message": "Snapshot erfolgreich erstellt",
            "timestamp": snapshot.timestamp,
            "actual_value": float(snapshot.actual_value),
            "invested_amount": float(snapshot.invested_amount)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Snapshot: {str(e)}")


@router.get("/{portfolio_id}/performance", response_model=List[PortfolioPerformanceEntry])
def get_portfolio_performance(
        portfolio_id: UUID,
        days: Optional[int] = Query(30, description="Zeitraum in Tagen"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Sicherheit
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio nicht gefunden oder keine Zugriffsberechtigung"
        )

    # 2. Zeitfilter berechnen (JETZT IN UTC)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 3. Snapshots abfragen
    snapshots = db.query(PortfolioValue).filter(
        PortfolioValue.portfolio_id == portfolio_id,
        PortfolioValue.timestamp >= start_date
    ).order_by(asc(PortfolioValue.timestamp)).all()

    # 4. Daten aufbereiten
    performance_trend = []
    for s in snapshots:
        actual = float(s.actual_value)
        invested = float(s.invested_amount)

        profit_loss = actual - invested
        profit_loss_pct = (profit_loss / invested * 100) if invested > 0 else 0

        performance_trend.append(
            PortfolioPerformanceEntry(
                timestamp=s.timestamp,
                actual_value=actual,
                invested_amount=invested,
                profit_loss=round(profit_loss, 2),
                profit_loss_pct=round(profit_loss_pct, 2)
            )
        )

    return performance_trend


@router.get("/", response_model=List[PortfolioOut], status_code=status.HTTP_200_OK)
def get_all_portfolios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()

@router.get("/{id}", response_model=PortfolioOut, status_code=status.HTTP_200_OK)
def get_specified_portfolio(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == id, Portfolio.user_id == current_user.id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return portfolio

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == id, Portfolio.user_id == current_user.id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.delete(portfolio)
    db.commit()