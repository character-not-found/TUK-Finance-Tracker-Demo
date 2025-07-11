# app/database.py
# Refactored to use SQLAlchemy for a relational database (e.g., PostgreSQL or SQLite)

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict # Still useful for summaries
import logging

# Import your Pydantic models and settings
from .models import FixedCost, DailyExpense, Income, CostFrequency, ExpenseCategory, CashOnHand, PaymentMethod
from app.config import settings # Import settings

logger = logging.getLogger(__name__)

# Use the DATABASE_URL from settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite with FastAPI
# For PostgreSQL, you might use 'pool_pre_ping=True'
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # For PostgreSQL, ensure you have psycopg2-binary installed
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# --- SQLAlchemy Models (Mirroring your Pydantic models) ---
# These define the table structure in your SQL database
class DBCashOnHand(Base):
    __tablename__ = "cash_on_hand"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.now)

class DBFixedCost(Base):
    __tablename__ = "fixed_costs"
    id = Column(Integer, primary_key=True, index=True)
    amount_eur = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    cost_frequency = Column(SQLEnum(CostFrequency), nullable=False) # Store Enum value
    category = Column(SQLEnum(ExpenseCategory), nullable=False)     # Store Enum value
    recipient = Column(String, nullable=True)
    cost_date = Column(String, nullable=False) # Storing as string YYYY-MM-DD
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False) # Store Enum value
    timestamp = Column(DateTime, default=datetime.now)

class DBDailyExpense(Base):
    __tablename__ = "daily_expenses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category = Column(SQLEnum(ExpenseCategory), nullable=False) # Store Enum value
    cost_date = Column(String, nullable=False) # Storing as string YYYY-MM-DD
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False) # Store Enum value
    timestamp = Column(DateTime, default=datetime.now)

class DBIncome(Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True, index=True)
    income_date = Column(String, nullable=False) # Storing as string YYYY-MM-DD
    tours_revenue_eur = Column(Float, nullable=False)
    transfers_revenue_eur = Column(Float, nullable=False)
    hours_worked = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

# --- Database Dependency for FastAPI ---
# This function yields a database session that FastAPI can use.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Functions for managing Cash On Hand (Rewritten for SQLAlchemy) ---
def get_cash_on_hand_balance(db_session: Session) -> CashOnHand:
    balance_entry = db_session.query(DBCashOnHand).first()
    if not balance_entry:
        # Initialize with 0.0 if no entry exists
        initial_balance_data = DBCashOnHand(balance=0.0, last_updated=datetime.now())
        db_session.add(initial_balance_data)
        db_session.commit()
        db_session.refresh(initial_balance_data)
        logger.info("Initialized cash on hand balance to 0.0.")
        return CashOnHand(doc_id=initial_balance_data.id, **initial_balance_data.__dict__)
    logger.debug(f"Retrieved cash on hand balance: {balance_entry.balance}")
    return CashOnHand(doc_id=balance_entry.id, **balance_entry.__dict__)

def update_cash_on_hand_balance(db_session: Session, amount: float):
    current_balance_entry = get_cash_on_hand_balance(db_session)
    new_balance = current_balance_entry.balance + amount
    db_session.query(DBCashOnHand).filter(DBCashOnHand.id == current_balance_entry.doc_id).update(
        {'balance': round(new_balance, 2), 'last_updated': datetime.now()}
    )
    db_session.commit()
    logger.info(f"Cash on hand updated by {amount:.2f}. New balance: {new_balance:.2f}")

def set_initial_cash_on_hand(db_session: Session, initial_balance: float) -> CashOnHand:
    db_session.query(DBCashOnHand).delete() # Clear existing entries
    db_session.commit()
    initial_balance_data = DBCashOnHand(balance=round(initial_balance, 2), last_updated=datetime.now())
    db_session.add(initial_balance_data)
    db_session.commit()
    db_session.refresh(initial_balance_data)
    logger.info(f"Initial cash on hand balance set to {initial_balance:.2f}.")
    return CashOnHand(doc_id=initial_balance_data.id, **initial_balance_data.__dict__)

# --- Functions for managing Fixed Costs (Rewritten for SQLAlchemy) ---
def add_fixed_cost(db_session: Session, cost: FixedCost) -> FixedCost:
    # Convert Pydantic model to SQLAlchemy model
    db_cost = DBFixedCost(
        amount_eur=cost.amount_eur,
        description=cost.description,
        cost_frequency=cost.cost_frequency, # Enums are handled by SQLEnum
        category=cost.category,
        recipient=cost.recipient,
        cost_date=cost.cost_date,
        payment_method=cost.payment_method, # Enums are handled by SQLEnum
        timestamp=datetime.now()
    )
    db_session.add(db_cost)
    db_session.commit()
    db_session.refresh(db_cost) # Refresh to get the auto-generated ID
    logger.info(f"Added fixed cost: {cost.description} with ID {db_cost.id}")
    if cost.payment_method == PaymentMethod.CASH:
        update_cash_on_hand_balance(db_session, -cost.amount_eur)
        logger.info(f"Cash on hand decreased by {cost.amount_eur:.2f} for fixed cost (cash payment).")
    return FixedCost(doc_id=db_cost.id, **db_cost.__dict__)

def get_all_fixed_costs(db_session: Session) -> List[FixedCost]:
    costs = db_session.query(DBFixedCost).all()
    logger.info(f"Retrieved {len(costs)} fixed costs.")
    return [FixedCost(doc_id=cost.id, **cost.__dict__) for cost in costs]

def get_fixed_cost_by_id(db_session: Session, doc_id: int) -> Optional[FixedCost]:
    cost = db_session.query(DBFixedCost).filter(DBFixedCost.id == doc_id).first()
    if cost:
        logger.info(f"Retrieved fixed cost with ID: {doc_id}")
        return FixedCost(doc_id=cost.id, **cost.__dict__)
    logger.warning(f"Fixed cost with ID {doc_id} not found.")
    return None

def update_fixed_cost(db_session: Session, doc_id: int, updates: Dict[str, Any]) -> bool:
    old_cost = get_fixed_cost_by_id(db_session, doc_id)
    if not old_cost:
        logger.warning(f"Fixed cost with ID {doc_id} not found for update.")
        return False

    old_amount = old_cost.amount_eur
    old_payment_method = old_cost.payment_method

    # Convert incoming string values to Enum members for SQLAlchemy update
    if 'cost_frequency' in updates and isinstance(updates['cost_frequency'], str):
        updates['cost_frequency'] = CostFrequency(updates['cost_frequency'])
    if 'category' in updates and isinstance(updates['category'], str):
        updates['category'] = ExpenseCategory(updates['category'])
    if 'payment_method' in updates and isinstance(updates['payment_method'], str):
        updates['payment_method'] = PaymentMethod(updates['payment_method'])

    updates['timestamp'] = datetime.now()

    updated_count = db_session.query(DBFixedCost).filter(DBFixedCost.id == doc_id).update(updates)
    db_session.commit()

    if updated_count:
        logger.info(f"Updated fixed cost with ID {doc_id}. Changes: {updates}")
        new_cost = get_fixed_cost_by_id(db_session, doc_id) # Fetch updated cost to get new amount/method
        new_amount = new_cost.amount_eur
        new_payment_method = new_cost.payment_method

        if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, old_amount)
            logger.info(f"Fixed cost {doc_id} changed from cash to {new_payment_method.value}. Added {old_amount:.2f} back to cash.")
        elif old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, -new_amount)
            logger.info(f"Fixed cost {doc_id} changed from {old_payment_method.value} to cash. Subtracted {new_amount:.2f} from cash.")
        elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
            amount_difference = old_amount - new_amount
            update_cash_on_hand_balance(db_session, amount_difference)
            logger.info(f"Fixed cost {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
        else:
            logger.info(f"Fixed cost {doc_id} payment method not cash, cash on hand not affected by update.")
        return True
    logger.warning(f"Fixed cost with ID {doc_id} not found for update.")
    return False

def delete_fixed_cost(db_session: Session, doc_id: int) -> bool:
    cost_to_delete = get_fixed_cost_by_id(db_session, doc_id)
    if not cost_to_delete:
        logger.warning(f"Fixed cost with ID {doc_id} not found for deletion.")
        return False

    deleted_count = db_session.query(DBFixedCost).filter(DBFixedCost.id == doc_id).delete()
    db_session.commit()

    if deleted_count:
        logger.info(f"Deleted fixed cost with ID {doc_id}.")
        if cost_to_delete.payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, cost_to_delete.amount_eur)
            logger.info(f"Cash on hand increased by {cost_to_delete.amount_eur:.2f} due to deletion of cash-paid fixed cost.")
        return True
    logger.warning(f"Fixed cost with ID {doc_id} not found for deletion.")
    return False

# --- Functions for managing Daily Expenses (Rewritten for SQLAlchemy) ---
def add_daily_expense(db_session: Session, expense: DailyExpense) -> DailyExpense:
    db_expense = DBDailyExpense(
        amount=expense.amount,
        description=expense.description,
        category=expense.category,
        cost_date=expense.cost_date,
        payment_method=expense.payment_method,
        timestamp=datetime.now()
    )
    db_session.add(db_expense)
    db_session.commit()
    db_session.refresh(db_expense)
    logger.info(f"Added daily expense: {expense.description} with ID {db_expense.id}")
    if expense.payment_method == PaymentMethod.CASH:
        update_cash_on_hand_balance(db_session, -expense.amount)
        logger.info(f"Cash on hand decreased by {expense.amount:.2f} for daily expense (cash payment).")
    return DailyExpense(doc_id=db_expense.id, **db_expense.__dict__)

def get_all_daily_expenses(db_session: Session) -> List[DailyExpense]:
    expenses = db_session.query(DBDailyExpense).all()
    logger.info(f"Retrieved {len(expenses)} daily expenses.")
    return [DailyExpense(doc_id=expense.id, **expense.__dict__) for expense in expenses]

def get_daily_expense_by_id(db_session: Session, doc_id: int) -> Optional[DailyExpense]:
    expense = db_session.query(DBDailyExpense).filter(DBDailyExpense.id == doc_id).first()
    if expense:
        logger.info(f"Retrieved daily expense with ID: {doc_id}")
        return DailyExpense(doc_id=expense.id, **expense.__dict__)
    logger.warning(f"Daily expense with ID {doc_id} not found.")
    return None

def update_daily_expense(db_session: Session, doc_id: int, updates: Dict[str, Any]) -> bool:
    old_expense = get_daily_expense_by_id(db_session, doc_id)
    if not old_expense:
        logger.warning(f"Daily expense with ID {doc_id} not found for update.")
        return False

    old_amount = old_expense.amount
    old_payment_method = old_expense.payment_method

    if 'category' in updates and isinstance(updates['category'], str):
        updates['category'] = ExpenseCategory(updates['category'])
    if 'payment_method' in updates and isinstance(updates['payment_method'], str):
        updates['payment_method'] = PaymentMethod(updates['payment_method'])

    updates['timestamp'] = datetime.now()

    updated_count = db_session.query(DBDailyExpense).filter(DBDailyExpense.id == doc_id).update(updates)
    db_session.commit()

    if updated_count:
        logger.info(f"Updated daily expense with ID {doc_id}. Changes: {updates}")
        new_expense = get_daily_expense_by_id(db_session, doc_id)
        new_amount = new_expense.amount
        new_payment_method = new_expense.payment_method

        if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, old_amount)
            logger.info(f"Daily expense {doc_id} changed from cash to {new_payment_method.value}. Added {old_amount:.2f} back to cash.")
        elif old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, -new_amount)
            logger.info(f"Daily expense {doc_id} changed from {old_payment_method.value} to cash. Subtracted {new_amount:.2f} from cash.")
        elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
            amount_difference = old_amount - new_amount
            update_cash_on_hand_balance(db_session, amount_difference)
            logger.info(f"Daily expense {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
        else:
            logger.info(f"Daily expense {doc_id} payment method not cash, cash on hand not affected by update.")
        return True
    logger.warning(f"Daily expense with ID {doc_id} not found for update.")
    return False

def delete_daily_expense(db_session: Session, doc_id: int) -> bool:
    expense_to_delete = get_daily_expense_by_id(db_session, doc_id)
    if not expense_to_delete:
        logger.warning(f"Daily expense with ID {doc_id} not found for deletion.")
        return False

    deleted_count = db_session.query(DBDailyExpense).filter(DBDailyExpense.id == doc_id).delete()
    db_session.commit()

    if deleted_count:
        logger.info(f"Deleted daily expense with ID {doc_id}.")
        if expense_to_delete.payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(db_session, expense_to_delete.amount)
            logger.info(f"Cash on hand increased by {expense_to_delete.amount:.2f} due to deletion of cash-paid daily expense.")
        return True
    logger.warning(f"Daily expense with ID {doc_id} not found for deletion.")
    return False

# --- Functions for managing Income (Rewritten for SQLAlchemy) ---
def add_income(db_session: Session, income: Income) -> Income:
    db_income = DBIncome(
        income_date=income.income_date,
        tours_revenue_eur=income.tours_revenue_eur,
        transfers_revenue_eur=income.transfers_revenue_eur,
        hours_worked=income.hours_worked,
        timestamp=datetime.now()
    )
    db_session.add(db_income)
    db_session.commit()
    db_session.refresh(db_income)
    logger.info(f"Added income entry: {income.income_date} with ID {db_income.id}")
    total_income_amount = income.tours_revenue_eur + income.transfers_revenue_eur
    update_cash_on_hand_balance(db_session, total_income_amount)
    logger.info(f"Cash on hand increased by {total_income_amount:.2f} for income.")
    return Income(doc_id=db_income.id, **db_income.__dict__)

def get_all_income(db_session: Session) -> List[Income]:
    incomes = db_session.query(DBIncome).all()
    logger.info(f"Retrieved {len(incomes)} income entries.")
    return [Income(doc_id=income.id, **income.__dict__) for income in incomes]

def get_income_by_id(db_session: Session, doc_id: int) -> Optional[Income]:
    income = db_session.query(DBIncome).filter(DBIncome.id == doc_id).first()
    if income:
        logger.info(f"Retrieved income entry with ID: {doc_id}")
        return Income(doc_id=income.id, **income.__dict__)
    logger.warning(f"Income entry with ID {doc_id} not found.")
    return None

def update_income(db_session: Session, doc_id: int, updates: Dict[str, Any]) -> bool:
    old_income = get_income_by_id(db_session, doc_id)
    if not old_income:
        logger.warning(f"Income entry with ID {doc_id} not found for update.")
        return False

    old_total_income = old_income.tours_revenue_eur + old_income.transfers_revenue_eur

    updates['timestamp'] = datetime.now()

    updated_count = db_session.query(DBIncome).filter(DBIncome.id == doc_id).update(updates)
    db_session.commit()

    if updated_count:
        logger.info(f"Updated income entry with ID {doc_id}. Changes: {updates}")
        new_income = get_income_by_id(db_session, doc_id)
        new_total_income = new_income.tours_revenue_eur + new_income.transfers_revenue_eur
        amount_difference = new_total_income - old_total_income
        update_cash_on_hand_balance(db_session, amount_difference)
        logger.info(f"Income {doc_id} amount changed. Adjusted cash by {amount_difference:.2f}.")
        return True
    logger.warning(f"Income entry with ID {doc_id} not found for update.")
    return False

def delete_income(db_session: Session, doc_id: int) -> bool:
    income_to_delete = get_income_by_id(db_session, doc_id)
    if not income_to_delete:
        logger.warning(f"Income entry with ID {doc_id} not found for deletion.")
        return False

    deleted_count = db_session.query(DBIncome).filter(DBIncome.id == doc_id).delete()
    db_session.commit()

    if deleted_count:
        logger.info(f"Deleted income entry with ID {doc_id}.")
        total_income_amount = income_to_delete.tours_revenue_eur + income_to_delete.transfers_revenue_eur
        update_cash_on_hand_balance(db_session, -total_income_amount)
        logger.info(f"Cash on hand decreased by {total_income_amount:.2f} due to deletion of income.")
        return True
    logger.warning(f"Income entry with ID {doc_id} not found for deletion.")
    return False

# --- Functions for clearing all data (for development/testing) ---
def clear_all_data(db_session: Session):
    """
    Clears all data from all tables, including cash on hand. Use with caution!
    """
    db_session.query(DBFixedCost).delete()
    db_session.query(DBDailyExpense).delete()
    db_session.query(DBIncome).delete()
    db_session.query(DBCashOnHand).delete()
    db_session.commit()
    set_initial_cash_on_hand(db_session, 0.0) # Re-initialize cash on hand to 0 after clearing
    logger.info("All database tables truncated and cash on hand reset to 0.0 successfully.")

# --- Functions for Summaries (Rewritten for SQLAlchemy) ---
from sqlalchemy import func, and_

def get_daily_expenses_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[DailyExpense]:
    expenses = db_session.query(DBDailyExpense).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(expenses)} daily expenses between {start_date} and {end_date}.")
    return [DailyExpense(doc_id=exp.id, **exp.__dict__) for exp in expenses]

def get_fixed_costs_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[FixedCost]:
    costs = db_session.query(DBFixedCost).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(costs)} fixed costs between {start_date} and {end_date}.")
    return [FixedCost(doc_id=cost.id, **cost.__dict__) for cost in costs]

def get_income_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[Income]:
    incomes = db_session.query(DBIncome).filter(
        and_(DBIncome.income_date >= start_date, DBIncome.income_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(incomes)} income entries between {start_date} and {end_date}.")
    return [Income(doc_id=inc.id, **inc.__dict__) for inc in incomes]

def get_monthly_summary(db_session: Session, year: int, month: int) -> Dict[str, float]:
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    total_monthly_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date)
    ).scalar() or 0.0

    total_monthly_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date)
    ).scalar() or 0.0

    total_monthly_expenses = total_monthly_daily_expenses + total_monthly_fixed_costs

    income_results = db_session.query(
        func.sum(DBIncome.tours_revenue_eur),
        func.sum(DBIncome.transfers_revenue_eur)
    ).filter(
        and_(DBIncome.income_date >= start_date, DBIncome.income_date <= end_date)
    ).first()

    total_monthly_income = (income_results[0] or 0.0) + (income_results[1] or 0.0)

    net_monthly_profit = total_monthly_income - total_monthly_expenses

    summary = {
        "total_monthly_expenses": round(total_monthly_expenses, 2),
        "total_monthly_income": round(total_monthly_income, 2),
        "net_monthly_profit": round(net_monthly_profit, 2)
    }
    logger.info(f"Generated monthly summary for {year}-{month:02d}: {summary}")
    return summary

def get_expense_categories_summary(db_session: Session, year: int, month: int) -> Dict[str, float]:
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    category_totals = defaultdict(float)

    daily_expenses = db_session.query(DBDailyExpense).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date)
    ).all()
    for expense in daily_expenses:
        category_totals[expense.category.value] += expense.amount

    fixed_costs = db_session.query(DBFixedCost).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date)
    ).all()
    for cost in fixed_costs:
        category_totals[cost.category.value] += cost.amount_eur

    summary = {category: round(total, 2) for category, total in category_totals.items()}
    logger.info(f"Generated expense categories summary for {year}-{month:02d}: {summary}")
    return summary

def get_income_sources_summary(db_session: Session, year: int, month: int) -> Dict[str, float]:
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    source_totals = defaultdict(float)
    income_entries = db_session.query(DBIncome).filter(
        and_(DBIncome.income_date >= start_date, DBIncome.income_date <= end_date)
    ).all()

    for income in income_entries:
        source_totals['Tours'] += income.tours_revenue_eur
        source_totals['Transfers'] += income.transfers_revenue_eur

    summary = {source: round(total, 2) for source, total in source_totals.items()}
    logger.info(f"Generated income sources summary for {year}-{month:02d}: {summary}")
    return summary

def get_yearly_summary(db_session: Session, year: int) -> Dict[str, float]:
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    total_yearly_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date)
    ).scalar() or 0.0

    total_yearly_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date)
    ).scalar() or 0.0

    total_yearly_expenses = total_yearly_daily_expenses + total_yearly_fixed_costs

    income_results = db_session.query(
        func.sum(DBIncome.tours_revenue_eur),
        func.sum(DBIncome.transfers_revenue_eur)
    ).filter(
        and_(DBIncome.income_date >= start_date, DBIncome.income_date <= end_date)
    ).first()

    total_yearly_income = (income_results[0] or 0.0) + (income_results[1] or 0.0)

    net_yearly_profit = total_yearly_income - total_yearly_expenses

    summary = {
        "total_yearly_expenses": round(total_yearly_expenses, 2),
        "total_yearly_income": round(total_yearly_income, 2),
        "net_yearly_profit": round(net_yearly_profit, 2)
    }
    logger.info(f"Generated yearly summary for {year}: {summary}")
    return summary

def get_global_summary(db_session: Session) -> Dict[str, float]:
    total_global_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).scalar() or 0.0
    total_global_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).scalar() or 0.0
    total_global_expenses = total_global_daily_expenses + total_global_fixed_costs

    income_results = db_session.query(
        func.sum(DBIncome.tours_revenue_eur),
        func.sum(DBIncome.transfers_revenue_eur)
    ).first()

    total_global_income = (income_results[0] or 0.0) + (income_results[1] or 0.0)
    net_global_profit = total_global_income - total_global_expenses

    summary = {
        "total_global_expenses": round(total_global_expenses, 2),
        "total_global_income": round(total_global_income, 2),
        "net_global_profit": round(net_global_profit, 2)
    }
    logger.info(f"Generated global summary: {summary}")
    return summary

# Function to create all tables (call this on app startup or migration)
def create_all_tables(engine_param=None): # Added engine_param for flexibility
    # Use the module-level engine if no specific engine is passed
    target_engine = engine_param if engine_param else engine
    Base.metadata.create_all(bind=target_engine)
    logger.info("All database tables created successfully (if they didn't exist).")

