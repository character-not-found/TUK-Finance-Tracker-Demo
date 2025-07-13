# app/api/routes.py
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response # Import Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from datetime import datetime, timedelta # Import timedelta for cookie expiration
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

# Import the individual routers
from .routers import fixed_costs
from .routers import daily_expenses
from .routers import income
from .routers import summary

# Import database functions and the get_db dependency
from app import database
from app.database import get_db, create_all_tables
from app.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cash-On-Hand Finance Tracker API",
    description="API for managing business expenses, costs, and income.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(fixed_costs.router)
app.include_router(daily_expenses.router)
app.include_router(income.router)
app.include_router(summary.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")
    database.create_all_tables()

    db_session = next(get_db())
    try:
        from app.database import get_cash_on_hand_balance, set_initial_cash_on_hand
        current_cash = get_cash_on_hand_balance(db_session)
        if current_cash.balance == 0.0 and current_cash.doc_id is None:
             set_initial_cash_on_hand(db_session, 0.0)
             logger.info("Cash on hand initialized to 0.0 during startup.")
    except Exception as e:
        logger.error(f"Error during cash on hand initialization at startup: {e}", exc_info=True)
    finally:
        db_session.close()


# --- HTML Endpoints ---
@app.get("/login", response_class=HTMLResponse, summary="Serve the login page")
async def login_page(request: Request):
    logger.info("Serving login.html")
    return templates.TemplateResponse("login.html", {"request": request, "datetime": datetime})

@app.get("/", response_class=HTMLResponse, summary="Serve the main dashboard HTML page")
async def read_root(request: Request, db: Session = Depends(get_db)):
    # Check for access token in cookies
    access_token = request.cookies.get("access_token")

    if settings.APP_ENV == "demo" and not access_token:
        logger.info("No access token found in demo environment, redirecting to login.")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    logger.info("Serving dashboard_content.html")
    return templates.TemplateResponse("dashboard_content.html", {"request": request, "datetime": datetime})

@app.get("/register-expenses", response_class=HTMLResponse, summary="Serve the expense registration page")
async def register_expenses_page(request: Request, db: Session = Depends(get_db)):
    logger.info("Serving register_expenses.html")
    return templates.TemplateResponse("register_expenses.html", {"request": request, "datetime": datetime})

@app.get("/register-income", response_class=HTMLResponse, summary="Serve the income registration page")
async def register_income_page(request: Request, db: Session = Depends(get_db)):
    logger.info("Serving register_income.html")
    return templates.TemplateResponse("register_income.html", {"request": request, "datetime": datetime})

@app.get("/data-management", response_class=HTMLResponse, summary="Serve the data management page")
async def data_management_page(request: Request, db: Session = Depends(get_db)):
    logger.info("Serving data_management.html")
    return templates.TemplateResponse("data_management.html", {"request": request, "datetime": datetime})

@app.get("/health", summary="Health check endpoint")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}

# --- Authentication Endpoint ---
@app.post("/login/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None, db: Session = Depends(get_db)): # Add Response parameter
    if settings.APP_ENV == "demo":
        if form_data.username == settings.DEMO_USERNAME and form_data.password == settings.DEMO_PASSWORD:
            logger.info(f"Demo user '{form_data.username}' logged in successfully.")
            access_token = "demo_access_token_for_employer" # Static token for demo

            # Set the access token as an HttpOnly cookie
            # For demo, let's make it last for 1 hour (3600 seconds)
            expires_at = datetime.now() + timedelta(hours=1)
            response.set_cookie(
                key="access_token",
                value=access_token,
                expires=expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT"), # Format for cookie expires
                httponly=True, # Prevent JavaScript access
                samesite="lax", # Protect against CSRF
                secure=True, # Only send over HTTPS (important for production)
                path="/" # Available across the entire application
            )
            return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password for demo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        logger.warning(f"Attempted login for user '{form_data.username}' in {settings.APP_ENV} environment.")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Production authentication logic not yet implemented. Please replace this placeholder.",
        )

# New: Logout endpoint to clear the cookie
@app.post("/logout")
async def logout(response: Response):
    logger.info("Logout endpoint accessed. Clearing access token cookie.")
    response.set_cookie(
        key="access_token",
        value="", # Empty value
        expires=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"), # Expire immediately
        httponly=True,
        samesite="lax",
        secure=True,
        path="/"
    )
    return {"message": "Logged out successfully"}
