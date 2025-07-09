# app/api/routers/fixed_costs.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging # Import logging

# Relative imports from the 'app' package
from ... import database
from ...models import FixedCost, PaymentMethod # Ensure FixedCost and PaymentMethod are imported

# Get a logger for this router
logger = logging.getLogger(__name__)

# Create an API router specific to fixed costs
router = APIRouter(
    prefix="/fixed-costs",
    tags=["Fixed Costs"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[FixedCost], summary="Retrieve all fixed costs")
async def get_fixed_costs():
    """
    Retrieves a list of all fixed cost entries from the database.
    """
    logger.info("Attempting to retrieve all fixed costs.")
    costs = database.get_all_fixed_costs()
    logger.info(f"Successfully retrieved {len(costs)} fixed costs.")
    return costs

@router.get("/{doc_id}", response_model=FixedCost, summary="Retrieve a specific fixed cost by ID")
async def get_fixed_cost_by_id(doc_id: int):
    """
    Retrieves a single fixed cost entry by its document ID.
    Raises a 404 error if the cost is not found.
    """
    logger.info(f"Attempting to retrieve fixed cost with ID: {doc_id}")
    cost = database.get_fixed_cost_by_id(doc_id) # Use the database function
    if not cost:
        logger.warning(f"Fixed cost with ID {doc_id} not found.")
        raise HTTPException(status_code=404, detail=f"Fixed cost with ID {doc_id} not found")
    logger.info(f"Successfully retrieved fixed cost with ID: {doc_id}")
    return cost

@router.post("/", response_model=FixedCost, status_code=status.HTTP_201_CREATED, summary="Create a new fixed cost")
async def create_fixed_cost(fixed_cost: FixedCost):
    """
    Adds a new fixed cost entry to the database.
    """
    logger.info(f"Attempting to create a new fixed cost: {fixed_cost.description}")
    try:
        new_cost = database.add_fixed_cost(fixed_cost)
        logger.info(f"Fixed cost created successfully with ID: {new_cost.doc_id}")
        return new_cost
    except Exception as e:
        logger.error(f"Failed to create fixed cost: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error adding fixed cost: {e}")

@router.put("/{doc_id}", response_model=FixedCost, summary="Update an existing fixed cost by ID")
async def update_fixed_cost_api(doc_id: int, updates: Dict[str, Any]):
    """
    Updates an existing fixed cost entry by its document ID.
    """
    logger.info(f"Attempting to update fixed cost with ID {doc_id} with updates: {updates}")
    
    # Ensure payment_method is converted to Enum if present in updates
    if 'payment_method' in updates and isinstance(updates['payment_method'], str):
        try:
            updates['payment_method'] = PaymentMethod(updates['payment_method'])
        except ValueError:
            logger.warning(f"Invalid payment_method provided for fixed cost update: {updates['payment_method']}")
            raise HTTPException(status_code=400, detail="Invalid payment_method provided")

    success = database.update_fixed_cost(doc_id, updates)
    if not success:
        logger.warning(f"Fixed cost with ID {doc_id} not found or update failed.")
        raise HTTPException(status_code=404, detail=f"Fixed cost with ID {doc_id} not found or update failed.")
    # Retrieve the updated cost to return it
    updated_cost = database.get_fixed_cost_by_id(doc_id) # Use the database function
    if not updated_cost: # Should not happen if update was successful
        logger.error(f"Failed to retrieve updated fixed cost with ID {doc_id} after successful update operation.")
        raise HTTPException(status_code=500, detail="Failed to retrieve updated fixed cost.")
    logger.info(f"Fixed cost with ID {doc_id} updated successfully.")
    return updated_cost

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a fixed cost by ID")
async def delete_fixed_cost_api(doc_id: int):
    """
    Deletes a fixed cost entry by its document ID.
    """
    logger.info(f"Attempting to delete fixed cost with ID: {doc_id}")
    success = database.delete_fixed_cost(doc_id)
    if not success:
        logger.warning(f"Fixed cost with ID {doc_id} not found or deletion failed.")
        raise HTTPException(status_code=404, detail=f"Fixed cost with ID {doc_id} not found or deletion failed.")
    logger.info(f"Fixed cost with ID {doc_id} deleted successfully.")
    return {"message": "Fixed cost deleted successfully"}
