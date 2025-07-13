# app/api/routers/income.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any # Keep Dict, Any for potential future uses, but List[Income] is what we return
import logging
from sqlalchemy.orm import Session

from app import database
from app.database import get_db
from app.models import Income # Ensure this Income model has attributes for tours_revenue_eur and transfers_revenue_eur

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/income",
    tags=["Income"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[Income], summary="Retrieve all income entries")
async def get_income(db: Session = Depends(get_db)) -> List[Income]:
    """
    Retrieves a list of all income entries from the database and calculates
    the daily_total_eur for each entry.
    """
    logger.info("Attempting to retrieve all income entries.")
    
    # Fetch income entries from the database
    incomes_from_db = database.get_all_income(db)
    
    # Calculate daily_total_eur for each income entry
    processed_incomes = []
    for income_item in incomes_from_db:
        # Ensure tours_revenue_eur and transfers_revenue_eur are treated as numbers
        # and handle cases where they might be None
        tours_revenue = income_item.tours_revenue_eur if income_item.tours_revenue_eur is not None else 0.0
        transfers_revenue = income_item.transfers_revenue_eur if income_item.transfers_revenue_eur is not None else 0.0
        
        income_item.daily_total_eur = tours_revenue + transfers_revenue
        processed_incomes.append(income_item)

    logger.info(f"Successfully retrieved and processed {len(processed_incomes)} income entries.")
    return processed_incomes

@router.get("/{doc_id}", response_model=Income, summary="Retrieve a specific income entry by ID")
async def get_income_by_id(doc_id: int, db: Session = Depends(get_db)) -> Income:
    """
    Retrieves a single income entry by its document ID and calculates
    the daily_total_eur for it.
    Raises a 404 error if the income is not found.
    """
    logger.info(f"Attempting to retrieve income entry with ID: {doc_id}")
    
    inc = database.get_income_by_id(db, doc_id)
    if not inc:
        logger.warning(f"Income entry with ID {doc_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Income entry with ID {doc_id} not found.")
    
    # Calculate daily_total_eur for the single income entry
    tours_revenue = inc.tours_revenue_eur if inc.tours_revenue_eur is not None else 0.0
    transfers_revenue = inc.transfers_revenue_eur if inc.transfers_revenue_eur is not None else 0.0
    
    inc.daily_total_eur = tours_revenue + transfers_revenue
    
    logger.info(f"Successfully retrieved and processed income entry with ID: {doc_id}.")
    return inc

@router.post("/", response_model=Income, status_code=status.HTTP_201_CREATED, summary="Create a new income entry")
async def create_income_api(income: Income, db: Session = Depends(get_db)) -> Income:
    """
    Creates a new income entry in the database.
    """
    logger.info(f"Attempting to create a new income entry: {income.dict()}")
    # The 'daily_total_eur' doesn't need to be part of the creation payload
    # as it's calculated on retrieval. Ensure your database model doesn't expect it for creation.
    # If income.daily_total_eur is passed in the payload, remove it before creating.
    income_data = income.dict(exclude_unset=True) # Use exclude_unset to avoid passing unset fields
    if 'daily_total_eur' in income_data:
        del income_data['daily_total_eur'] # Remove it if present, as it's a calculated field

    new_income = database.create_income(db, **income_data)
    
    # After creation, you might want to fetch and return the full object with daily_total_eur calculated
    # Or, if the frontend doesn't need it immediately after creation, you can skip this part.
    # For consistency, let's retrieve it again to include the calculated field.
    if new_income:
        tours_revenue = new_income.tours_revenue_eur if new_income.tours_revenue_eur is not None else 0.0
        transfers_revenue = new_income.transfers_revenue_eur if new_income.transfers_revenue_eur is not None else 0.0
        new_income.daily_total_eur = tours_revenue + transfers_revenue
    
    logger.info(f"Income entry created successfully with ID: {new_income.doc_id}")
    return new_income


@router.put("/{doc_id}", response_model=Income, summary="Update an existing income entry")
async def update_income_api(doc_id: int, income: Income, db: Session = Depends(get_db)) -> Income:
    """
    Updates an existing income entry identified by its document ID.
    Raises a 404 error if the income is not found.
    """
    logger.info(f"Attempting to update income entry with ID: {doc_id} with data: {income.dict()}")
    
    updates = income.dict(exclude_unset=True)
    if 'daily_total_eur' in updates:
        del updates['daily_total_eur'] # Don't try to update a calculated field directly

    success = database.update_income(db, doc_id, updates)
    if not success:
        logger.warning(f"Income entry with ID {doc_id} not found or update failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Income entry with ID {doc_id} not found or update failed.")
    
    updated_income = database.get_income_by_id(db, doc_id)
    if not updated_income:
        logger.error(f"Failed to retrieve updated income entry with ID {doc_id} after successful update operation.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated income entry.")
    
    # Calculate daily_total_eur for the updated income entry
    tours_revenue = updated_income.tours_revenue_eur if updated_income.tours_revenue_eur is not None else 0.0
    transfers_revenue = updated_income.transfers_revenue_eur if updated_income.transfers_revenue_eur is not None else 0.0
    updated_income.daily_total_eur = tours_revenue + transfers_revenue
    
    logger.info(f"Income entry with ID {doc_id} updated successfully.")
    return updated_income

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an income entry by ID")
async def delete_income_api(doc_id: int, db: Session = Depends(get_db)):
    """
    Deletes an income entry by its document ID.
    """
    logger.info(f"Attempting to delete income entry with ID: {doc_id}")
    success = database.delete_income(db, doc_id)
    if not success:
        logger.warning(f"Income entry with ID {doc_id} not found or deletion failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Income entry with ID {doc_id} not found or deletion failed.")
    logger.info(f"Income entry with ID {doc_id} deleted successfully.")