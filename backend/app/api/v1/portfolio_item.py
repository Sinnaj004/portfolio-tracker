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
    # 1. Portfolio Check (inkl. Währung)
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    # 2. Asset Logik (Suche/Erstellung)
    asset = None
    if item_in.isin:
        asset = db.query(Asset).filter(Asset.isin == item_in.isin).first()
    if not asset and item_in.symbol:
        asset = db.query(Asset).filter(Asset.symbol == item_in.symbol.upper()).first()

    if not asset:
        external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)
        if not external_data:
            raise HTTPException(status_code=404, detail="Asset not found externally")

        asset = db.query(Asset).filter(Asset.symbol == external_data["symbol"].upper()).first()
        if not asset:
            external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)

            # Strenger Check: Wenn kein Name da ist, existiert das Asset für uns nicht
            if not external_data or not external_data.get("name"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Asset '{item_in.symbol or item_in.isin}' wurde nicht gefunden oder ist unvollständig."
                )

            # ... restliche Logik zum Speichern ...
            asset = Asset(
                symbol=external_data["symbol"].upper(),
                name=external_data["name"],  # Hier wissen wir jetzt, dass er da ist
                asset_type=external_data.get("asset_type") or "stock",
                currency=(external_data.get("currency") or "USD").upper(),
                isin=external_data.get("isin") or item_in.isin,
                last_api_update=datetime.now()
            )

            db.add(asset)
            db.flush()
            if external_data.get("current_price"):
                db.add(AssetPrice(asset_id=asset.id, price=external_data["current_price"], timestamp=datetime.now()))

    # --- NEU: WÄHRUNGS- & TRANSAKTIONS-LOGIK ---

    asset_curr = (asset.currency or "EUR").upper()
    portfolio_curr = (portfolio.currency or "EUR").upper()  # Währung vom Portfolio!

    # Wechselkurs: 1 Asset_Curr = X Portfolio_Curr (z.B. 1 USD = 0.91 CHF)
    exchange_rate = float(asset_service.get_exchange_rate(asset_curr, portfolio_curr))

    # WICHTIG: User gibt Preis in Portfolio-Währung an (z.B. CHF).
    # Wir speichern in der DB den Preis pro Einheit in Asset-Währung (z.B. USD).
    purchase_price_asset_curr = float(item_in.avg_cost_price) / exchange_rate

    # Transaktion loggen
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        type="BUY",
        quantity=item_in.quantity,
        price_per_unit=purchase_price_asset_curr,  # In Asset-Währung
        fees=0.0,
        total_amount=float(item_in.quantity) * purchase_price_asset_curr,
        currency=asset_curr,
        exchange_rate=exchange_rate,  # Kurs zum Kaufzeitpunkt fixieren
        transaction_date=datetime.now()
    )
    db.add(new_transaction)

    # 4. PortfolioItem (Bestand & Mischkurs in Asset-Währung)
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

    if float(db_item.quantity) > 0:
        # Mischkurs-Berechnung (beide Werte liegen nun in Asset-Währung vor)
        total_cost_old = float(db_item.quantity) * float(db_item.avg_cost_price)
        total_cost_new = float(item_in.quantity) * purchase_price_asset_curr
        new_total_quantity = float(db_item.quantity) + float(item_in.quantity)

        db_item.avg_cost_price = (total_cost_old + total_cost_new) / new_total_quantity
        db_item.quantity = new_total_quantity
    else:
        db_item.quantity = item_in.quantity
        db_item.avg_cost_price = purchase_price_asset_curr

    db.commit()
    db.refresh(db_item)

    return db_item


@router.get("/{portfolio_id}", response_model=List[PortfolioItemOut], status_code=status.HTTP_200_OK)
def get_portfolio_items(
        portfolio_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Das Portfolio laden, um die Zielwährung zu bestimmen
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio nicht gefunden"
        )

    target_currency = (portfolio.currency or "EUR").upper()

    # 2. Portfolio-Items mit Assets und Preisen laden
    items = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).filter(
        PortfolioItem.portfolio_id == portfolio_id
    ).all()

    # 3. Daten für das Frontend aufbereiten und umrechnen
    for item in items:
        asset_curr = (item.asset.currency or "EUR").upper()

        # Den aktuellen Wechselkurs bestimmen: 1 Einheit der Asset-Währung = X Einheiten Portfolio-Währung
        # Beispiel: 1 USD = 0.89 CHF
        try:
            current_rate = float(asset_service.get_exchange_rate(asset_curr, target_currency))
        except Exception:
            current_rate = 1.0  # Fallback, falls API-Umrechnung fehlschlägt

        # --- A. Einstiegspreis (avg_cost_price) umrechnen ---
        # Er liegt in der DB in Asset-Währung (z.B. USD).
        # Wir rechnen ihn in CHF um, damit qty * avg_cost_price im Frontend den CHF-Wert ergibt.
        if item.avg_cost_price:
            item.avg_cost_price = float(item.avg_cost_price) * current_rate

        # --- B. Aktuellen Marktpreis umrechnen ---
        latest = item.asset.latest_price_record
        if latest:
            price_in_asset_curr = float(latest.price)
            # Aktuellen Kurs von USD nach CHF umrechnen
            item.asset.current_price = price_in_asset_curr * current_rate
            item.asset.last_updated = latest.timestamp
        else:
            item.asset.current_price = 0.0
            item.asset.last_updated = None

        # Hilfsfeld für das Frontend (optional)
        item.current_exchange_rate = current_rate

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
        joinedload(PortfolioItem.asset),
        joinedload(PortfolioItem.portfolio)
    ).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    # 2. Währungskontext bestimmen
    asset_curr = (db_item.asset.currency or "EUR").upper()
    portfolio_curr = (db_item.portfolio.currency or "EUR").upper()

    # Wechselkurs holen: 1 Einheit Asset_Curr = X Einheiten User_Curr (z.B. 1 USD = 0.92 EUR)
    current_rate = float(asset_service.get_exchange_rate(asset_curr, portfolio_curr))

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