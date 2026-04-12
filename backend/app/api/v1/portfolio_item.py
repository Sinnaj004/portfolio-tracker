from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from typing import List, Union
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioItem, Asset, AssetPrice
from app.schemas.portfolio_items import PortfolioItemOut, PortfolioItemCreate, PortfolioItemSell
from fastapi import APIRouter, Depends, HTTPException, status, Response
from uuid import UUID
from decimal import Decimal
from ...services.asset_service import asset_service


router = APIRouter()


@router.post("/{portfolio_id}/items", response_model=PortfolioItemOut, status_code=status.HTTP_201_CREATED)
def add_portfolio_item(
        portfolio_id: UUID,
        item_in: PortfolioItemCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Portfolio Check
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    print(f"\n--- DEBUG START: Processing {item_in.symbol or item_in.isin} ---")

    asset = None
    current_live_price = None

    # 2. Suche in lokaler DB
    if item_in.isin:
        asset = db.query(Asset).filter(Asset.isin == item_in.isin).first()
    if not asset and item_in.symbol:
        asset = db.query(Asset).filter(Asset.symbol == item_in.symbol.upper()).first()

    # 3. Logik: Nur extern suchen, wenn das Asset noch gar nicht existiert
    if not asset:
        print("DEBUG: Asset neu. Starte einmalige externe Suche...")
        external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)

        if not external_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found externally")

        current_live_price = external_data.get("current_price")

        asset = Asset(
            symbol=external_data["symbol"].upper(),
            name=external_data["name"],
            asset_type=external_data["asset_type"],
            currency=external_data["currency"],
            isin=external_data.get("isin") or item_in.isin,
            last_api_update=datetime.now()
        )
        db.add(asset)
        db.flush()  # ID generieren

        # Ersten Preis in Historie schreiben
        if current_live_price:
            new_price_entry = AssetPrice(asset_id=asset.id, price=current_live_price, timestamp=datetime.now())
            db.add(new_price_entry)
    else:
        print(f"DEBUG: Asset {asset.symbol} bereits vorhanden. Kein API-Call nötig.")
        # Wir holen den Preis für die Response einfach aus der bestehenden Historie
        latest = asset.latest_price_record
        current_live_price = latest.price if latest else 0

    # 4. PortfolioItem verwalten (Mischkurs etc.)
    db_item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.asset_id == asset.id
    ).first()

    if not db_item:
        db_item = PortfolioItem(portfolio_id=portfolio_id, asset_id=asset.id, quantity=0, avg_cost_price=0)
        db.add(db_item)

    if db_item.quantity > 0:
        total_cost_old = db_item.quantity * db_item.avg_cost_price
        total_cost_new = item_in.quantity * item_in.avg_cost_price
        new_total_quantity = db_item.quantity + item_in.quantity
        db_item.avg_cost_price = (total_cost_old + total_cost_new) / new_total_quantity
        db_item.quantity = new_total_quantity
    else:
        db_item.quantity = item_in.quantity
        db_item.avg_cost_price = item_in.avg_cost_price

    db.commit()
    db.refresh(db_item)

    # 5. Preisdaten an das Objekt für die Response heften
    db_item.asset.current_price = current_live_price
    db_item.asset.last_api_update = asset.last_api_update

    print(f"--- DEBUG END: Success (Asset: {asset.symbol}) ---\n")
    return db_item

@router.get("/{portfolio_id}", response_model=List[PortfolioItemOut], status_code=status.HTTP_200_OK)
def get_portfolio_items(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Abfrage mit "Eager Loading"
    # Wir laden PortfolioItem -> Asset -> prices in einer einzigen SQL-Abfrage (JOIN)
    items = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).filter(
        PortfolioItem.portfolio_id == portfolio_id
    ).all()

    # 2. Die virtuellen Felder für Pydantic befüllen
    for item in items:
        # Hier nutzen wir deine neue @property 'latest_price_record'
        latest = item.asset.latest_price_record
        if latest:
            # Wir "pappen" die Daten temporär an das Asset-Objekt
            # Pydantic liest sie dann für das AssetShort-Schema aus
            item.asset.current_price = latest.price
            item.asset.last_updated = latest.timestamp
        else:
            # Fallback, falls noch gar kein Preis in der DB existiert
            item.asset.current_price = 0.0
            item.asset.last_updated = None

    return items

@router.get("/{portfolio_id}/items/{item_id}", response_model=PortfolioItemOut, status_code=status.HTTP_200_OK)
def get_portfolio_item(portfolio_id: UUID, item_id: UUID, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    # 1. Abfrage mit joinedload für Asset und Preise
    item = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # 2. Preis-Daten für Pydantic befestigen
    latest = item.asset.latest_price_record
    if latest:
        item.asset.current_price = latest.price
        item.asset.last_api_update = latest.timestamp

    return item

@router.delete("/{portfolio_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(portfolio_id: UUID, item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    db.delete(item)
    db.commit()


@router.post("/{portfolio_id}/items/{item_id}/sell", response_model=Union[PortfolioItemOut, None])
def sell_portfolio_item(portfolio_id: UUID, item_id: UUID, sell_in: PortfolioItemSell, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Abfrage mit erweitertem joinedload (jetzt auch inklusive prices)
    db_item = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    # 2. Validierung
    if db_item.quantity < sell_in.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough shares. Quantity: {db_item.quantity}, Planned sell: {sell_in.quantity}"
        )

    # 3. Logik: Abziehen oder Löschen
    new_quantity = db_item.quantity - sell_in.quantity

    if new_quantity == 0:
        db.delete(db_item)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    else:
        db_item.quantity = new_quantity
        db.commit()
        db.refresh(db_item)

        # 4. Preisdaten für die API-Antwort anheften
        # Wir nutzen wieder die @property aus dem Asset-Model
        latest = db_item.asset.latest_price_record
        if latest:
            db_item.asset.current_price = latest.price
            # Achte darauf, ob dein Schema 'last_api_update' oder 'last_updated' heißt:
            db_item.asset.last_api_update = latest.timestamp
        else:
            db_item.asset.current_price = 0.0

        return db_item