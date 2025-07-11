# app/api/routes.py
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from datetime import datetime
from sqlalchemy.orm import Session # Import Session
from fastapi.security import OAuth2PasswordRequestForm # For login endpoint

# Import the individual routers (these will need updates to use get_db dependency)
from .routers import fixed_costs
from .routers import daily_expenses
from .routers import income
from .routers import summary

# Import database functions and the get_db dependency
from app import database # Keep this for general database module access if needed
from app.database import get_db, create_all_tables # Import create_all_tables
from app.config import settings # Import your settings

# Get a logger for this module
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TUK'N'ROLL Business Management API",
    description="API for managing business expenses, costs, and income.",
    version="1.0.0"
)

# Configure Jinja2Templates to serve HTML files
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the routers
# IMPORTANT: These routers will need to be updated to accept a db: Session dependency
app.include_router(fixed_costs.router)
app.include_router(daily_expenses.router)
app.include_router(income.router)
app.include_router(summary.router)

# --- Database Initialization on Startup ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")
    # Create database tables if they don't exist
    database.create_all_tables()

    # Initialize cash on hand if it's a fresh DB
    db_session = next(get_db()) # Get a session for startup tasks
    try:
        # Check if cash_on_hand table is empty or needs initialization
        # This is a simple check; a more robust migration system might be needed for production
        from app.database import get_cash_on_hand_balance, set_initial_cash_on_hand
        current_cash = get_cash_on_hand_balance(db_session)
        # If the balance is 0.0 and it's a new entry (no doc_id from a loaded state), initialize
        if current_cash.balance == 0.0 and current_cash.doc_id is None:
             set_initial_cash_on_hand(db_session, 0.0)
             logger.info("Cash on hand initialized to 0.0 during startup.")
    except Exception as e:
        logger.error(f"Error during cash on hand initialization at startup: {e}", exc_info=True)
    finally:
        db_session.close()


# --- HTML Endpoints ---
# These endpoints will now receive the 'db' dependency.
@app.get("/", response_class=HTMLResponse, summary="Serve the main dashboard HTML page")
async def read_root(request: Request, db: Session = Depends(get_db)): # Inject DB session
    logger.info("Serving dashboard_content.html")
    # Example: You might fetch summary data here and pass it to the template
    # summary_data = database.get_global_summary(db)
    return templates.TemplateResponse("dashboard_content.html", {"request": request, "datetime": datetime})

@app.get("/register-expenses", response_class=HTMLResponse, summary="Serve the expense registration page")
async def register_expenses_page(request: Request, db: Session = Depends(get_db)): # Inject DB session
    logger.info("Serving register_expenses.html")
    return templates.TemplateResponse("register_expenses.html", {"request": request, "datetime": datetime})

@app.get("/register-income", response_class=HTMLResponse, summary="Serve the income registration page")
async def register_income_page(request: Request, db: Session = Depends(get_db)): # Inject DB session
    logger.info("Serving register_income.html")
    return templates.TemplateResponse("register_income.html", {"request": request, "datetime": datetime})

@app.get("/data-management", response_class=HTMLResponse, summary="Serve the data management page")
async def data_management_page(request: Request, db: Session = Depends(get_db)): # Inject DB session
    logger.info("Serving data_management.html")
    return templates.TemplateResponse("data_management.html", {"request": request, "datetime": datetime})

# Add a simple health check endpoint
@app.get("/health", summary="Health check endpoint")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}

# --- Authentication Endpoint (Placeholder for Production/Development Auth) ---
# This endpoint will handle login for non-demo environments.
@app.post("/login/token") # Example path, adjust as per your actual login endpoint
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # This block will be for production/development authentication.
    # The demo-specific login logic will be added later on the 'demo' branch.
    logger.info(f"Attempted login for user '{form_data.username}' in {settings.APP_ENV} environment.")

    # IMPORTANT: Replace this placeholder with your actual production authentication logic.
    # This would typically involve:
    # 1. Querying your actual user database (using the 'db' session).
    # 2. Hashing passwords and verifying credentials.
    # 3. Generating a proper JWT (JSON Web Token) for authentication.
    # 4. Returning the access token.

    # Example placeholder for production auth (replace with your real logic):
    # user = authenticate_user_from_db(db, form_data.username, form_data.password)
    # if not user:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # access_token = create_access_token(data={"sub": user.username}) # You'd need a function for this
    # return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Production authentication logic not yet implemented. Please replace this placeholder.",
    )
