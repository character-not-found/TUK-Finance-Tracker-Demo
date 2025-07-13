# scripts/populate_demo_data.py
import random
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal, create_all_tables, get_cash_on_hand_balance, set_initial_cash_on_hand
from app.models import FixedCost, DailyExpense, Income, CostFrequency, ExpenseCategory, PaymentMethod
from app.database import (
    add_fixed_cost, add_daily_expense, add_income,
    clear_all_fixed_costs, clear_all_daily_expenses, clear_all_income, reset_cash_on_hand_balance # Import new functions
)

# Configure a basic logger for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_random_date(start_date: datetime, end_date: datetime) -> str:
    """Generates a random date string (YYYY-MM-DD) within a given range."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.strftime("%Y-%m-%d")

def generate_random_amount(min_val: float, max_val: float) -> float:
    """Generates a random float amount, rounded to two decimal places."""
    return round(random.uniform(min_val, max_val), 2)

def generate_random_fixed_cost() -> FixedCost:
    """Generates a random FixedCost entry."""
    categories = [e for e in ExpenseCategory]
    frequencies = [f for f in CostFrequency if f != CostFrequency.INITIAL_INVESTMENT]
    payment_methods = [pm for pm in PaymentMethod]

    cost_date = generate_random_date(datetime.now() - timedelta(days=365), datetime.now())
    amount = generate_random_amount(50.0, 1000.0)
    description = random.choice([
        "Office Rent", "Software Subscription", "Vehicle Insurance",
        "Annual License Fee", "Marketing Campaign", "Garage Rental"
    ])
    category = random.choice(categories)
    cost_frequency = random.choice(frequencies)
    recipient = random.choice(["Vendor A", "Supplier B", "Service Co.", "Landlord LLC"])
    payment_method = random.choice(payment_methods)

    return FixedCost(
        amount_eur=amount,
        description=description,
        cost_frequency=cost_frequency,
        category=category,
        recipient=recipient,
        cost_date=cost_date,
        payment_method=payment_method
    )

def generate_random_daily_expense() -> DailyExpense:
    """Generates a random DailyExpense entry."""
    categories = [e for e in ExpenseCategory if e not in [
        ExpenseCategory.INSURANCE, ExpenseCategory.LICENSES, ExpenseCategory.VEHICLE_PURCHASE, ExpenseCategory.MARKETING
    ]]
    payment_methods = [pm for pm in PaymentMethod]

    cost_date = generate_random_date(datetime.now() - timedelta(days=90), datetime.now())
    amount = generate_random_amount(5.0, 150.0)
    description = random.choice([
        "Lunch", "Diesel refill", "Small repair", "Office supplies",
        "Snacks for trip", "Electricity bill (daily portion)", "Tuk wash"
    ])
    category = random.choice(categories)
    payment_method = random.choice(payment_methods)

    return DailyExpense(
        amount=amount,
        description=description,
        category=category,
        cost_date=cost_date,
        payment_method=payment_method
    )

def generate_random_income() -> Income:
    """Generates a random Income entry."""
    income_date = generate_random_date(datetime.now() - timedelta(days=90), datetime.now())
    tours_revenue = generate_random_amount(20.0, 500.0)
    transfers_revenue = generate_random_amount(10.0, 300.0)
    hours_worked = round(random.uniform(2.0, 10.0), 2)

    return Income(
        income_date=income_date,
        tours_revenue_eur=tours_revenue,
        transfers_revenue_eur=transfers_revenue,
        hours_worked=hours_worked
    )

def populate_fake_data(num_fixed_costs: int = 5, num_daily_expenses: int = 30, num_income_entries: int = 20):
    """
    Populates the database with fake data, clearing existing entries first.
    Args:
        num_fixed_costs (int): Number of fixed cost entries to generate.
        num_daily_expenses (int): Number of daily expense entries to generate.
        num_income_entries (int): Number of income entries to generate.
    """
    logger.info("Starting fake data population...")
    db_session = SessionLocal()
    try:
        create_all_tables() # Ensure tables exist
        logger.info("Database tables ensured to be created.")

        # --- NEW: Clear existing data ---
        logger.info("Clearing existing data from tables...")
        clear_all_fixed_costs(db_session)
        clear_all_daily_expenses(db_session)
        clear_all_income(db_session)
        reset_cash_on_hand_balance(db_session, 1000.0) # Reset cash on hand to initial value
        logger.info("Existing data cleared and cash on hand reset.")
        # --- END NEW ---

        # Add Fixed Costs
        logger.info(f"Generating {num_fixed_costs} fake fixed costs...")
        for _ in range(num_fixed_costs):
            fixed_cost = generate_random_fixed_cost()
            add_fixed_cost(db_session, fixed_cost)
        logger.info(f"Finished generating {num_fixed_costs} fixed costs.")

        # Add Daily Expenses
        logger.info(f"Generating {num_daily_expenses} fake daily expenses...")
        for _ in range(num_daily_expenses):
            daily_expense = generate_random_daily_expense()
            add_daily_expense(db_session, daily_expense)
        logger.info(f"Finished generating {num_daily_expenses} daily expenses.")

        # Add Income Entries
        logger.info(f"Generating {num_income_entries} fake income entries...")
        for _ in range(num_income_entries):
            income_entry = generate_random_income()
            add_income(db_session, income_entry)
        logger.info(f"Finished generating {num_income_entries} income entries.")

        logger.info("Fake data population complete.")

    except Exception as e:
        logger.error(f"An error occurred during fake data population: {e}", exc_info=True)
    finally:
        db_session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    populate_fake_data(
        num_fixed_costs=10,
        num_daily_expenses=50,
        num_income_entries=30
    )
