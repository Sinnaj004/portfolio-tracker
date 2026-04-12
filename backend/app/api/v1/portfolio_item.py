from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from typing import List, Union
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioItem, Asset, AssetPrice, Transaction
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
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    print(f"\n--- DEBUG START: Processing {item_in.symbol or item_in.isin} ---")

    asset = None
    current_live_price = None

    # 2. Suche in lokaler DB (Erster Check)
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

        # Zweiter Check nach API-Suche (Unique Constraint Schutz)
        asset = db.query(Asset).filter(Asset.symbol == external_data["symbol"].upper()).first()

        if not asset:
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
            db.flush()  # ID für Preis-Eintrag generieren

            if current_live_price:
                new_price_entry = AssetPrice(asset_id=asset.id, price=current_live_price, timestamp=datetime.now())
                db.add(new_price_entry)
        else:
            print(f"DEBUG: Asset {asset.symbol} nach API-Abgleich doch gefunden.")
            if not asset.isin and external_data.get("isin"):
                asset.isin = external_data["isin"]

            latest = asset.latest_price_record
            current_live_price = latest.price if latest else external_data.get("current_price")
    else:
        print(f"DEBUG: Asset {asset.symbol} bereits vorhanden.")
        latest = asset.latest_price_record
        current_live_price = latest.price if latest else 0

    # --- NEU: TRANSAKTIONS-LOGIK (BUY) ---

    # Währungen und Wechselkurs ermitteln
    asset_curr = (asset.currency or "EUR").upper()
    user_currency = getattr(current_user, "preferred_currency", "EUR") or "EUR"

    # Wechselkurs zum Kaufzeitpunkt aus dem Cache/API holen
    exchange_rate = asset_service.get_exchange_rate(asset_curr, user_currency)

    # Transaktion in das Logbuch schreiben
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        type="BUY",
        quantity=item_in.quantity,
        price_per_unit=item_in.avg_cost_price,
        fees=0.0,
        total_amount=float(item_in.quantity) * float(item_in.avg_cost_price),
        currency=asset_curr,
        exchange_rate=exchange_rate,
        transaction_date=datetime.now()
    )
    db.add(new_transaction)

    # 4. PortfolioItem verwalten (Bestand & Mischkurs)
    db_item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.asset_id == asset.id
    ).first()

    if not db_item:
        db_item = PortfolioItem(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            quantity=0,
            avg_cost_price=0
        )
        db.add(db_item)

    # Mischkurs-Berechnung bei Nachkäufen
    if db_item.quantity > 0:
        total_cost_old = float(db_item.quantity) * float(db_item.avg_cost_price)
        total_cost_new = float(item_in.quantity) * float(item_in.avg_cost_price)
        new_total_quantity = float(db_item.quantity) + float(item_in.quantity)

        db_item.avg_cost_price = (total_cost_old + total_cost_new) / new_total_quantity
        db_item.quantity = new_total_quantity
    else:
        # Erstkauf
        db_item.quantity = item_in.quantity
        db_item.avg_cost_price = item_in.avg_cost_price

    # 5. Finale Speicherung
    db.commit()
    db.refresh(db_item)

    # Preisdaten für die API-Response anheften (Virtual Fields)
    db_item.asset.current_price = current_live_price
    db_item.asset.last_api_update = asset.last_api_update

    print(f"--- DEBUG END: Success (Asset: {asset.symbol}, Rate: {exchange_rate}) ---\n")

    return db_item


@router.get("/{portfolio_id}", response_model=List[PortfolioItemOut], status_code=status.HTTP_200_OK)
def get_portfolio_items(
        portfolio_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Abfrage mit "Eager Loading"
    items = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).filter(
        PortfolioItem.portfolio_id == portfolio_id
    ).all()

    # User Währung bestimmen (Fallback auf EUR)
    user_currency = getattr(current_user, "preferred_currency", "EUR") or "EUR"

    # 2. Die virtuellen Felder befüllen + Währungsumrechnung
    for item in items:
        latest = item.asset.latest_price_record
        if latest:
            price_in_asset_curr = float(latest.price)
            asset_curr = item.asset.currency or "EUR"

            # UMRECHNUNG: Falls Asset-Währung (z.B. USD) != User-Währung (z.B. EUR)
            if asset_curr.upper() != user_currency.upper():
                rate = asset_service.get_exchange_rate(asset_curr, user_currency)
                item.asset.current_price = price_in_asset_curr * rate
            else:
                item.asset.current_price = price_in_asset_curr

            item.asset.last_updated = latest.timestamp
        else:
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
def sell_portfolio_item(
        portfolio_id: UUID,
        item_id: UUID,
        sell_in: PortfolioItemSell,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Item inkl. Asset laden
    db_item = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset)
    ).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    # 2. Währungskontext bestimmen
    asset_curr = (db_item.asset.currency or "EUR").upper()
    user_curr = (getattr(current_user, "preferred_curency", "EUR") or "EUR").upper()

    # Wechselkurs holen: 1 Einheit Asset_Curr = X Einheiten User_Curr (z.B. 1 USD = 0.92 EUR)
    current_rate = float(asset_service.get_exchange_rate(asset_curr, user_curr))

    # 3. Verkaufspreis bestimmen & ggf. umrechnen
    # Wir speichern in der DB IMMER in Asset-Währung (z.B. USD)
    if sell_in.sale_price is not None:
        # User gibt Preis in seiner Währung an (z.B. EUR).
        # Umrechnung in Asset-Währung: EUR / Rate = USD
        final_sale_price_asset_curr = float(sell_in.sale_price) / current_rate
    else:
        # Fallback auf Marktpreis (dieser liegt bereits in Asset-Währung vor)
        latest = db_item.asset.latest_price_record
        if not latest:
            raise HTTPException(status_code=400, detail="Kein Marktpreis verfügbar. Bitte Preis manuell angeben.")
        final_sale_price_asset_curr = float(latest.price)

    # 4. PnL Berechnung (In der Währung des Assets)
    # (Verkaufspreis USD - Einkaufspreis USD) * Menge
    pnl_in_asset_curr = (final_sale_price_asset_curr - float(db_item.avg_cost_price)) * float(sell_in.quantity)

    # 5. Transaktion loggen
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=db_item.asset_id,
        type="SELL",
        quantity=sell_in.quantity,
        price_per_unit=final_sale_price_asset_curr,  # In USD
        fees=0.0,
        total_amount=float(sell_in.quantity) * final_sale_price_asset_curr,
        currency=asset_curr,  # "USD"
        exchange_rate=current_rate,  # 0.92 (Wichtig für Rückrechnung: USD * 0.92 = EUR)
        realized_pnl=pnl_in_asset_curr,
        transaction_date=sell_in.sale_date or datetime.now()
    )
    db.add(new_transaction)

    # 6. Bestand anpassen oder löschen
    new_quantity = float(db_item.quantity) - float(sell_in.quantity)

    if new_quantity <= 0:
        db.delete(db_item)
        db.commit()
        # Bei vollständigem Verkauf geben wir 204 zurück
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    db_item.quantity = new_quantity
    db.commit()
    db.refresh(db_item)

    # Preisdaten für die Response-Vorschau (optional)
    db_item.asset.current_price = final_sale_price_asset_curr

    return db_item