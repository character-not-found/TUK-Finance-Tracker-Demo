# app/api/routes.py
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routers import fixed_costs, daily_expenses, income, summary
from app.database import get_db, create_all_tables, get_cash_on_hand_balance, set_initial_cash_on_hand
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

class ForceHTTPSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "x-forwarded-proto" in request.headers and request.headers["x-forwarded-proto"] == "https":
            request.scope["scheme"] = "https"
        response = await call_next(request)
        return response

app = FastAPI(
    title="Cash-On-Hand Business Manager Demo API",
    description="API for managing business expenses, costs, and income in a demo environment.",
    version="1.0.0",
    forwarded_allow_ips=["*"]
)

app.add_middleware(ForceHTTPSMiddleware)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(fixed_costs.router)
app.include_router(daily_expenses.router)
app.include_router(income.router)
app.include_router(summary.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")
    create_all_tables()
    logger.info(f"FastAPI is starting with APP_ENV: {settings.APP_ENV}")

    db_session = SessionLocal()
    try:
        initial_balance = get_cash_on_hand_balance(db_session)
        if initial_balance is None:
            set_initial_cash_on_hand(db_session, 1000.00)
            logger.info("Initial cash on hand balance set to 1000.00 EUR.")
        else:
            logger.info(f"Cash on hand balance already exists: {initial_balance.balance:.2f} EUR.")
    finally:
        db_session.close()

async def get_current_user_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning("Attempted access to protected route without access token.")
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Not authenticated",
            headers={"Location": "/login"}
        )
    # In a real app, you would validate this token (e.g., JWT verification)
    # For this demo, we just check its presence.
    if access_token != "demo_access_token_for_employer":
        logger.warning(f"Invalid access token: {access_token}")
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Invalid authentication token",
            headers={"Location": "/login"}
        )
    return access_token


# --- HTML Endpoints ---
@app.get("/login", response_class=HTMLResponse, summary="Serve the login page")
async def login_page(request: Request):
    logger.info("Serving login.html")
    return templates.TemplateResponse("login.html", {"request": request, "datetime": datetime})

@app.get("/", response_class=HTMLResponse, summary="Serve the main dashboard HTML page")
async def read_root(request: Request, db: Session = Depends(get_db), token: str = Depends(get_current_user_token)):
    logger.info("Serving dashboard_content.html")
    return templates.TemplateResponse("dashboard_content.html", {"request": request, "datetime": datetime})

@app.get("/register-expenses", response_class=HTMLResponse, summary="Serve the expense registration page")
async def register_expenses_page(request: Request, db: Session = Depends(get_db), token: str = Depends(get_current_user_token)):
    logger.info("Serving register_expenses.html")
    return templates.TemplateResponse("register_expenses.html", {"request": request, "datetime": datetime})

@app.get("/register-income", response_class=HTMLResponse, summary="Serve the income registration page")
async def register_income_page(request: Request, db: Session = Depends(get_db), token: str = Depends(get_current_user_token)):
    logger.info("Serving register_income.html")
    return templates.TemplateResponse("register_income.html", {"request": request, "datetime": datetime})

@app.get("/data-management", response_class=HTMLResponse, summary="Serve the data management page")
async def data_management_page(request: Request, db: Session = Depends(get_db), token: str = Depends(get_current_user_token)):
    logger.info("Serving data_management.html")
    return templates.TemplateResponse("data_management.html", {"request": request, "datetime": datetime})

@app.get("/health", summary="Health check endpoint")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}

# --- Authentication Endpoint ---
@app.post("/login/token")
async def login_for_access_token(
    response: Response, form_data: OAuth2PasswordRequestForm = Depends()
):  
    if settings.APP_ENV == "demo":
        if (
            form_data.username == settings.DEMO_USERNAME
            and form_data.password == settings.DEMO_PASSWORD
        ):
            access_token = "demo_access_token_for_employer"
            expires_at = datetime.now() + timedelta(hours=1)
            response.set_cookie(
                key="access_token",
                value=access_token,
                expires=expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                httponly=True,
                samesite="lax",
                secure=False,
                path="/"
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

@app.post("/logout")
async def logout(response: Response):
    logger.info("Logout endpoint accessed. Clearing access token cookie.")
    response.set_cookie(
        key="access_token",
        value="",
        expires=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    return {"message": "Logged out successfully"}
