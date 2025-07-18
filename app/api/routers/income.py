# app/api/routers/income.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging
from sqlalchemy.orm import Session

from app import database
from app.database import get_db
from app.models import Income, AggregatedIncome

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/income",
    tags=["Income"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[AggregatedIncome], summary="Retrieve all aggregated income entries by date")
async def get_aggregated_income(db: Session = Depends(get_db)) -> List[AggregatedIncome]:
    """
    Retrieves a list of all income entries from the database, aggregated by date.
    """
    logger.info("Attempting to retrieve all aggregated income entries.")
    aggregated_incomes = database.get_aggregated_income_by_date(db)
    logger.info(f"Successfully retrieved {len(aggregated_incomes)} aggregated income entries.")
    return aggregated_incomes

@router.get("/all-individual", response_model=List[Income], summary="Retrieve all individual income entries")
async def get_all_individual_income(db: Session = Depends(get_db)) -> List[Income]:
    """
    Retrieves a list of all individual income entries from the database.
    This endpoint is for internal use where non-aggregated data is needed (e.g., calculations).
    """
    logger.info("Attempting to retrieve all individual income entries.")
    incomes_from_db = database.get_all_income(db)
    processed_incomes = []
    for income_item in incomes_from_db:
        tours_revenue = income_item.tours_revenue_eur if income_item.tours_revenue_eur is not None else 0.0
        transfers_revenue = income_item.transfers_revenue_eur if income_item.transfers_revenue_eur is not None else 0.0
        income_item.daily_total_eur = tours_revenue + transfers_revenue
        processed_incomes.append(income_item)
    logger.info(f"Successfully retrieved and processed {len(processed_incomes)} individual income entries.")
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
    income_data = income.dict(exclude_unset=True)
    if 'daily_total_eur' in income_data:
        del income_data['daily_total_eur']

    new_income = database.add_income(db, income=income)
    
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
        del updates['daily_total_eur']

    success = database.update_income(db, doc_id, updates)
    if not success:
        logger.warning(f"Income entry with ID {doc_id} not found or update failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Income entry with ID {doc_id} not found or update failed.")
    
    updated_income = database.get_income_by_id(db, doc_id)
    if not updated_income:
        logger.error(f"Failed to retrieve updated income entry with ID {doc_id} after successful update operation.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated income entry.")
    
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