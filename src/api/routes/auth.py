"""
Authentication routes for admin dashboard.
"""

import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

router = APIRouter()

# Simple password hashing (using bcrypt if available, otherwise basic check)
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


class LoginRequest(BaseModel):
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    if HAS_BCRYPT:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    else:
        # Simple comparison for development (NOT SECURE for production)
        return plain_password == hashed_password


def get_admin_credentials():
    """Get admin credentials from environment variables."""
    username = os.getenv('ADMIN_USERNAME', 'admin')
    password = os.getenv('ADMIN_PASSWORD', 'admin')
    
    if HAS_BCRYPT and password.startswith('$2b$'):
        # Password is already hashed
        return username, password
    elif HAS_BCRYPT:
        # Hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return username, hashed.decode('utf-8')
    else:
        # Plain text (development only)
        return username, password


@router.post("/login")
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint. Creates a session cookie.
    """
    username, password_hash = get_admin_credentials()
    
    if credentials.username != username:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    request.session["authenticated"] = True
    request.session["username"] = username
    
    return JSONResponse({
        "status": "success",
        "message": "Login successful",
        "username": username
    })


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint. Clears session.
    """
    request.session.clear()
    return JSONResponse({
        "status": "success",
        "message": "Logout successful"
    })


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "authenticated": True,
        "username": request.session.get("username")
    }


def require_auth(request: Request):
    """
    Dependency to require authentication.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session.get("username")
