from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class Portfolio(BaseModel):
    name: str
    currency: str = "EUR"
    description: Optional[str] = None


class PortfolioCreate(Portfolio):
    pass

class PortfolioOut(Portfolio):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
