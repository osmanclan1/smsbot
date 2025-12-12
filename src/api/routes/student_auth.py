"""
Student authentication routes - simple username/password login.
"""

import os
import secrets
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from starlette.requests import Request
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from storage.dynamodb import DynamoDBService

router = APIRouter()

# Simple password hashing (using bcrypt if available, otherwise basic check)
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except:
            return False
    else:
        # Simple comparison for development (NOT SECURE for production)
        return plain_password == hashed_password


def hash_password(password: str) -> str:
    """Hash a password."""
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    else:
        # Plain text for development (NOT SECURE for production)
        return password


# Make hash_password available to DynamoDB service
__all__ = ['router', 'hash_password', 'verify_password']


@router.post("/register")
async def register(request: Request, credentials: RegisterRequest):
    """
    Register a new student account.
    """
    db = DynamoDBService()
    
    # Check if username already exists
    existing = db.get_student_by_username(credentials.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create student account
    student_id = db.create_student_account(
        username=credentials.username,
        password=credentials.password,
        email=credentials.email,
        name=credentials.name
    )
    
    # Auto-login after registration
    request.session["student_authenticated"] = True
    request.session["student_username"] = credentials.username
    request.session["student_id"] = student_id
    
    return JSONResponse({
        "status": "success",
        "message": "Registration successful",
        "student_id": student_id,
        "username": credentials.username
    })


@router.post("/login")
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint for students. Creates a session cookie.
    """
    db = DynamoDBService()
    
    # Get student account
    student = db.get_student_by_username(credentials.username)
    if not student:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    stored_password = student.get('password_hash') or student.get('password')
    if not verify_password(credentials.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create session
    request.session["student_authenticated"] = True
    request.session["student_username"] = credentials.username
    request.session["student_id"] = student.get('student_id') or student.get('username')
    
    return JSONResponse({
        "status": "success",
        "message": "Login successful",
        "username": credentials.username,
        "student_id": student.get('student_id')
    })


@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint. Clears session.
    """
    request.session.pop("student_authenticated", None)
    request.session.pop("student_username", None)
    request.session.pop("student_id", None)
    return JSONResponse({
        "status": "success",
        "message": "Logout successful"
    })


@router.get("/me")
async def get_current_student(request: Request):
    """
    Get current authenticated student info.
    """
    if not request.session.get("student_authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = request.session.get("student_username")
    student_id = request.session.get("student_id")
    
    # Get full student profile
    db = DynamoDBService()
    student = db.get_student_by_username(username)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    
    # Return student info (without password)
    return {
        "authenticated": True,
        "username": username,
        "student_id": student_id,
        "name": student.get('name'),
        "email": student.get('email'),
        "created_at": student.get('created_at')
    }


def require_student_auth(request: Request):
    """
    Dependency to require student authentication.
    """
    if not request.session.get("student_authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "username": request.session.get("student_username"),
        "student_id": request.session.get("student_id")
    }
