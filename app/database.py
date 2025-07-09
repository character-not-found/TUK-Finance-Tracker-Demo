# database.py
# First, ensure you have TinyDB and Pydantic installed in your virtual environment:
# pip install tinydb pydantic

from tinydb import TinyDB, Query
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
import logging # Import logging
from pathlib import Path # Import Path

# Import the defined models
from .models import FixedCost, DailyExpense, Income, CostFrequency, ExpenseCategory, CashOnHand, PaymentMethod # Import CashOnHand and PaymentMethod

# Get a logger for this module
logger = logging.getLogger(__name__)

# Initialize the TinyDB database.
db_path = Path(__file__).parent.parent / 'db.json'
db = TinyDB(str(db_path))

# Define tables for different types of financial entries.
fixed_costs_table = db.table('fixed_costs')
daily_expenses_table = db.table('daily_expenses')
income_table = db.table('income')
cash_on_hand_table = db.table('cash_on_hand') # New table for cash on hand

# Define a Query object for easier querying
Entry = Query()
CashEntry = Query() # New Query object for CashOnHand table

# --- Functions for managing Cash On Hand ---

def get_cash_on_hand_balance() -> CashOnHand:
    """
    Retrieves the current cash on hand balance.
    If no entry exists, it initializes it to 0.0 and returns it.
    """
    try:
        balance_entry = cash_on_hand_table.all()
        if not balance_entry:
            # Initialize with 0.0 if no entry exists
            initial_balance_data = {
                'balance': 0.0,
                'last_updated': datetime.now().isoformat()
            }
            doc_id = cash_on_hand_table.insert(initial_balance_data)
            logger.info("Initialized cash on hand balance to 0.0.")
            return CashOnHand(doc_id=doc_id, **initial_balance_data)
        else:
            # There should ideally be only one entry, return the first one
            entry = balance_entry[0]
            logger.debug(f"Retrieved cash on hand balance: {entry['balance']}")
            return CashOnHand(doc_id=entry.doc_id, **entry)
    except Exception as e:
        logger.error(f"Error retrieving or initializing cash on hand balance: {e}", exc_info=True)
        # Return a default/error state CashOnHand object
        return CashOnHand(balance=0.0, last_updated=datetime.now())

def update_cash_on_hand_balance(amount: float):
    """
    Updates the cash on hand balance by adding the specified amount.
    A positive amount increases cash, a negative amount decreases it.
    """
    try:
        current_balance_entry = get_cash_on_hand_balance()
        new_balance = current_balance_entry.balance + amount
        updated_data = {
            'balance': round(new_balance, 2), # Round to 2 decimal places for currency
            'last_updated': datetime.now().isoformat()
        }
        # Update the existing entry (assuming there's only one)
        cash_on_hand_table.update(updated_data, doc_ids=[current_balance_entry.doc_id])
        logger.info(f"Cash on hand updated by {amount:.2f}. New balance: {new_balance:.2f}")
    except Exception as e:
        logger.error(f"Error updating cash on hand balance by {amount}: {e}", exc_info=True)
        raise # Re-raise to indicate failure to the calling function

def set_initial_cash_on_hand(initial_balance: float) -> CashOnHand:
    """
    Sets the initial cash on hand balance.
    This should typically only be called once or for a full reset.
    """
    try:
        # Clear existing entries to ensure only one
        cash_on_hand_table.truncate()
        initial_balance_data = {
            'balance': round(initial_balance, 2),
            'last_updated': datetime.now().isoformat()
        }
        doc_id = cash_on_hand_table.insert(initial_balance_data)
        logger.info(f"Initial cash on hand balance set to {initial_balance:.2f}.")
        return CashOnHand(doc_id=doc_id, **initial_balance_data)
    except Exception as e:
        logger.error(f"Error setting initial cash on hand balance to {initial_balance}: {e}", exc_info=True)
        raise

# --- Functions for managing Fixed Costs ---

def add_fixed_cost(cost: FixedCost) -> FixedCost:
    """
    Adds a new fixed cost entry to the fixed_costs table and updates cash on hand if payment method is Cash.
    """
    try:
        cost_data = cost.model_dump(exclude_none=True, exclude={'doc_id'})
        cost_data['timestamp'] = datetime.now().isoformat()
        doc_id = fixed_costs_table.insert(cost_data)
        cost.doc_id = doc_id
        cost.timestamp = datetime.fromisoformat(cost_data['timestamp'])
        logger.info(f"Added fixed cost: {cost.description} with ID {doc_id}")
        if cost.payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(-cost.amount_eur) # Decrease cash on hand
            logger.info(f"Cash on hand decreased by {cost.amount_eur:.2f} for fixed cost (cash payment).")
        else:
            logger.info(f"Fixed cost {cost.description} paid by {cost.payment_method.value}, cash on hand not affected.")
        return cost
    except Exception as e:
        logger.error(f"Error adding fixed cost: {e}", exc_info=True)
        raise

def get_all_fixed_costs() -> List[FixedCost]:
    """
    Retrieves a list of all fixed cost entries from the fixed_costs table.
    Handles missing 'payment_method' by defaulting to 'Cash' for old entries.
    """
    try:
        costs = []
        for doc in fixed_costs_table.all():
            # Create a mutable copy of the document data
            doc_data = dict(doc)
            # Provide a default value for 'payment_method' if it's missing in old entries
            if 'payment_method' not in doc_data or doc_data['payment_method'] is None:
                doc_data['payment_method'] = PaymentMethod.CASH.value # Default to Cash for old entries
                logger.warning(f"Fixed cost ID {doc.doc_id} missing payment_method, defaulted to Cash.")
            costs.append(FixedCost(doc_id=doc.doc_id, **doc_data))
        logger.info(f"Retrieved {len(costs)} fixed costs.")
        return costs
    except Exception as e:
        logger.error(f"Error retrieving all fixed costs: {e}", exc_info=True)
        return []

def get_fixed_cost_by_id(doc_id: int) -> Optional[FixedCost]:
    """
    Retrieves a single fixed cost entry by its document ID.
    """
    try:
        # Cast doc_id to int to ensure correct lookup with TinyDB
        cost_data = fixed_costs_table.get(doc_id=int(doc_id))
        if cost_data:
            # Create a mutable copy of the document data
            cost_data_mutable = dict(cost_data)
            # Provide a default value for 'payment_method' if it's missing
            if 'payment_method' not in cost_data_mutable or cost_data_mutable['payment_method'] is None:
                cost_data_mutable['payment_method'] = PaymentMethod.CASH.value
                logger.warning(f"Fixed cost ID {doc_id} missing payment_method, defaulted to Cash for retrieval.")
            logger.info(f"Retrieved fixed cost with ID: {doc_id}")
            return FixedCost(doc_id=cost_data.doc_id, **cost_data_mutable)
        logger.warning(f"Fixed cost with ID {doc_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving fixed cost by ID {doc_id}: {e}", exc_info=True)
        return None

def update_fixed_cost(doc_id: int, updates: Dict[str, Any]) -> bool:
    """
    Updates an existing fixed cost entry by its document ID and conditionally adjusts cash on hand.
    """
    try:
        old_cost = get_fixed_cost_by_id(doc_id)
        if not old_cost:
            logger.warning(f"Fixed cost with ID {doc_id} not found for update.")
            return False

        old_amount = old_cost.amount_eur
        old_payment_method = old_cost.payment_method

        new_amount = updates.get('amount_eur', old_amount) # Use new amount if provided, else old
        # Ensure new_payment_method is a PaymentMethod Enum member
        new_payment_method_str = updates.get('payment_method', old_payment_method.value if old_payment_method else PaymentMethod.CASH.value)
        new_payment_method = PaymentMethod(new_payment_method_str)


        # Convert enum values from string if necessary (FastAPI handles this for Pydantic models, but direct updates might need it)
        if 'cost_frequency' in updates and isinstance(updates['cost_frequency'], str):
            updates['cost_frequency'] = CostFrequency(updates['cost_frequency'])
        if 'category' in updates and isinstance(updates['category'], str):
            updates['category'] = ExpenseCategory(updates['category'])
        # Ensure payment_method in updates is stored as its value string
        if 'payment_method' in updates and isinstance(updates['payment_method'], PaymentMethod):
            updates['payment_method'] = updates['payment_method'].value
        elif 'payment_method' in updates and isinstance(updates['payment_method'], str):
            updates['payment_method'] = PaymentMethod(updates['payment_method']).value # Convert string to Enum then to value

        updates['timestamp'] = datetime.now().isoformat()

        # Cast doc_id to int for the update operation, and use doc_ids (plural)
        updated_count = fixed_costs_table.update(updates, doc_ids=[int(doc_id)])
        if updated_count:
            logger.info(f"Updated fixed cost with ID {doc_id}. Changes: {updates}")

            # Adjust cash on hand based on old and new payment methods and amounts
            if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
                # Was cash, now not cash: add old amount back to cash
                update_cash_on_hand_balance(old_amount)
                logger.info(f"Fixed cost {doc_id} changed from cash to {new_payment_method.value}. Added {old_amount:.2f} back to cash.")
            elif old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                # Was not cash, now cash: subtract new amount from cash
                update_cash_on_hand_balance(-new_amount)
                logger.info(f"Fixed cost {doc_id} changed from {old_payment_method.value} to cash. Subtracted {new_amount:.2f} from cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                # Both are cash: adjust by the difference
                amount_difference = old_amount - new_amount
                update_cash_on_hand_balance(amount_difference)
                logger.info(f"Fixed cost {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
            else:
                logger.info(f"Fixed cost {doc_id} payment method not cash, cash on hand not affected by update.")
            return True
        logger.warning(f"Fixed cost with ID {doc_id} not found for update.")
        return False
    except Exception as e:
        logger.error(f"Error updating fixed cost with ID {doc_id}: {e}", exc_info=True)
        return False

def delete_fixed_cost(doc_id: int) -> bool:
    """
    Deletes a fixed cost entry by its document ID and conditionally adjusts cash on hand.
    """
    try:
        cost_to_delete = get_fixed_cost_by_id(doc_id)
        if not cost_to_delete:
            logger.warning(f"Fixed cost with ID {doc_id} not found for deletion.")
            return False

        # Cast doc_id to int for the remove operation
        deleted_count = fixed_costs_table.remove(doc_ids=[int(doc_id)])
        if deleted_count:
            logger.info(f"Deleted fixed cost with ID {doc_id}.")
            if cost_to_delete.payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(cost_to_delete.amount_eur) # Add amount back to cash on hand
                logger.info(f"Cash on hand increased by {cost_to_delete.amount_eur:.2f} due to deletion of cash-paid fixed cost.")
            else:
                logger.info(f"Fixed cost {doc_id} payment method not cash, cash on hand not affected by deletion.")
            return True
        logger.warning(f"Fixed cost with ID {doc_id} not found for deletion.")
        return False
    except Exception as e:
        logger.error(f"Error deleting fixed cost with ID {doc_id}: {e}", exc_info=True)
        return False

# --- Functions for managing Daily Expenses ---

def add_daily_expense(expense: DailyExpense) -> DailyExpense:
    """
    Adds a new daily expense entry to the daily_expenses table and updates cash on hand if payment method is Cash.
    """
    try:
        expense_data = expense.model_dump(exclude_none=True, exclude={'doc_id'})
        expense_data['timestamp'] = datetime.now().isoformat()
        doc_id = daily_expenses_table.insert(expense_data)
        expense.doc_id = doc_id
        expense.timestamp = datetime.fromisoformat(expense_data['timestamp'])
        logger.info(f"Added daily expense: {expense.description} with ID {doc_id}")
        if expense.payment_method == PaymentMethod.CASH:
            update_cash_on_hand_balance(-expense.amount) # Decrease cash on hand
            logger.info(f"Cash on hand decreased by {expense.amount:.2f} for daily expense (cash payment).")
        else:
            logger.info(f"Daily expense {expense.description} paid by {expense.payment_method.value}, cash on hand not affected.")
        return expense
    except Exception as e:
        logger.error(f"Error adding daily expense: {e}", exc_info=True)
        raise

def get_all_daily_expenses() -> List[DailyExpense]:
    """
    Retrieves a list of all daily expense entries from the daily_expenses table.
    Handles missing 'payment_method' by defaulting to 'Cash' for old entries.
    """
    try:
        expenses = []
        for doc in daily_expenses_table.all():
            # Create a mutable copy of the document data
            doc_data = dict(doc)
            # Provide a default value for 'payment_method' if it's missing in old entries
            if 'payment_method' not in doc_data or doc_data['payment_method'] is None:
                doc_data['payment_method'] = PaymentMethod.CASH.value # Default to Cash for old entries
                logger.warning(f"Daily expense ID {doc.doc_id} missing payment_method, defaulted to Cash.")
            expenses.append(DailyExpense(doc_id=doc.doc_id, **doc_data))
        logger.info(f"Retrieved {len(expenses)} daily expenses.")
        return expenses
    except Exception as e:
        logger.error(f"Error retrieving all daily expenses: {e}", exc_info=True)
        return []

def get_daily_expense_by_id(doc_id: int) -> Optional[DailyExpense]:
    """
    Retrieves a single daily expense entry by its document ID.
    """
    try:
        # Cast doc_id to int to ensure correct lookup with TinyDB
        expense_data = daily_expenses_table.get(doc_id=int(doc_id))
        if expense_data:
            # Create a mutable copy of the document data
            expense_data_mutable = dict(expense_data)
            # Provide a default value for 'payment_method' if it's missing
            if 'payment_method' not in expense_data_mutable or expense_data_mutable['payment_method'] is None:
                expense_data_mutable['payment_method'] = PaymentMethod.CASH.value
                logger.warning(f"Daily expense ID {doc_id} missing payment_method, defaulted to Cash for retrieval.")
            logger.info(f"Retrieved daily expense with ID: {doc_id}")
            return DailyExpense(doc_id=expense_data.doc_id, **expense_data_mutable)
        logger.warning(f"Daily expense with ID {doc_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving daily expense by ID {doc_id}: {e}", exc_info=True)
        return None

def update_daily_expense(doc_id: int, updates: Dict[str, Any]) -> bool:
    """
    Updates an existing daily expense entry by its document ID and conditionally adjusts cash on hand.
    """
    try:
        old_expense = get_daily_expense_by_id(doc_id)
        if not old_expense:
            logger.warning(f"Daily expense with ID {doc_id} not found for update.")
            return False

        old_amount = old_expense.amount
        old_payment_method = old_expense.payment_method

        new_amount = updates.get('amount', old_amount)
        # Ensure new_payment_method is a PaymentMethod Enum member
        new_payment_method_str = updates.get('payment_method', old_payment_method.value if old_payment_method else PaymentMethod.CASH.value)
        new_payment_method = PaymentMethod(new_payment_method_str)

        updates['timestamp'] = datetime.now().isoformat()
        if 'category' in updates and isinstance(updates['category'], str):
            updates['category'] = ExpenseCategory(updates['category'])
        # Ensure payment_method in updates is stored as its value string
        if 'payment_method' in updates and isinstance(updates['payment_method'], PaymentMethod):
            updates['payment_method'] = updates['payment_method'].value
        elif 'payment_method' in updates and isinstance(updates['payment_method'], str):
            updates['payment_method'] = PaymentMethod(updates['payment_method']).value # Convert string to Enum then to value

        # Cast doc_id to int for the update operation, and use doc_ids (plural)
        updated_count = daily_expenses_table.update(updates, doc_ids=[int(doc_id)])
        if updated_count:
            logger.info(f"Updated daily expense with ID {doc_id}. Changes: {updates}")

            # Adjust cash on hand based on old and new payment methods and amounts
            if old_payment_method == PaymentMethod.CASH and new_payment_method != PaymentMethod.CASH:
                # Was cash, now not cash: add old amount back to cash
                update_cash_on_hand_balance(old_amount)
                logger.info(f"Daily expense {doc_id} changed from cash to {new_payment_method.value}. Added {old_amount:.2f} back to cash.")
            elif old_payment_method != PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                # Was not cash, now cash: subtract new amount from cash
                update_cash_on_hand_balance(-new_amount)
                logger.info(f"Daily expense {doc_id} changed from {old_payment_method.value} to cash. Subtracted {new_amount:.2f} from cash.")
            elif old_payment_method == PaymentMethod.CASH and new_payment_method == PaymentMethod.CASH:
                # Both are cash: adjust by the difference
                amount_difference = old_amount - new_amount
                update_cash_on_hand_balance(amount_difference)
                logger.info(f"Daily expense {doc_id} (cash payment) amount changed. Adjusted cash by {amount_difference:.2f}.")
            else:
                logger.info(f"Daily expense {doc_id} payment method not cash, cash on hand not affected by update.")
            return True
        logger.warning(f"Daily expense with ID {doc_id} not found for update.")
        return False
    except Exception as e:
        logger.error(f"Error updating daily expense with ID {doc_id}: {e}", exc_info=True)
        return False

def delete_daily_expense(doc_id: int) -> bool:
    """
    Deletes a daily expense entry by its document ID and conditionally adjusts cash on hand.
    """
    try:
        expense_to_delete = get_daily_expense_by_id(doc_id)
        if not expense_to_delete:
            logger.warning(f"Daily expense with ID {doc_id} not found for deletion.")
            return False

        # Cast doc_id to int for the remove operation
        deleted_count = daily_expenses_table.remove(doc_ids=[int(doc_id)])
        if deleted_count:
            logger.info(f"Deleted daily expense with ID {doc_id}.")
            if expense_to_delete.payment_method == PaymentMethod.CASH:
                update_cash_on_hand_balance(expense_to_delete.amount) # Add amount back to cash on hand
                logger.info(f"Cash on hand increased by {expense_to_delete.amount:.2f} due to deletion of cash-paid daily expense.")
            else:
                logger.info(f"Daily expense {doc_id} payment method not cash, cash on hand not affected by deletion.")
            return True
        logger.warning(f"Daily expense with ID {doc_id} not found for deletion.")
        return False
    except Exception as e:
        logger.error(f"Error deleting daily expense with ID {doc_id}: {e}", exc_info=True)
        return False

# --- Functions for managing Income ---

def add_income(income: Income) -> Income:
    """
    Adds a new income entry to the income table and updates cash on hand.
    """
    try:
        income_data = income.model_dump(exclude_none=True, exclude={'doc_id'})
        income_data['timestamp'] = datetime.now().isoformat()
        doc_id = income_table.insert(income_data)
        income.doc_id = doc_id
        income.timestamp = datetime.fromisoformat(income_data['timestamp'])
        logger.info(f"Added income entry: {income.income_date} with ID {doc_id}")
        total_income_amount = income.tours_revenue_eur + income.transfers_revenue_eur
        update_cash_on_hand_balance(total_income_amount) # Increase cash on hand
        logger.info(f"Cash on hand increased by {total_income_amount:.2f} for income.")
        return income
    except Exception as e:
        logger.error(f"Error adding income entry: {e}", exc_info=True)
        raise

def get_all_income() -> List[Income]:
    """
    Retrieves a list of all income entries from the income table.
    """
    try:
        incomes = [Income(doc_id=doc.doc_id, **doc) for doc in income_table.all()]
        logger.info(f"Retrieved {len(incomes)} income entries.")
        return incomes
    except Exception as e:
        logger.error(f"Error retrieving all income entries: {e}", exc_info=True)
        return []

def get_income_by_id(doc_id: int) -> Optional[Income]:
    """
    Retrieves a single income entry by its document ID.
    """
    try:
        # Cast doc_id to int to ensure correct lookup with TinyDB
        income_data = income_table.get(doc_id=int(doc_id))
        if income_data:
            logger.info(f"Retrieved income entry with ID: {doc_id}")
            return Income(doc_id=income_data.doc_id, **income_data)
        logger.warning(f"Income entry with ID {doc_id} not found.")
        return None
    except Exception as e:
        logger.error(f"Error retrieving income entry by ID {doc_id}: {e}", exc_info=True)
        return None

def update_income(doc_id: int, updates: Dict[str, Any]) -> bool:
    """
    Updates an existing income entry by its document ID and adjusts cash on hand.
    """
    try:
        old_income = get_income_by_id(doc_id)
        if not old_income:
            logger.warning(f"Income entry with ID {doc_id} not found for update.")
            return False

        old_total_income = old_income.tours_revenue_eur + old_income.transfers_revenue_eur
        new_tours_revenue = updates.get('tours_revenue_eur', old_income.tours_revenue_eur)
        new_transfers_revenue = updates.get('transfers_revenue_eur', old_income.transfers_revenue_eur)
        new_total_income = new_tours_revenue + new_transfers_revenue

        updates['timestamp'] = datetime.now().isoformat()

        # Cast doc_id to int for the update operation, and use doc_ids (plural)
        updated_count = income_table.update(updates, doc_ids=[int(doc_id)])
        if updated_count:
            logger.info(f"Updated income entry with ID {doc_id}. Changes: {updates}")
            amount_difference = new_total_income - old_total_income # If new is higher, difference is positive (more income)
            update_cash_on_hand_balance(amount_difference) # Adjust cash on hand
            logger.info(f"Income {doc_id} amount changed. Adjusted cash by {amount_difference:.2f}.")
            return True
        logger.warning(f"Income entry with ID {doc_id} not found for update.")
        return False
    except Exception as e:
        logger.error(f"Error updating income entry with ID {doc_id}: {e}", exc_info=True)
        return False

def delete_income(doc_id: int) -> bool:
    """
    Deletes an income entry by its document ID and adjusts cash on hand.
    """
    try:
        income_to_delete = get_income_by_id(doc_id)
        if not income_to_delete:
            logger.warning(f"Income entry with ID {doc_id} not found for deletion.")
            return False

        # Cast doc_id to int for the remove operation
        deleted_count = income_table.remove(doc_ids=[int(doc_id)])
        if deleted_count:
            logger.info(f"Deleted income entry with ID {doc_id}.")
            total_income_amount = income_to_delete.tours_revenue_eur + income_to_delete.transfers_revenue_eur
            update_cash_on_hand_balance(-total_income_amount) # Decrease cash on hand
            logger.info(f"Cash on hand decreased by {total_income_amount:.2f} due to deletion of income.")
            return True
        logger.warning(f"Income entry with ID {doc_id} not found for deletion.")
        return False
    except Exception as e:
        logger.error(f"Error deleting income entry with ID {doc_id}: {e}", exc_info=True)
        return False

# --- Functions for clearing all data (for development/testing) ---
def clear_all_data():
    """
    Clears all data from all tables, including cash on hand. Use with caution!
    """
    try:
        fixed_costs_table.truncate()
        daily_expenses_table.truncate()
        income_table.truncate()
        cash_on_hand_table.truncate() # Clear cash on hand table as well
        # Re-initialize cash on hand to 0 after clearing
        set_initial_cash_on_hand(0.0)
        logger.info("All database tables truncated and cash on hand reset to 0.0 successfully.")
    except Exception as e:
        logger.error(f"Error clearing all data: {e}", exc_info=True)
        raise

# --- Functions for Summaries ---

def get_daily_expenses_by_date_range(start_date: str, end_date: str) -> List[DailyExpense]:
    """
    Retrieves daily expense entries within a specified date range.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        expenses = []
        for doc in daily_expenses_table.search(
                (Entry.cost_date >= start_date) & (Entry.cost_date <= end_date)
            ):
            # Create a mutable copy of the document data
            doc_data = dict(doc)
            if 'payment_method' not in doc_data or doc_data['payment_method'] is None:
                doc_data['payment_method'] = PaymentMethod.CASH.value # Default for old entries
                logger.warning(f"Daily expense ID {doc.doc_id} missing payment_method, defaulted to Cash.")
            expenses.append(DailyExpense(doc_id=doc.doc_id, **doc_data))
        logger.info(f"Retrieved {len(expenses)} daily expenses between {start_date} and {end_date}.")
        return expenses
    except Exception as e:
        logger.error(f"Error retrieving daily expenses by date range ({start_date} to {end_date}): {e}", exc_info=True)
        return []

def get_fixed_costs_by_date_range(start_date: str, end_date: str) -> List[FixedCost]:
    """
    Retrieves fixed cost entries within a specified date range.
    This function considers all fixed costs, regardless of frequency,
    if their cost_date falls within the range.
    """
    try:
        costs = []
        for doc in fixed_costs_table.search(
                (Entry.cost_date >= start_date) & (Entry.cost_date <= end_date)
            ):
            # Create a mutable copy of the document data
            doc_data = dict(doc)
            if 'payment_method' not in doc_data or doc_data['payment_method'] is None:
                doc_data['payment_method'] = PaymentMethod.CASH.value # Default for old entries
                logger.warning(f"Fixed cost ID {doc.doc_id} missing payment_method, defaulted to Cash.")
            costs.append(FixedCost(doc_id=doc.doc_id, **doc_data))
        logger.info(f"Retrieved {len(costs)} fixed costs between {start_date} and {end_date}.")
        return costs
    except Exception as e:
        logger.error(f"Error retrieving fixed costs by date range ({start_date} to {end_date}): {e}", exc_info=True)
        return []

def get_income_by_date_range(start_date: str, end_date: str) -> List[Income]:
    """
    Retrieves income entries within a specified date range.
    """
    try:
        incomes = [
            Income(doc_id=doc.doc_id, **doc)
            for doc in income_table.search(
                (Entry.income_date >= start_date) & (Entry.income_date <= end_date)
            )
        ]
        logger.info(f"Retrieved {len(incomes)} income entries between {start_date} and {end_date}.")
        return incomes
    except Exception as e:
        logger.error(f"Error retrieving income by date range ({start_date} to {end_date}): {e}", exc_info=True)
        return []

def get_monthly_summary(year: int, month: int) -> Dict[str, float]:
    """
    Calculates total monthly expenses, income, and net profit/loss.
    """
    try:
        # Construct date range for the month
        start_date = f"{year}-{month:02d}-01"
        # Calculate the last day of the month
        if month == 12:
            end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        end_date = end_date_dt.strftime("%Y-%m-%d")

        # Sum all daily expenses for the month
        all_daily_expenses_month = get_daily_expenses_by_date_range(start_date, end_date)
        total_monthly_daily_expenses = sum(expense.amount for expense in all_daily_expenses_month)

        # Sum all fixed costs for the month (only monthly ones, and prorate annual/initial if needed, but for simplicity, sum all in range)
        # For a true monthly summary, you'd need to decide how to prorate annual/one-off costs.
        # Assuming for now, we sum all fixed costs whose 'cost_date' falls within the month.
        all_fixed_costs_month = get_fixed_costs_by_date_range(start_date, end_date)
        total_monthly_fixed_costs = sum(cost.amount_eur for cost in all_fixed_costs_month)

        total_monthly_expenses = total_monthly_daily_expenses + total_monthly_fixed_costs

        all_income_month = get_income_by_date_range(start_date, end_date)
        # Calculate total monthly income dynamically from tours and transfers revenue
        total_monthly_income = sum(inc.tours_revenue_eur + inc.transfers_revenue_eur for inc in all_income_month)

        net_monthly_profit = total_monthly_income - total_monthly_expenses

        summary = {
            "total_monthly_expenses": round(total_monthly_expenses, 2),
            "total_monthly_income": round(total_monthly_income, 2),
            "net_monthly_profit": round(net_monthly_profit, 2)
        }
        logger.info(f"Generated monthly summary for {year}-{month:02d}: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating monthly summary for {year}-{month:02d}: {e}", exc_info=True)
        return {}

def get_expense_categories_summary(year: int, month: int) -> Dict[str, float]:
    """
    Calculates total expenses grouped by category for a given month.
    Includes both daily expenses and fixed costs.
    """
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        end_date = end_date_dt.strftime("%Y-%m-%d")

        category_totals = defaultdict(float)

        # Daily Expenses
        daily_expenses = get_daily_expenses_by_date_range(start_date, end_date)
        for expense in daily_expenses:
            category_totals[expense.category.value] += expense.amount

        # Fixed Costs
        fixed_costs = get_fixed_costs_by_date_range(start_date, end_date)
        for cost in fixed_costs:
            category_totals[cost.category.value] += cost.amount_eur

        summary = {category: round(total, 2) for category, total in category_totals.items()}
        logger.info(f"Generated expense categories summary for {year}-{month:02d}: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating expense categories summary for {year}-{month:02d}: {e}", exc_info=True)
        return {}


def get_income_sources_summary(year: int, month: int) -> Dict[str, float]:
    """
    Calculates total income grouped by source (Tours, Transfers) for a given month.
    """
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        end_date = end_date_dt.strftime("%Y-%m-%d")

        source_totals = defaultdict(float)
        income_entries = get_income_by_date_range(start_date, end_date)

        for income in income_entries:
            source_totals['Tours'] += income.tours_revenue_eur
            source_totals['Transfers'] += income.transfers_revenue_eur

        summary = {source: round(total, 2) for source, total in source_totals.items()}
        logger.info(f"Generated income sources summary for {year}-{month:02d}: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating income sources summary for {year}-{month:02d}: {e}", exc_info=True)
        return {}

def get_yearly_summary(year: int) -> Dict[str, float]:
    """
    Calculates total yearly expenses, income, and net profit/loss.
    """
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # Sum all daily expenses for the year
        all_daily_expenses_year = get_daily_expenses_by_date_range(start_date, end_date)
        total_yearly_daily_expenses = sum(expense.amount for expense in all_daily_expenses_year)

        # Sum all fixed costs for the year (Annual, Monthly, One-Off, Initial Investment)
        all_fixed_costs_year = get_fixed_costs_by_date_range(start_date, end_date)
        total_yearly_fixed_costs = sum(cost.amount_eur for cost in all_fixed_costs_year)

        total_yearly_expenses = total_yearly_daily_expenses + total_yearly_fixed_costs

        all_income_year = get_income_by_date_range(start_date, end_date)
        # Calculate total yearly income dynamically from tours and transfers revenue
        total_yearly_income = sum(inc.tours_revenue_eur + inc.transfers_revenue_eur for inc in all_income_year)

        net_yearly_profit = total_yearly_income - total_yearly_expenses

        summary = {
            "total_yearly_expenses": round(total_yearly_expenses, 2),
            "total_yearly_income": round(total_yearly_income, 2),
            "net_yearly_profit": round(net_yearly_profit, 2)
        }
        logger.info(f"Generated yearly summary for {year}: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating yearly summary for {year}: {e}", exc_info=True)
        return {}

def get_global_summary() -> Dict[str, float]:
    """
    Calculates total global expenses, income, and net profit/loss across all records.
    """
    try:
        # Sum all daily expenses
        all_daily_expenses = get_all_daily_expenses()
        total_global_daily_expenses = sum(expense.amount for expense in all_daily_expenses)

        # Sum all fixed costs (all frequencies)
        all_fixed_costs = get_all_fixed_costs()
        total_global_fixed_costs = sum(cost.amount_eur for cost in all_fixed_costs)

        total_global_expenses = total_global_daily_expenses + total_global_fixed_costs

        all_income = get_all_income()
        # Calculate total income dynamically from tours and transfers revenue
        total_global_income = sum(inc.tours_revenue_eur + inc.transfers_revenue_eur for inc in all_income)

        net_global_profit = total_global_income - total_global_expenses

        summary = {
            "total_global_expenses": round(total_global_expenses, 2),
            "total_global_income": round(total_global_income, 2),
            "net_global_profit": round(net_global_profit, 2)
        }
        logger.info(f"Generated global summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error generating global summary: {e}", exc_info=True)
        return {}
