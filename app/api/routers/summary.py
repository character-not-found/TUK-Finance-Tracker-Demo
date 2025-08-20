# app/api/routers/summary.py
from fastapi import APIRouter, Query as FastAPIQuery, Depends
from typing import Dict
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app import database
from app.database import get_db
from app.models import CashOnHand
from app.api.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/summary",
    tags=["Summaries"],
)

@router.get("/monthly", summary="Get monthly expenses, income, and net profit/loss")
async def get_monthly_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    month: int = FastAPIQuery(default=datetime.now().month, description="Month for the summary (1-12)"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves a summary of income grouped by source (Tours, Transfers) for a given month.
    """
    logger.info(f"Request for income sources summary for {year}-{month:02d}.")
    summary = database.get_income_sources_summary(db, year, month)
    logger.info(f"Successfully generated income sources summary for {year}-{month:02d}.")
    return summary

@router.get("/weekly", summary="Get weekly expenses, income, and net profit/loss")
async def get_weekly_summary_api(
    start_date: str = FastAPIQuery(description="Start date for the summary (YYYY-MM-DD)"),
    end_date: str = FastAPIQuery(description="End date for the summary (YYYY-MM-DD)"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss for a given week.
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    logger.info(f"Request for weekly summary for {start_date} to {end_date}.")
    summary = database.get_weekly_summary(db, start_date_obj, end_date_obj)
    logger.info(f"Successfully generated weekly summary for {start_date} to {end_date}.")
    return summary

@router.get("/weekly-expense-categories", summary="Get weekly expenses by category")
async def get_weekly_expense_categories_summary_api(
    start_date: str = FastAPIQuery(description="Start date for the summary (YYYY-MM-DD)"),
    end_date: str = FastAPIQuery(description="End date for the summary (YYYY-MM-DD)"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves a summary of expenses grouped by category for a given week.
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    logger.info(f"Request for weekly expense categories summary for {start_date} to {end_date}.")
    summary = database.get_weekly_expense_categories_summary(db, start_date_obj, end_date_obj)
    logger.info(f"Successfully generated weekly expense categories summary for {start_date} to {end_date}.")
    return summary

@router.get("/weekly-income-sources", summary="Get weekly income by source")
async def get_weekly_income_sources_summary_api(
    start_date: str = FastAPIQuery(description="Start date for the summary (YYYY-MM-DD)"),
    end_date: str = FastAPIQuery(description="End date for the summary (YYYY-MM-DD)"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves a summary of income by source for a given week.
    """
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    logger.info(f"Request for weekly income sources summary for {start_date} to {end_date}.")
    summary = database.get_weekly_income_sources_summary(db, start_date_obj, end_date_obj)
    logger.info(f"Successfully generated weekly income sources summary for {start_date} to {end_date}.")
    return summary

@router.get("/yearly", summary="Get yearly expenses, income, and net profit/loss")
async def get_yearly_summary_api(
    year: int = FastAPIQuery(default=datetime.now().year, description="Year for the summary"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss for a given year.
    """
    logger.info(f"Request for yearly summary for {year}.")
    summary = database.get_yearly_summary(db, year)
    logger.info(f"Successfully generated yearly summary for {year}.")
    return summary

@router.get("/global", summary="Get global expenses, income, and net profit/loss")
async def get_global_summary_api(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss across all records.
    """
    logger.info("Request for global summary.")
    summary = database.get_global_summary(db)
    logger.info("Successfully generated global summary.")
    return summary

@router.get("/cash-on-hand", response_model=CashOnHand, summary="Get current cash on hand balance")
async def get_cash_on_hand_api(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieves the current cash on hand balance.
    """
    logger.info("Request for cash on hand balance.")
    balance = database.get_cash_on_hand_balance(db)
    logger.info(f"Successfully retrieved cash on hand balance: {balance.balance:.2f}")
    return balance

@router.get("/daily-income-average", summary="Get daily average income for a given date range (considering days with income)")
async def get_daily_income_average_api(
    start_date: datetime = FastAPIQuery(..., description="Start date for the period (YYYY-MM-DD)"),
    end_date: datetime = FastAPIQuery(..., description="End date for the period (YYYY-MM-DD)"),
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Retrieves the daily average income for a specified date range,
    only counting days where income was recorded.
    """
    logger.info(f"Request for daily income average from {start_date.date()} to {end_date.date()}.")
    average_income = database.get_daily_income_average_for_period(db, start_date, end_date)
    logger.info(f"Successfully generated daily income average: {average_income}.")
    return {"daily_average_income": average_income}