from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Numeric, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now())

    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    currency = Column(String, default="EUR")
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="portfolios")
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('user_id', 'name', name='_user_portfolio_name_uc'),)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(String) # e.g., "stock", "crypto"
    isin = Column(String, unique=True, index=True, nullable=True)
    currency = Column(String, default="USD")
    last_api_update = Column(DateTime, nullable=True)

    prices = relationship("AssetPrice", back_populates="asset", cascade="all, delete-orphan")

    @property
    def latest_price_record(self):
        """Gibt das neueste AssetPrice-Objekt aus der Historie zurück."""
        if not self.prices:
            return None
        # Sortiert die Liste der Preise nach Timestamp absteigend
        return sorted(self.prices, key=lambda p: p.timestamp, reverse=True)[0]


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    quantity = Column(Numeric(precision=18, scale=8), nullable=False) # Präzise für Krypto
    avg_cost_price = Column(Numeric(precision=18, scale=4))
    avg_exchange_rate = Column(Numeric(precision=18, scale=8))

    portfolio = relationship("Portfolio", back_populates="items")
    asset = relationship("Asset")



class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)

    type = Column(String, nullable=False)  # "BUY", "SELL", "DIVIDEND"
    quantity = Column(Numeric(18, 8), nullable=False)
    price_per_unit = Column(Numeric(18, 4), nullable=False)
    fees = Column(Numeric(18, 4), default=0.0)
    total_amount = Column(Numeric(18, 4))  # (quantity * price_per_unit) + fees (oder - fees bei Verkauf)
    currency = Column(String, default="EUR")
    exchange_rate = Column(Numeric(18, 6), default=1.0)
    transaction_date = Column(DateTime, default=datetime.now)

    # Optional aber nützlich für Statistiken:
    realized_pnl = Column(Numeric(18, 4), nullable=True)  # Nur für SELL

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset")



class AssetPrice(Base):
    __tablename__ = "asset_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(16, 8), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True) # Index für schnelle Zeit-Abfragen

    asset = relationship("Asset", back_populates="prices")