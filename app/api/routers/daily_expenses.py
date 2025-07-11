# app/api/routers/daily_expenses.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging # Import logging
from sqlalchemy.orm import Session # Import Session
from fastapi import Depends # Ensure Depends is imported
from app.database import get_db # Import the database dependency

# Relative imports from the 'app' package
from ... import database
from ...models import DailyExpense, PaymentMethod # Ensure DailyExpense and PaymentMethod are imported

# Get a logger for this router
logger = logging.getLogger(__name__)

# Create an API router specific to daily expenses
router = APIRouter(
    prefix="/daily-expenses", # Updated prefix
    tags=["Daily Expenses"], # Updated tag
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[DailyExpense], summary="Retrieve all daily expenses") # Updated summary
async def get_daily_expenses(db: Session = Depends(get_db)): # Renamed function
    """
    Retrieves a list of all daily expense entries from the database.
    """
    logger.info("Attempting to retrieve all daily expenses.")
    expenses = database.get_all_daily_expenses(db) # Updated function call
    logger.info(f"Successfully retrieved {len(expenses)} daily expenses.")
    return expenses

@router.get("/{doc_id}", response_model=DailyExpense, summary="Retrieve a specific daily expense by ID") # Updated summary
async def get_daily_expense_by_id(doc_id: int, db: Session = Depends(get_db)): # Renamed function
    """
    Retrieves a single daily expense entry by its document ID.
    Raises a 404 error if the expense is not found.
    """
    logger.info(f"Attempting to retrieve daily expense with ID: {doc_id}")
    expense = database.get_daily_expense_by_id(db, doc_id) # Updated table
    if not expense:
        logger.warning(f"Daily expense with ID {doc_id} not found.")
        raise HTTPException(status_code=404, detail="Daily expense not found")
    logger.info(f"Successfully retrieved daily expense with ID: {doc_id}")
    return expense

@router.post("/", response_model=DailyExpense, status_code=status.HTTP_201_CREATED, summary="Create a new daily expense") # Updated summary
async def create_daily_expense(daily_expense: DailyExpense, db: Session = Depends(get_db)): # Renamed function and parameter
    """
    Adds a new daily expense entry to the database.
    """
    logger.info(f"Attempting to create a new daily expense: {daily_expense.description}")
    try:
        new_expense = database.add_daily_expense(db, daily_expense) # CORRECTED FUNCTION CALL
        logger.info(f"Daily expense created successfully with ID: {new_expense.doc_id}")
        return new_expense
    except Exception as e:
        logger.error(f"Failed to create daily expense: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error adding daily expense: {e}")

@router.put("/{doc_id}", response_model=DailyExpense, summary="Update an existing daily expense by ID")
async def update_daily_expense_api(doc_id: int, updates: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Updates an existing daily expense entry by its document ID.
    """
    logger.info(f"Attempting to update daily expense with ID {doc_id} with updates: {updates}")

    # Ensure payment_method is converted to Enum if present in updates
    if 'payment_method' in updates and isinstance(updates['payment_method'], str):
        try:
            updates['payment_method'] = PaymentMethod(updates['payment_method'])
        except ValueError:
            logger.warning(f"Invalid payment_method provided for daily expense update: {updates['payment_method']}")
            raise HTTPException(status_code=400, detail="Invalid payment_method provided")

    success = database.update_daily_expense(db, doc_id, updates)
    if not success:
        logger.warning(f"Daily expense with ID {doc_id} not found or update failed.")
        raise HTTPException(status_code=404, detail=f"Daily expense with ID {doc_id} not found or update failed.")
    # Retrieve the updated expense to return it
    updated_expense = database.get_daily_expense_by_id(db, doc_id)
    if not updated_expense: # Should not happen if update was successful
        logger.error(f"Failed to retrieve updated daily expense with ID {doc_id} after successful update operation.")
        raise HTTPException(status_code=500, detail="Failed to retrieve updated daily expense.")
    logger.info(f"Daily expense with ID {doc_id} updated successfully.")
    return updated_expense

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a daily expense by ID") # Updated summary
async def delete_daily_expense_api(doc_id: int, db: Session = Depends(get_db)): # Renamed function
    """
    Deletes a daily expense entry by its document ID.
    """
    logger.info(f"Attempting to delete daily expense with ID: {doc_id}")
    success = database.delete_daily_expense(db, doc_id)
    if not success:
        logger.warning(f"Daily expense with ID {doc_id} not found or deletion failed.")
        raise HTTPException(status_code=404, detail="Daily expense not found")
    logger.info(f"Daily expense with ID {doc_id} deleted successfully.")
    return {"message": "Daily expense deleted successfully"}
    