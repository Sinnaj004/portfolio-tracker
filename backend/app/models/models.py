from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Numeric, Integer
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
    preferred_curency = Column(String, default="EUR")
    created_at = Column(DateTime, default=datetime.now)

    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    owner = relationship("User", back_populates="portfolios")
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(String) # e.g., "stock", "crypto"
    isin = Column(String, nullable=True)
    currency = Column(String, default="USD")
    last_api_update = Column(DateTime, nullable=True)

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    quantity = Column(Numeric(precision=18, scale=8), nullable=False) # Präzise für Krypto
    avg_cost_price = Column(Numeric(precision=18, scale=4))

    portfolio = relationship("Portfolio", back_populates="items")
    asset = relationship("Asset")


class Transaction(Base):
    """Logbuch aller Käufe, Verkäufe und Dividenden."""
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)

    # Typ: "BUY", "SELL", "DIVIDEND"
    type = Column(String, nullable=False)
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    price_per_unit = Column(Numeric(precision=18, scale=4), nullable=False)
    fees = Column(Numeric(precision=18, scale=4), default=0.0)
    currency = Column(String, default="EUR")
    transaction_date = Column(DateTime, default=datetime.now)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset")


class AssetPrice(Base):
    """
    Speichert historische Preise.
    Hinweis: Diese Tabelle wird in TimescaleDB später als 'Hypertable' markiert.
    """
    __tablename__ = "asset_prices"
    timestamp = Column(DateTime, primary_key=True, default=datetime.now)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), primary_key=True)
    price = Column(Numeric(precision=18, scale=4), nullable=False)
    volume = Column(Numeric(precision=18, scale=2), nullable=True)

    asset = relationship("Asset")