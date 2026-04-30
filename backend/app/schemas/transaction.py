from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TransactionBase(BaseModel):
    type: str  # BUY, SELL, DIVIDEND
    quantity: Decimal
    price_per_unit: Decimal
    fees: Decimal = Decimal("0.0")
    total_amount: Decimal
    currency: str
    exchange_rate: Decimal
    transaction_date: datetime
    realized_pnl: Optional[Decimal] = None


class TransactionOut(TransactionBase):
    id: UUID
    portfolio_id: UUID
    asset_id: UUID

    # Diese Felder kommen via JOIN aus der Asset-Tabelle
    asset_name: Optional[str] = None
    asset_symbol: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)