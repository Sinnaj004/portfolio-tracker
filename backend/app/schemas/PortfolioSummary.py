from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import List, Optional


class PortfolioSummary(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    currency: str
    total_value: Decimal        # Aktueller Marktwert in Portfolio-Währung
    total_invested: Decimal     # Summe der Einstandskosten in Portfolio-Währung
    profit_loss_abs: Decimal    # Gewinn/Verlust absolut
    profit_loss_pct: Decimal    # Gewinn/Verlust in Prozent
    item_count: int

    class Config:
        from_attributes = True