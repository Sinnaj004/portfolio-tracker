from pydantic import BaseModel, ConfigDict, Field, model_validator
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional


# Hilfsschema für die Anzeige von Asset-Details im Item
class AssetShort(BaseModel):
    id: UUID
    symbol: Optional[str] = None
    name: str
    isin: Optional[str] = None
    asset_type: str
    current_price: Optional[Decimal] = None
    last_api_update: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Gemeinsame Felder
class PortfolioItemBase(BaseModel):
    quantity: Decimal = Field(..., gt=0, description="Menge muss größer als 0 sein")
    avg_cost_price: Optional[Decimal] = Field(None, ge=0)


# Schema für den POST-Request (Eingabe)
class PortfolioItemCreate(PortfolioItemBase):
    # Identifikatoren - alle optional, aber einer muss kommen
    symbol: Optional[str] = None
    isin: Optional[str] = None

    @model_validator(mode='after')
    def validate_identifiers(self) -> 'PortfolioItemCreate':
        if not any([self.symbol, self.isin]):
            raise ValueError('Mindestens Ticker oder ISIN  muss angegeben werden.')
        return self


# Schema für die API-Antwort (Ausgabe)
class PortfolioItemOut(PortfolioItemBase):
    id: UUID
    portfolio_id: UUID
    asset_id: UUID

    # Hier betten wir die Asset-Details ein (sehr praktisch fürs Frontend!)
    asset: AssetShort

    model_config = ConfigDict(from_attributes=True)

class PortfolioItemSell(BaseModel):
    quantity: Decimal = Field(..., gt=0, decimal_places=4)

    class Config:
        coerce_numbers_to_str = True