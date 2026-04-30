from datetime import datetime, timezone # timezone hinzugefügt
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Union
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User, PortfolioItem, Asset, AssetPrice, Transaction
from app.schemas.portfolio_items import PortfolioItemOut, PortfolioItemCreate, PortfolioItemSell
from fastapi import APIRouter, Depends, HTTPException, status, Response
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio nicht gefunden")

    # 2. Asset Logik
    asset = None
    if item_in.isin:
        asset = db.query(Asset).filter(Asset.isin == item_in.isin).first()
    if not asset and item_in.symbol:
        asset = db.query(Asset).filter(Asset.symbol == item_in.symbol.upper()).first()

    if not asset:
        external_data = asset_service.search_external_asset(symbol=item_in.symbol, isin=item_in.isin)
        if not external_data or not external_data.get("name"):
            raise HTTPException(status_code=404, detail="Asset nicht gefunden.")

        asset = Asset(
            symbol=external_data["symbol"].upper(),
            name=external_data["name"],
            asset_type=external_data.get("asset_type") or "stock",
            currency=(external_data.get("currency") or "USD").upper(),
            isin=external_data.get("isin") or item_in.isin,
            last_api_update=datetime.now(timezone.utc) # Geändert auf UTC
        )
        db.add(asset)
        db.flush()
        if external_data.get("current_price"):
            db.add(AssetPrice(
                asset_id=asset.id,
                price=external_data["current_price"],
                timestamp=datetime.now(timezone.utc) # Geändert auf UTC
            ))

    # --- PRÄZISE BERECHNUNGEN MIT DECIMAL ---
    input_qty = Decimal(str(item_in.quantity))
    input_price_portfolio_curr = Decimal(str(item_in.avg_cost_price))

    asset_curr = (asset.currency or "EUR").upper()
    portfolio_curr = (portfolio.currency or "EUR").upper()
    exchange_rate = Decimal(str(asset_service.get_exchange_rate(asset_curr, portfolio_curr)))

    purchase_price_asset_curr = input_price_portfolio_curr / exchange_rate

    # 3. Transaktion loggen
    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        type="BUY",
        quantity=input_qty,
        price_per_unit=purchase_price_asset_curr,
        fees=Decimal("0.0"),
        total_amount=input_qty * purchase_price_asset_curr,
        currency=asset_curr,
        exchange_rate=exchange_rate,
        transaction_date=datetime.now(timezone.utc) # Geändert auf UTC
    )
    db.add(new_transaction)

    # 4. PortfolioItem aktualisieren
    db_item = db.query(PortfolioItem).filter(
        PortfolioItem.portfolio_id == portfolio_id,
        PortfolioItem.asset_id == asset.id
    ).first()

    if not db_item:
        db_item = PortfolioItem(
            portfolio_id=portfolio_id,
            asset_id=asset.id,
            quantity=input_qty,
            avg_cost_price=input_price_portfolio_curr,
            avg_exchange_rate=exchange_rate
        )
        db.add(db_item)
    else:
        current_qty = Decimal(str(db_item.quantity))
        current_avg_price_port_curr = Decimal(str(db_item.avg_cost_price))
        new_total_quantity = current_qty + input_qty

        total_cost_old_port_curr = current_qty * current_avg_price_port_curr
        total_cost_new_port_curr = input_qty * input_price_portfolio_curr

        db_item.avg_cost_price = (total_cost_old_port_curr + total_cost_new_port_curr) / new_total_quantity

        current_avg_fx = Decimal(str(db_item.avg_exchange_rate or exchange_rate))
        total_fx_old = current_qty * current_avg_fx
        total_fx_new = input_qty * exchange_rate
        db_item.avg_exchange_rate = (total_fx_old + total_fx_new) / new_total_quantity

        db_item.quantity = new_total_quantity

    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/{portfolio_id}", response_model=List[PortfolioItemOut], status_code=status.HTTP_200_OK)
def get_portfolio_items(
        portfolio_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio nicht gefunden")

    target_currency = (portfolio.currency or "EUR").upper()

    items = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices)
    ).filter(
        PortfolioItem.portfolio_id == portfolio_id
    ).all()

    for item in items:
        asset_curr = (item.asset.currency or "EUR").upper()
        if item.avg_cost_price:
            item.avg_cost_price = Decimal(str(item.avg_cost_price))

        try:
            current_rate = Decimal(str(asset_service.get_exchange_rate(asset_curr, target_currency)))
        except Exception:
            current_rate = Decimal("1.0")

        latest = item.asset.latest_price_record
        if latest:
            item.asset.current_price = Decimal(str(latest.price)) * current_rate
            item.asset.last_updated = latest.timestamp
        else:
            item.asset.current_price = Decimal("0.0")
            item.asset.last_updated = None

        item.current_exchange_rate = current_rate

    return items

@router.get("/{portfolio_id}/items/{item_id}", response_model=PortfolioItemOut, status_code=status.HTTP_200_OK)
def get_portfolio_item(
    portfolio_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(PortfolioItem).options(
        joinedload(PortfolioItem.asset).joinedload(Asset.prices),
        joinedload(PortfolioItem.portfolio)
    ).join(Portfolio).filter(
        PortfolioItem.id == item_id,
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    target_currency = (item.portfolio.currency or "EUR").upper()
    asset_curr = (item.asset.currency or "EUR").upper()

    if item.avg_cost_price:
        item.avg_cost_price = Decimal(str(item.avg_cost_price))

    try:
        current_rate = Decimal(str(asset_service.get_exchange_rate(asset_curr, target_currency)))
    except Exception:
        current_rate = Decimal("1.0")

    latest = item.asset.latest_price_record
    if latest:
        item.asset.current_price = Decimal(str(latest.price)) * current_rate
        item.asset.last_updated = latest.timestamp
    else:
        item.asset.current_price = Decimal("0.00")
        item.asset.last_updated = None

    item.current_exchange_rate = current_rate
    return item

@router.delete("/{portfolio_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(portfolio_id: UUID, item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PortfolioItem).filter(PortfolioItem.id == item_id, Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio item not found")

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

    asset_curr = (db_item.asset.currency or "EUR").upper()
    portfolio_curr = (db_item.portfolio.currency or "EUR").upper()
    current_rate = float(asset_service.get_exchange_rate(asset_curr, portfolio_curr))

    if sell_in.sale_price is not None:
        final_sale_price_asset_curr = float(sell_in.sale_price) / current_rate
    else:
        latest = db_item.asset.latest_price_record
        if not latest:
            raise HTTPException(status_code=400, detail="Kein Marktpreis verfügbar.")
        final_sale_price_asset_curr = float(latest.price)

    # Da wir nun in Portfoliowährung einkaufen, müssen wir avg_cost_price
    # für den Transaktions-Log (Asset-Währung) kurz zurückrechnen
    avg_cost_asset_curr = float(db_item.avg_cost_price) / float(db_item.avg_exchange_rate or current_rate)
    pnl_in_asset_curr = (final_sale_price_asset_curr - avg_cost_asset_curr) * float(sell_in.quantity)

    new_transaction = Transaction(
        portfolio_id=portfolio_id,
        asset_id=db_item.asset_id,
        type="SELL",
        quantity=sell_in.quantity,
        price_per_unit=final_sale_price_asset_curr,
        fees=0.0,
        total_amount=float(sell_in.quantity) * final_sale_price_asset_curr,
        currency=asset_curr,
        exchange_rate=current_rate,
        realized_pnl=pnl_in_asset_curr,
        transaction_date=sell_in.sale_date.astimezone(timezone.utc) if sell_in.sale_date else datetime.now(timezone.utc) # UTC-Fix
    )
    db.add(new_transaction)

    new_quantity = float(db_item.quantity) - float(sell_in.quantity)

    if new_quantity <= 0:
        db.delete(db_item)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    db_item.quantity = new_quantity
    db.commit()
    db.refresh(db_item)

    return db_item