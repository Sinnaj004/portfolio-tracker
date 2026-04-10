from sqlalchemy.orm import Session, joinedload
from typing import List, Union
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioItem, Asset
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
    # 1. Portfolio Check: Existiert es und gehört es dem User?
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    print(f"\n--- DEBUG START: Processing {item_in.symbol or item_in.isin} ---")

    # 2. Asset Suche in der lokalen Datenbank
    asset = None

    # Zuerst nach ISIN suchen (eindeutiger)
    if item_in.isin:
        asset = db.query(Asset).filter(Asset.isin == item_in.isin).first()

    # Wenn nicht gefunden, nach Symbol suchen
    if not asset and item_in.symbol:
        asset = db.query(Asset).filter(Asset.symbol == item_in.symbol.upper()).first()

    # 3. Externer Check & Merge-Logik
    if not asset:
        print("DEBUG: Asset nicht in DB. Starte externe Suche...")
        external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)

        if not external_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found externally")

        # Prüfen, ob das extern gefundene Symbol vielleicht DOCH schon in der DB ist
        # (Wichtig, wenn man via ISIN sucht und das Symbol schon ohne ISIN existiert)
        asset = db.query(Asset).filter(Asset.symbol == external_data["symbol"].upper()).first()

        if asset:
            print(f"DEBUG: Asset über externes Symbol '{asset.symbol}' in DB gefunden. Merge ISIN...")
            if not asset.isin and (external_data.get("isin") or item_in.isin):
                asset.isin = external_data.get("isin") or item_in.isin
        else:
            print("DEBUG: Erstelle komplett neues Asset...")
            asset = Asset(
                symbol=external_data["symbol"].upper(),
                name=external_data["name"],
                asset_type=external_data["asset_type"],
                currency=external_data["currency"],
                isin=external_data.get("isin") or item_in.isin
            )
            db.add(asset)
    else:
        print(f"DEBUG: Asset in DB gefunden: {asset.symbol}")
        # Falls Asset da ist, aber die ISIN noch fehlte: Jetzt nachpflegen!
        if not asset.isin and item_in.isin:
            print(f"DEBUG: Pflege ISIN {item_in.isin} für bestehendes Asset nach.")
            asset.isin = item_in.isin

    db.flush()  # Stellt sicher, dass 'asset.id' verfügbar ist

    # 4. PortfolioItem (Verknüpfung) verwalten
    db_item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.asset_id == asset.id
    ).first()

    if not db_item:
        print("DEBUG: Erstelle neuen Portfolio-Eintrag.")
        db_item = PortfolioItem(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            quantity=0,
            avg_cost_price=0
        )
        db.add(db_item)

    # 5. Werte aktualisieren (Mischkurs-Berechnung)
    if db_item.quantity > 0:
        total_cost_old = db_item.quantity * db_item.avg_cost_price
        total_cost_new = item_in.quantity * item_in.avg_cost_price

        new_total_quantity = db_item.quantity + item_in.quantity

        # Der gewichtete Durchschnitt
        db_item.avg_cost_price = (total_cost_old + total_cost_new) / new_total_quantity
        db_item.quantity = new_total_quantity
    else:
        # Erster Kauf dieses Assets
        db_item.quantity = item_in.quantity
        db_item.avg_cost_price = item_in.avg_cost_price

    db.commit()
    db.refresh(db_item)

    print(f"--- DEBUG END: Success (Asset: {asset.symbol}, ISIN: {asset.isin}) ---\n")
    return db_item

@router.get("/{portfolio_id}", response_model=List[PortfolioItemOut], status_code=status.HTTP_200_OK)
def get_all_portfolio_items(portfolio_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()

    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    return portfolio.items

@router.get("/{portfolio_id/items/{item_id}", response_model=PortfolioItemOut, status_code=status.HTTP_200_OK)
def get_portfolio_item(portfolio_id: UUID, item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    return item

@router.delete("/{portfolio_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(portfolio_id: UUID, item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    db.delete(item)
    db.commit()


@router.post("/{portfolio_id}/items/{item_id}/sell", response_model=Union[PortfolioItemOut, None])
def sell_portfolio_item(
        portfolio_id: UUID,
        item_id: UUID,
        sell_in: PortfolioItemSell,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # FIX 1: Nutze joinedload, damit das 'asset' Objekt geladen wird und nicht "string" liefert
    db_item = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset)
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

        # FIX 2: Nach dem Commit refresh aufrufen, um die Asset-Verknüpfung im Speicher zu behalten
        db.refresh(db_item)
        return db_item