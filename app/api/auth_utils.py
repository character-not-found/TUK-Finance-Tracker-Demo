# app/api/auth_utils.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(request: Request):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    auth_header = request.headers.get("Authorization")
    token_to_check = None
    if auth_header and auth_header.startswith("Bearer "):
        token_to_check = auth_header.split(" ")[1]

    if not token_to_check:
        token_to_check = request.cookies.get("access_token")

    if not token_to_check:
        logger.warning("Token not found in header or cookie.")
        raise credentials_exception

    try:
        payload = jwt.decode(token_to_check, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Invalid token payload: missing 'sub'")
            raise credentials_exception
        return username
    except JWTError as e:
        logger.warning(f"JWT decoding failed: {e}")
        raise credentials_exception
    
async def get_current_user_optional(request: Request):
    token_to_check = None
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token_to_check = auth_header.split(" ")[1]

    if not token_to_check:
        token_to_check = request.cookies.get("access_token")

    if not token_to_check:
        logger.info("Optional token check: No token found. Returning None.")
        return None

    try:
        payload = jwt.decode(token_to_check, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Optional token check: Invalid token payload. Returning None.")
            return None
        return username
    except JWTError:
        logger.warning("Optional token check: JWT decoding failed. Returning None.")
        return None