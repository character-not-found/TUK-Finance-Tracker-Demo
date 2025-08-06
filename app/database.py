# app/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum, func, and_, not_, distinct, cast, Date
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging

from .models import FixedCost, DailyExpense, Income, CostFrequency, ExpenseCategory, CashOnHand, PaymentMethod, AggregatedIncome
from app.config import settings

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
    cost_frequency = Column(SQLEnum(CostFrequency), nullable=False)
    category = Column(SQLEnum(ExpenseCategory), nullable=False)
    recipient = Column(String, nullable=True)
    cost_date = Column(String, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

class DBDailyExpense(Base):
    __tablename__ = "daily_expenses"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category = Column(SQLEnum(ExpenseCategory), nullable=False)
    cost_date = Column(String, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

class DBIncome(Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True, index=True)
    income_date = Column(String, nullable=False)
    tours_revenue_eur = Column(Float, nullable=False)
    transfers_revenue_eur = Column(Float, nullable=False)
    hours_worked = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Helper function to get the appropriate date column expression based on dialect
def _get_date_column_expression(db_session: Session, column: Column) -> ColumnElement:
    """
    Returns the SQLAlchemy expression for a date column, handling dialect differences.
    """
    if db_session.bind.dialect.name == 'postgresql':
        return cast(column, Date)
    else: # Default to SQLite or other dialects where func.date() works
        return func.date(column)

def get_cash_on_hand_balance(db_session: Session) -> CashOnHand:
    balance_entry = db_session.query(DBCashOnHand).first()
    if not balance_entry:
        initial_balance_data = DBCashOnHand(balance=0.0, last_updated=datetime.now())
        db_session.add(initial_balance_data)
        db_session.commit()
        db_session.refresh(initial_balance_data)
        logger.info("Initialized cash on hand balance to 0.0.")
        # Ensure that the validated model is returned even if it's the newly created one
        return CashOnHand.model_validate(initial_balance_data)
    logger.debug(f"Retrieved cash on hand balance: {balance_entry.balance}")
    return CashOnHand.model_validate(balance_entry)

def update_cash_on_hand_balance(db_session: Session, amount: float):
    current_balance_entry = get_cash_on_hand_balance(db_session)
    new_balance = current_balance_entry.balance + amount
    # Corrected: Use current_balance_entry.doc_id instead of .id
    db_session.query(DBCashOnHand).filter(DBCashOnHand.id == current_balance_entry.doc_id).update(
        {'balance': round(new_balance, 2), 'last_updated': datetime.now()}
    )
    db_session.commit()
    logger.info(f"Cash on hand updated by {amount:.2f}. New balance: {new_balance:.2f}")

def set_initial_cash_on_hand(db_session: Session, initial_balance: float) -> CashOnHand:
    db_session.query(DBCashOnHand).delete()
    db_session.commit()
    initial_balance_data = DBCashOnHand(balance=round(initial_balance, 2), last_updated=datetime.now())
    db_session.add(initial_balance_data)
    db_session.commit()
    db_session.refresh(initial_balance_data)
    logger.info(f"Initial cash on hand balance set to {initial_balance:.2f}.")
    return CashOnHand.model_validate(initial_balance_data)

def add_fixed_cost(db_session: Session, cost: FixedCost) -> FixedCost:
    db_cost = DBFixedCost(
        amount_eur=cost.amount_eur,
        description=cost.description,
        cost_frequency=cost.cost_frequency,
        category=cost.category,
        recipient=cost.recipient,
        cost_date=cost.cost_date,
        payment_method=cost.payment_method,
        timestamp=datetime.now()
    )
    db_session.add(db_cost)
    db_session.commit()
    db_session.refresh(db_cost)
    logger.info(f"Added fixed cost: {cost.description} with ID {db_cost.id}")
    NON_PROFIT_CATEGORIES = {ExpenseCategory.NON_BUSINESS_RELATED, ExpenseCategory.BANK_DEPOSIT}
    if cost.payment_method == PaymentMethod.CASH and cost.category not in NON_PROFIT_CATEGORIES:
        update_cash_on_hand_balance(db_session, -cost.amount_eur)
        logger.info(f"Cash on hand decreased by {cost.amount_eur:.2f} for fixed cost (cash payment, business related).")
    elif cost.payment_method == PaymentMethod.CASH and cost.category in NON_PROFIT_CATEGORIES:
        update_cash_on_hand_balance(db_session, -cost.amount_eur)
        logger.info(f"Cash on hand decreased by {cost.amount_eur:.2f} for fixed cost (cash payment, non-profit related).")
    return FixedCost.model_validate(db_cost)

def get_all_fixed_costs(db_session: Session) -> List[FixedCost]:
    costs = db_session.query(DBFixedCost).all()
    logger.info(f"Retrieved {len(costs)} fixed costs.")
    return [FixedCost.model_validate(cost) for cost in costs]

def get_fixed_cost_by_id(db_session: Session, doc_id: int) -> Optional[FixedCost]:
    cost = db_session.query(DBFixedCost).filter(DBFixedCost.id == doc_id).first()
    if cost:
        logger.info(f"Retrieved fixed cost with ID: {doc_id}")
        return FixedCost.model_validate(cost)
    logger.warning(f"Fixed cost with ID {doc_id} not found.")
    return None

def update_fixed_cost(db_session: Session, doc_id: int, updates: Dict[str, Any]) -> bool:
    old_cost = get_fixed_cost_by_id(db_session, doc_id)
    if not old_cost:
        logger.warning(f"Fixed cost with ID {doc_id} not found for update.")
        return False

    old_amount = old_cost.amount_eur
    old_payment_method = old_cost.payment_method
    old_category = old_cost.category

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
        new_cost = get_fixed_cost_by_id(db_session, doc_id)
        new_amount = new_cost.amount_eur
        new_payment_method = new_cost.payment_method
        new_category = new_cost.category

        NON_PROFIT_CATEGORIES = {
            ExpenseCategory.NON_BUSINESS_RELATED,
            ExpenseCategory.BANK_DEPOSIT
        }

        old_was_non_profit = old_category in NON_PROFIT_CATEGORIES
        new_is_non_profit = new_category in NON_PROFIT_CATEGORIES

        if old_was_non_profit == new_is_non_profit:
            if new_payment_method == PaymentMethod.CASH and old_payment_method != PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, -new_amount)
                logger.info(f"Fixed cost {doc_id} changed to cash payment. Subtracted {new_amount:.2f} from cash.")
            elif new_payment_method != PaymentMethod.CASH and old_payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, old_amount)
                logger.info(f"Fixed cost {doc_id} changed from cash payment. Added {old_amount:.2f} back to cash.")
            elif new_payment_method == PaymentMethod.CASH and old_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Fixed cost {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Fixed cost {doc_id} (cash payment) amount unchanged. No cash adjustment needed.")
            else:
                logger.info(f"Fixed cost {doc_id} payment method not cash, cash on hand not affected by update.")

        elif not old_was_non_profit and new_is_non_profit:
            if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, old_amount)
                logger.info(f"Fixed cost {doc_id} (cash payment) changed from business to non-profit, and from cash to non-cash. Added {old_amount:.2f} back to cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Fixed cost {doc_id} changed from business to non-profit, both cash. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Fixed cost {doc_id} changed from business to non-profit, cash payment, no amount change. No cash adjustment.")
            else:
                logger.info(f"Fixed cost {doc_id} changed from business to non-profit. No cash movement relevant to this transition.")

        elif old_was_non_profit and not new_is_non_profit:
            if old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, -new_amount)
                logger.info(f"Fixed cost {doc_id} changed from non-profit to business, and from non-cash to cash. Subtracted {new_amount:.2f} from cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Fixed cost {doc_id} changed from non-profit to business, both cash. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Fixed cost {doc_id} changed from non-profit to business, cash payment, no amount change. No cash adjustment.")
            else:
                logger.info(f"Fixed cost {doc_id} changed from non-profit to business. No cash movement relevant to this transition.")
        return True
    logger.warning(f"Fixed cost with ID {doc_id} not found for update (should not happen if updated_count is True).")
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
    NON_PROFIT_CATEGORIES = {ExpenseCategory.NON_BUSINESS_RELATED, ExpenseCategory.BANK_DEPOSIT}
    if expense.payment_method == PaymentMethod.CASH and expense.category not in NON_PROFIT_CATEGORIES:
        update_cash_on_hand_balance(db_session, -expense.amount)
        logger.info(f"Cash on hand decreased by {expense.amount:.2f} for daily expense (cash payment, business related).")
    elif expense.payment_method == PaymentMethod.CASH and expense.category in NON_PROFIT_CATEGORIES:
        update_cash_on_hand_balance(db_session, -expense.amount)
        logger.info(f"Cash on hand decreased by {expense.amount:.2f} for daily expense (cash payment, non-profit related).")
    return DailyExpense.model_validate(db_expense)

def get_all_daily_expenses(db_session: Session) -> List[DailyExpense]:
    expenses = db_session.query(DBDailyExpense).all()
    logger.info(f"Retrieved {len(expenses)} daily expenses.")
    return [DailyExpense.model_validate(expense) for expense in expenses]

def get_daily_expense_by_id(db_session: Session, doc_id: int) -> Optional[DailyExpense]:
    expense = db_session.query(DBDailyExpense).filter(DBDailyExpense.id == doc_id).first()
    if expense:
        logger.info(f"Retrieved daily expense with ID: {doc_id}")
        return DailyExpense.model_validate(expense)
    logger.warning(f"Daily expense with ID {doc_id} not found.")
    return None

def update_daily_expense(db_session: Session, doc_id: int, updates: Dict[str, Any]) -> bool:
    old_expense = get_daily_expense_by_id(db_session, doc_id)
    if not old_expense:
        logger.warning(f"Daily expense with ID {doc_id} not found for update.")
        return False

    old_amount = old_expense.amount
    old_payment_method = old_expense.payment_method
    old_category = old_expense.category

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
        new_category = new_expense.category

        NON_PROFIT_CATEGORIES = {
            ExpenseCategory.NON_BUSINESS_RELATED,
            ExpenseCategory.BANK_DEPOSIT
        }

        old_was_non_profit = old_category in NON_PROFIT_CATEGORIES
        new_is_non_profit = new_category in NON_PROFIT_CATEGORIES

        if old_was_non_profit == new_is_non_profit:
            if new_payment_method == PaymentMethod.CASH and old_payment_method != PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, -new_amount)
                logger.info(f"Daily expense {doc_id} changed to cash payment. Subtracted {new_amount:.2f} from cash.")
            elif new_payment_method != PaymentMethod.CASH and old_payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, old_amount)
                logger.info(f"Daily expense {doc_id} changed from cash payment. Added {old_amount:.2f} back to cash.")
            elif new_payment_method == PaymentMethod.CASH and old_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Daily expense {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Daily expense {doc_id} (cash payment) amount unchanged. No cash adjustment needed.")
            else:
                logger.info(f"Daily expense {doc_id} payment method not cash, cash on hand not affected by update.")

        elif not old_was_non_profit and new_is_non_profit:
            if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, old_amount)
                logger.info(f"Daily expense {doc_id} (cash payment) changed from business to non-profit, and from cash to non-cash. Added {old_amount:.2f} back to cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Daily expense {doc_id} changed from business to non-profit, both cash. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Daily expense {doc_id} changed from business to non-profit, cash payment, no amount change. No cash adjustment.")
            else:
                logger.info(f"Daily expense {doc_id} changed from business to non-profit. No cash movement relevant to this transition.")

        elif old_was_non_profit and not new_is_non_profit:
            if old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(db_session, -new_amount)
                logger.info(f"Daily expense {doc_id} changed from non-profit to business, and from non-cash to cash. Subtracted {new_amount:.2f} from cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                amount_difference = old_amount - new_amount
                if amount_difference != 0:
                    update_cash_on_hand_balance(db_session, amount_difference)
                    logger.info(f"Daily expense {doc_id} changed from non-profit to business, both cash. Adjusted cash by {amount_difference:.2f}.")
                else:
                    logger.info(f"Daily expense {doc_id} changed from non-profit to business, cash payment, no amount change. No cash adjustment.")
            else:
                logger.info(f"Daily expense {doc_id} changed from non-profit to business. No cash movement relevant to this transition.")
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
    return Income.model_validate(db_income)

def get_all_income(db_session: Session) -> List[Income]:
    incomes = db_session.query(DBIncome).all()
    logger.info(f"Retrieved {len(incomes)} income entries.")
    return [Income.model_validate(income) for income in incomes]

def get_income_by_id(db_session: Session, doc_id: int) -> Optional[Income]:
    income = db_session.query(DBIncome).filter(DBIncome.id == doc_id).first()
    if income:
        logger.info(f"Retrieved income entry with ID: {doc_id}")
        return Income.model_validate(income)
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

def get_daily_expenses_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[DailyExpense]:
    expenses = db_session.query(DBDailyExpense).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(expenses)} daily expenses between {start_date} and {end_date}.")
    return [DailyExpense.model_validate(exp) for exp in expenses]

def get_fixed_costs_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[FixedCost]:
    costs = db_session.query(DBFixedCost).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(costs)} fixed costs between {start_date} and {end_date}.")
    return [FixedCost.model_validate(cost) for cost in costs]

def get_income_by_date_range(db_session: Session, start_date: str, end_date: str) -> List[Income]:
    incomes = db_session.query(DBIncome).filter(
        and_(DBIncome.income_date >= start_date, DBIncome.income_date <= end_date)
    ).all()
    logger.info(f"Retrieved {len(incomes)} income entries between {start_date} and {end_date}.")
    return [Income.model_validate(inc) for inc in incomes]

def get_aggregated_income_by_date(db_session: Session) -> List[AggregatedIncome]:
    """
    Retrieves and aggregates income entries by income_date.
    """
    results = db_session.query(
        DBIncome.income_date,
        func.sum(DBIncome.tours_revenue_eur).label('total_tours_revenue_eur'),
        func.sum(DBIncome.transfers_revenue_eur).label('total_transfers_revenue_eur'),
        func.sum(DBIncome.tours_revenue_eur + DBIncome.transfers_revenue_eur).label('total_daily_income_eur'),
        func.sum(DBIncome.hours_worked).label('total_hours_worked')
    ).group_by(DBIncome.income_date).order_by(DBIncome.income_date.desc()).all()

    aggregated_incomes = []
    for row in results:
        aggregated_incomes.append(AggregatedIncome.model_validate(row._asdict()))
    
    logger.info(f"Retrieved {len(aggregated_incomes)} aggregated income entries.")
    return aggregated_incomes

def get_monthly_summary(db_session: Session, year: int, month: int) -> Dict[str, float]:
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    end_date = end_date_dt.strftime("%Y-%m-%d")

    excluded_categories_from_profit = {
        ExpenseCategory.NON_BUSINESS_RELATED,
        ExpenseCategory.BANK_DEPOSIT
    }

    total_monthly_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date),
        not_(DBDailyExpense.category.in_(excluded_categories_from_profit))
    ).scalar() or 0.0

    total_monthly_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date),
        not_(DBFixedCost.category.in_(excluded_categories_from_profit))
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

    excluded_categories_from_summary = {
        ExpenseCategory.NON_BUSINESS_RELATED,
        ExpenseCategory.BANK_DEPOSIT
    }

    daily_expenses = db_session.query(DBDailyExpense).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date),
        not_(DBDailyExpense.category.in_(excluded_categories_from_summary))
    ).all()
    for expense in daily_expenses:
        category_totals[expense.category.value] += expense.amount

    fixed_costs = db_session.query(DBFixedCost).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date),
        not_(DBFixedCost.category.in_(excluded_categories_from_summary))
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

def get_weekly_summary(db_session: Session, start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """
    Retrieves a summary of total expenses, total income, and net profit/loss for a given week.
    """
    excluded_categories_from_profit = {
        ExpenseCategory.NON_BUSINESS_RELATED,
        ExpenseCategory.BANK_DEPOSIT
    }

    total_daily_expenses_for_week = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        and_(
            DBDailyExpense.cost_date >= start_date.strftime('%Y-%m-%d'),
            DBDailyExpense.cost_date <= end_date.strftime('%Y-%m-%d'),
            not_(DBDailyExpense.category.in_(excluded_categories_from_profit))
        )
    ).scalar() or 0.0

    total_fixed_costs_for_week = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        and_(
            DBFixedCost.cost_date >= start_date.strftime('%Y-%m-%d'),
            DBFixedCost.cost_date <= end_date.strftime('%Y-%m-%d'),
            not_(DBFixedCost.category.in_(excluded_categories_from_profit))
        )
    ).scalar() or 0.0
    
    total_expenses = total_daily_expenses_for_week + total_fixed_costs_for_week

    income_results = db_session.query(
        func.sum(DBIncome.tours_revenue_eur),
        func.sum(DBIncome.transfers_revenue_eur)
    ).filter(
        and_(
            DBIncome.income_date >= start_date.strftime('%Y-%m-%d'),
            DBIncome.income_date <= end_date.strftime('%Y-%m-%d')
        )
    ).first()

    total_income = (income_results[0] or 0.0) + (income_results[1] or 0.0)
    net_profit = total_income - total_expenses

    summary = {
        "total_weekly_expenses": round(total_expenses, 2),
        "total_weekly_income": round(total_income, 2),
        "net_weekly_profit": round(net_profit, 2),
    }
    logger.info(f"Generated weekly summary for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}: {summary}")
    return summary

def get_weekly_expense_categories_summary(db_session: Session, start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """
    Retrieves a summary of expenses grouped by category for a given week.
    """
    daily_expenses_by_category = db_session.query(
        DBDailyExpense.category,
        func.sum(DBDailyExpense.amount)
    ).filter(
        and_(
            DBDailyExpense.cost_date >= start_date.strftime('%Y-%m-%d'),
            DBDailyExpense.cost_date <= end_date.strftime('%Y-%m-%d')
        )
    ).group_by(DBDailyExpense.category).all()

    fixed_costs_by_category = db_session.query(
        DBFixedCost.category,
        func.sum(DBFixedCost.amount_eur)
    ).filter(
        and_(
            DBFixedCost.cost_date >= start_date.strftime('%Y-%m-%d'),
            DBFixedCost.cost_date <= end_date.strftime('%Y-%m-%d')
        )
    ).group_by(DBFixedCost.category).all()

    expense_summary = defaultdict(float)
    for category, amount in daily_expenses_by_category:
        expense_summary[category.value] += amount
    for category, amount in fixed_costs_by_category:
        expense_summary[category.value] += amount

    return {category: round(amount, 2) for category, amount in expense_summary.items()}

def get_weekly_income_sources_summary(db_session: Session, start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """
    Retrieves a summary of income by source for a given week.
    """
    income_summary = db_session.query(
        func.sum(DBIncome.tours_revenue_eur).label('tours_revenue_eur'),
        func.sum(DBIncome.transfers_revenue_eur).label('transfers_revenue_eur')
    ).filter(
        and_(
            DBIncome.income_date >= start_date.strftime('%Y-%m-%d'),
            DBIncome.income_date <= end_date.strftime('%Y-%m-%d')
        )
    ).first()

    summary = {
        "Tours": round(income_summary.tours_revenue_eur, 2) if income_summary.tours_revenue_eur else 0.0,
        "Transfers": round(income_summary.transfers_revenue_eur, 2) if income_summary.transfers_revenue_eur else 0.0,
    }
    return summary

def get_daily_income_average_for_period(db_session: Session, start_date: datetime, end_date: datetime) -> float:
    """
    Calculates the daily average income over a specified period,
    considering only days that had recorded income.
    """
    # Apply the helper function to DBIncome.income_date
    income_date_col = _get_date_column_expression(db_session, DBIncome.income_date)

    total_income_tours = db_session.query(func.sum(DBIncome.tours_revenue_eur)).filter(
        income_date_col >= start_date, # Use the casted/converted column
        income_date_col <= end_date    # Use the casted/converted column
    ).scalar() or 0.0

    total_income_transfers = db_session.query(func.sum(DBIncome.transfers_revenue_eur)).filter(
        income_date_col >= start_date, # Use the casted/converted column
        income_date_col <= end_date    # Use the casted/converted column
    ).scalar() or 0.0

    total_income = total_income_tours + total_income_transfers

    num_days_with_income = db_session.query(func.count(distinct(income_date_col))).filter( # Apply distinct on the casted/converted column
        income_date_col >= start_date,
        income_date_col <= end_date
    ).scalar() or 0

    if num_days_with_income > 0:
        daily_average_income = total_income / num_days_with_income
    else:
        daily_average_income = 0.0

    logger.info(f"Calculated daily income average for period {start_date} to {end_date}: {daily_average_income:.2f} over {num_days_with_income} days with income.")
    return round(daily_average_income, 2)

def get_yearly_summary(db_session: Session, year: int) -> Dict[str, float]:
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    excluded_categories_from_profit = {
        ExpenseCategory.NON_BUSINESS_RELATED,
        ExpenseCategory.BANK_DEPOSIT
    }

    total_yearly_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        and_(DBDailyExpense.cost_date >= start_date, DBDailyExpense.cost_date <= end_date),
        not_(DBDailyExpense.category.in_(excluded_categories_from_profit))
    ).scalar() or 0.0

    total_yearly_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        and_(DBFixedCost.cost_date >= start_date, DBFixedCost.cost_date <= end_date),
        not_(DBFixedCost.category.in_(excluded_categories_from_profit))
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
    excluded_categories_from_profit = {
        ExpenseCategory.NON_BUSINESS_RELATED,
        ExpenseCategory.BANK_DEPOSIT
    }

    total_global_daily_expenses = db_session.query(func.sum(DBDailyExpense.amount)).filter(
        not_(DBDailyExpense.category.in_(excluded_categories_from_profit))
    ).scalar() or 0.0
    total_global_fixed_costs = db_session.query(func.sum(DBFixedCost.amount_eur)).filter(
        not_(DBFixedCost.category.in_(excluded_categories_from_profit))
    ).scalar() or 0.0
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

def create_all_tables(engine_param=None):
    target_engine = engine_param if engine_param else engine
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database tables created successfully (if they didn't already exist).")

def get_single_day_income_summary(db_session: Session, target_date: datetime) -> AggregatedIncome:
    logger.info(f"DB: Attempting to retrieve single day income summary for {target_date.date()}")

    # Use the helper function to get the appropriate date column expression
    income_date_col = _get_date_column_expression(db_session, DBIncome.income_date)

    income_summary_query = db_session.query(
        func.sum(DBIncome.tours_revenue_eur).label('total_tours_revenue_eur'),
        func.sum(DBIncome.transfers_revenue_eur).label('total_transfers_revenue_eur'),
        func.sum(DBIncome.hours_worked).label('total_hours_worked')
    ).filter(
        income_date_col == target_date.date() # Compare with a date object
    ).first()

    # Handle case where no income entries exist for the day
    if income_summary_query is None or (income_summary_query.total_tours_revenue_eur is None and income_summary_query.total_transfers_revenue_eur is None):
        logger.info(f"DB: No income entries found for {target_date.date()}. Returning zero summary.")
        return AggregatedIncome(
            income_date=target_date.strftime("%Y-%m-%d"),
            total_tours_revenue_eur=0.0,
            total_transfers_revenue_eur=0.0,
            total_daily_income_eur=0.0,
            total_hours_worked=0.0
        )

    # Extract summed values, defaulting to 0.0 if None
    total_tours_revenue = income_summary_query.total_tours_revenue_eur or 0.0
    total_transfers_revenue = income_summary_query.total_transfers_revenue_eur or 0.0
    total_hours_worked = income_summary_query.total_hours_worked or 0.0
    total_daily_income = total_tours_revenue + total_transfers_revenue

    summary = AggregatedIncome(
        income_date=target_date.strftime("%Y-%m-%d"),
        total_tours_revenue_eur=round(total_tours_revenue, 2),
        total_transfers_revenue_eur=round(total_transfers_revenue, 2),
        total_daily_income_eur=round(total_daily_income, 2),
        total_hours_worked=round(total_hours_worked, 2)
    )
    logger.info(f"DB: Generated single day income summary for {target_date.date()}: {summary.total_daily_income_eur:.2f} EUR")
    return summary