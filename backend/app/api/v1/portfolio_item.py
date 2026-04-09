from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioItem, Asset
from app.schemas.portfolio_items import PortfolioItemOut, PortfolioItemCreate
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from decimal import Decimal
from ...services.asset_service import asset_service


router = APIRouter()


@router.post("/{portfolio_id}/items", response_model=PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def add_portfolio_item(portfolio_id: UUID, item_in: PortfolioItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Portfolio Check
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    # 2. Asset Check
    asset = db.query(Asset).filter(
        (Asset.isin == item_in.isin) if item_in.isin else (Asset.symbol == item_in.symbol.upper())
    ).first()

    # 3. Extern suchen, falls nicht in DB
    if not asset:
        external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)
        if not external_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

        # Asset neu anlegen
        asset = Asset(
            symbol=external_data["symbol"],
            name=external_data["name"],
            asset_type=external_data["asset_type"],
            currency=external_data["currency"],
            isin=item_in.isin  # Hier nutzen wir die ISIN aus dem Request
        )
        db.add(asset)
        db.flush()  # ID generieren

    # 4. PortfolioItem suchen oder erstellen
    db_item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.asset_id == asset.id
    ).first()

    if not db_item:
        db_item = PortfolioItem(portfolio_id=portfolio_id, asset_id=asset.id, quantity=0)
        db.add(db_item)

    # 5. Werte aktualisieren (WICHTIG: item_in nutzen!)
    db_item.quantity += item_in.quantity
    db_item.avg_cost_price = item_in.avg_cost_price  # Später hier ggf. Mischkurs berechnen

    db.commit()
    db.refresh(db_item)
    return db_item