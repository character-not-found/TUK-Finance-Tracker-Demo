# app/api/routes.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging # Import logging
from datetime import datetime # Import datetime here

# Import the individual routers
from .routers import fixed_costs
from .routers import daily_expenses
from .routers import income
from .routers import summary

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
app.include_router(fixed_costs.router)
app.include_router(daily_expenses.router)
app.include_router(income.router)
app.include_router(summary.router)

# --- HTML Endpoints ---
@app.get("/", response_class=HTMLResponse, summary="Serve the main dashboard HTML page")
async def read_root(request: Request):
    """
    Serves the 'dashboard_content.html' template, which displays the main dashboard.
    """
    logger.info("Serving dashboard_content.html")
    # Pass datetime to the template context
    return templates.TemplateResponse("dashboard_content.html", {"request": request, "datetime": datetime})

@app.get("/register-expenses", response_class=HTMLResponse, summary="Serve the expense registration page")
async def register_expenses_page(request: Request):
    """
    Serves the 'register_expenses.html' template for adding new expense entries.
    """
    logger.info("Serving register_expenses.html")
    # Pass datetime to the template context
    return templates.TemplateResponse("register_expenses.html", {"request": request, "datetime": datetime})

@app.get("/register-income", response_class=HTMLResponse, summary="Serve the income registration page")
async def register_income_page(request: Request):
    """
    Serves the 'register_income.html' template for adding new income entries.
    """
    logger.info("Serving register_income.html")
    # Pass datetime to the template context
    return templates.TemplateResponse("register_income.html", {"request": request, "datetime": datetime})

@app.get("/data-management", response_class=HTMLResponse, summary="Serve the data management page")
async def data_management_page(request: Request):
    """
    Serves the 'data_management.html' template for managing database entries.
    """
    logger.info("Serving data_management.html")
    # Pass datetime to the template context
    return templates.TemplateResponse("data_management.html", {"request": request, "datetime": datetime})

# Add a simple health check endpoint
@app.get("/health", summary="Health check endpoint")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}
