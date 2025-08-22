# app/api/routes.py
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import fixed_costs, daily_expenses, income, summary
from app.database import get_db, create_all_tables, get_cash_on_hand_balance, set_initial_cash_on_hand
from app.config import settings
from app.database import SessionLocal
from app.api.auth_utils import create_access_token, verify_password, get_password_hash, get_current_user, get_current_user_optional

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

origins = [
    "https://demotuk.duckdns.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(fixed_costs.router)
app.include_router(daily_expenses.router)
app.include_router(income.router)
app.include_router(summary.router)

PROTECTED_HTML_PATHS = [
    "/",
    "/register-expenses",
    "/register-income",
    "/data-management"
]

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

# --- HTML Endpoints ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED and request.url.path in PROTECTED_HTML_PATHS:
        logger.warning("Unauthorized access to root path, redirecting to login.")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return exc

@app.get("/login", response_class=HTMLResponse, summary="Serve the login page")
async def login_page(request: Request):
    logger.info("Serving login.html")
    return templates.TemplateResponse("login.html", {"request": request, "datetime": datetime})

@app.get("/", response_class=HTMLResponse, summary="Serve the main dashboard HTML page")
async def read_root(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    logger.info("Serving dashboard_content.html")
    return templates.TemplateResponse("dashboard_content.html", {"request": request, "datetime": datetime})

@app.get("/register-expenses", response_class=HTMLResponse, summary="Serve the expense registration page")
async def register_expenses_page(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    logger.info("Serving register_expenses.html")
    return templates.TemplateResponse("register_expenses.html", {"request": request, "datetime": datetime})

@app.get("/register-income", response_class=HTMLResponse, summary="Serve the income registration page")
async def register_income_page(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    logger.info("Serving register_income.html")
    return templates.TemplateResponse("register_income.html", {"request": request, "datetime": datetime})

@app.get("/data-management", response_class=HTMLResponse, summary="Serve the data management page")
async def data_management_page(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    logger.info("Serving data_management.html")
    return templates.TemplateResponse("data_management.html", {"request": request, "datetime": datetime})

@app.get("/health", summary="Health check endpoint")
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {"status": "ok"}

@app.get("/session_check", summary="Existing session check endpoint")
async def session_check_endpoint(user = Depends(get_current_user_optional)):
    if user:
        logger.info("Session check successful. User authenticated.")
        return {"status": "ok", "authenticated": True}
    else:
        logger.warning("Session check failed. No authenticated user.")
        return {"status": "ok", "authenticated": False}

# --- Authentication Endpoint ---
@app.post("/login/token")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    hashed_password_from_db = get_password_hash(settings.DEMO_PASSWORD)
    
    if (
        form_data.username == settings.DEMO_USERNAME
        and verify_password(form_data.password, hashed_password_from_db)
    ):
        access_token = create_access_token(
            data={"sub": form_data.username}
        )
        
        expires_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
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
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
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
