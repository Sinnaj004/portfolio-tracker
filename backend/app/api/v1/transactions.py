from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.models import Transaction, Portfolio, PortfolioItem, User
from app.schemas.transaction import TransactionOut

router = APIRouter()

@router.get("/{portfolio_id}/transactions", response_model=List[TransactionOut])
def get_portfolio_transactions(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liefert die gesamte Historie eines Portfolios (alle Assets).
    """
    # Zugriffsberechtigung prüfen
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio nicht gefunden")

    # Transactions laden und Assets direkt joinen für Name/Symbol
    transactions = db.query(Transaction).options(
        joinedload(Transaction.asset)
    ).filter(
        Transaction.portfolio_id == portfolio_id
    ).order_by(Transaction.transaction_date.desc()).all()

    for transaction in transactions:
        transaction.total_amount = transaction.total_amount * transaction.exchange_rate
        transaction.price_per_unit *= transaction.exchange_rate

        if transaction.realized_pnl:
            transaction.realized_pnl = transaction.realized_pnl  * transaction.exchange_rate

    # Mapping der Asset-Informationen in das Schema
    for tx in transactions:
        tx.asset_name = tx.asset.name
        tx.asset_symbol = tx.asset.symbol

    return transactions


@router.get("/{portfolio_id}/items/{item_id}/transactions", response_model=List[TransactionOut])
def get_item_transactions(
    portfolio_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liefert die Historie für ein spezifisches Asset innerhalb eines Portfolios.
    """
    # Prüfen, ob das Item existiert und dem User gehört
    item = db.query(PortfolioItem).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Asset im Portfolio nicht gefunden")

    # Nur Transaktionen für dieses spezifische Asset holen
    transactions = db.query(Transaction).options(
        joinedload(Transaction.asset)
    ).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.asset_id == item.asset_id
    ).order_by(Transaction.transaction_date.desc()).all()

    for tx in transactions:
        tx.asset_name = tx.asset.name
        tx.asset_symbol = tx.asset.symbol

    return transactions