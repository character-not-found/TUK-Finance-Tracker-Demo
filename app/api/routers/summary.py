# app/api/routers/summary.py
from fastapi import APIRouter, Query as FastAPIQuery, Depends
from typing import Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from app import database
from app.database import get_db
from app.models import CostFrequency, CashOnHand

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/summary",
    tags=["Summaries"],
)

@router.get("/monthly", summary="Get monthly expenses, income, and net profit/loss")
async def get_monthly_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    month: int = FastAPIQuery(default=datetime.now().month, description="Month for the summary (1-12)"),
    db: Session = Depends(get_db)
) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss for a given month.
    """
    logger.info(f"Request for monthly summary for {year}-{month:02d}.")
    summary = database.get_monthly_summary(db, year, month)
    logger.info(f"Successfully generated monthly summary for {year}-{month:02d}.")
    return summary

@router.get("/expense-categories", summary="Get monthly expenses by category")
async def get_expense_categories_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    month: int = FastAPIQuery(default=datetime.now().month, description="Month for the summary (1-12)"),
    db: Session = Depends(get_db)
) -> Dict[str, float]:
    """
    Retrieves a summary of expenses grouped by category for a given month.
    """
    logger.info(f"Request for expense categories summary for {year}-{month:02d}.")
    summary = database.get_expense_categories_summary(db, year, month)
    logger.info(f"Successfully generated expense categories summary for {year}-{month:02d}.")
    return summary

@router.get("/income-sources", summary="Get monthly income by source")
async def get_income_sources_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    month: int = FastAPIQuery(default=datetime.now().month, description="Month for the summary (1-12)"),
    db: Session = Depends(get_db)
) -> Dict[str, float]:
    """
    Retrieves a summary of income grouped by source (Tours, Transfers) for a given month.
    """
    logger.info(f"Request for income sources summary for {year}-{month:02d}.")
    summary = database.get_income_sources_summary(db, year, month)
    logger.info(f"Successfully generated income sources summary for {year}-{month:02d}.")
    return summary

@router.get("/yearly", summary="Get yearly expenses, income, and net profit/loss")
async def get_yearly_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    db: Session = Depends(get_db)
) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss for a given year.
    """
    logger.info(f"Request for yearly summary for {year}.")
    summary = database.get_yearly_summary(db, year)
    logger.info(f"Successfully generated yearly summary for {year}.")
    return summary

@router.get("/global", summary="Get global expenses, income, and net profit/loss")
async def get_global_summary_api(db: Session = Depends(get_db)) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss across all records.
    """
    logger.info("Request for global summary.")
    summary = database.get_global_summary(db)
    logger.info("Successfully generated global summary.")
    return summary

@router.get("/cash-on-hand", response_model=CashOnHand, summary="Get current cash on hand balance")
async def get_cash_on_hand_api(db: Session = Depends(get_db)):
    """
    Retrieves the current cash on hand balance.
    """
    logger.info("Request for cash on hand balance.")
    balance = database.get_cash_on_hand_balance(db)
    logger.info(f"Successfully retrieved cash on hand balance: {balance.balance:.2f}")
    return balance
