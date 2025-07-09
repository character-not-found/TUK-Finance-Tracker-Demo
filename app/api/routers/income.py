# app/api/routers/income.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging # Import logging

# Relative imports from the 'app' package
from ... import database
from ...models import Income

# Get a logger for this router
logger = logging.getLogger(__name__)

# Create an API router specific to income
router = APIRouter(
    prefix="/income",
    tags=["Income"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Income], summary="Retrieve all income entries")
async def get_income():
    """
    Retrieves a list of all income entries from the database.
    """
    logger.info("Attempting to retrieve all income entries.")
    incomes = database.get_all_income()
    logger.info(f"Successfully retrieved {len(incomes)} income entries.")
    return incomes

@router.get("/{doc_id}", response_model=Income, summary="Retrieve a specific income entry by ID")
async def get_income_by_id(doc_id: int):
    """
    Retrieves a single income entry by its document ID.
    Raises a 404 error if the income is not found.
    """
    logger.info(f"Attempting to retrieve income entry with ID: {doc_id}")
    inc = database.get_income_by_id(doc_id) # Use the database function
    if not inc:
        logger.warning(f"Income entry with ID {doc_id} not found.")
        raise HTTPException(status_code=404, detail=f"Income entry with ID {doc_id} not found")
    logger.info(f"Successfully retrieved income entry with ID: {doc_id}")
    return inc

@router.post("/", response_model=Income, status_code=status.HTTP_201_CREATED, summary="Create a new income entry")
async def create_income(income: Income):
    """
    Adds a new income entry to the database.
    """
    logger.info(f"Attempting to create a new income entry for date: {income.income_date}")
    try:
        new_income = database.add_income(income)
        logger.info(f"Income entry created successfully with ID: {new_income.doc_id}")
        return new_income
    except Exception as e:
        logger.error(f"Failed to create income entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error adding income: {e}")

@router.put("/{doc_id}", response_model=Income, summary="Update an existing income entry by ID")
async def update_income_api(doc_id: int, updates: Dict[str, Any]):
    """
    Updates an existing income entry by its document ID.
    """
    logger.info(f"Attempting to update income entry with ID {doc_id} with updates: {updates}")
    success = database.update_income(doc_id, updates)
    if not success:
        logger.warning(f"Income entry with ID {doc_id} not found or update failed.")
        raise HTTPException(status_code=404, detail=f"Income entry with ID {doc_id} not found or update failed.")
    # Retrieve the updated income to return it
    updated_income = database.get_income_by_id(doc_id) # Use the database function
    if not updated_income: # Should not happen if update was successful
        logger.error(f"Failed to retrieve updated income entry with ID {doc_id} after successful update operation.")
        raise HTTPException(status_code=500, detail="Failed to retrieve updated income entry.")
    logger.info(f"Income entry with ID {doc_id} updated successfully.")
    return updated_income

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an income entry by ID")
async def delete_income_api(doc_id: int):
    """
    Deletes an income entry by its document ID.
    """
    logger.info(f"Attempting to delete income entry with ID: {doc_id}")
    success = database.delete_income(doc_id)
    if not success:
        logger.warning(f"Income entry with ID {doc_id} not found or deletion failed.")
        raise HTTPException(status_code=404, detail=f"Income entry with ID {doc_id} not found or deletion failed.")
    logger.info(f"Income entry with ID {doc_id} deleted successfully.")
    return {"message": "Income deleted successfully"}
