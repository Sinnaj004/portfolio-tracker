from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.models import Portfolio, User
from app.schemas.portfolio import PortfolioCreate, PortfolioOut
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id, Portfolio.name == portfolio.name).first()

    if existing_portfolio:
        raise HTTPException(status_code=400, detail="Portfolioname already exists")

    new_portfolio = Portfolio(name=portfolio.name, user_id=current_user.id, description=portfolio.description, currency=portfolio.currency)
    db.add(new_portfolio)

    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio

@router.get("/", response_model=List[PortfolioOut], status_code=status.HTTP_200_OK)
def get_all_portfolios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()

@router.get("/{id}", response_model=PortfolioOut, status_code=status.HTTP_200_OK)
def get_specified_portfolio(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == id, Portfolio.user_id == current_user.id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return portfolio

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == id, Portfolio.user_id == current_user.id).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    db.delete(portfolio)
    db.commit()