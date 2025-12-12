"""
Authentication middleware for protecting admin routes.
Student routes use their own authentication via dependencies.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from fastapi import status


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect admin routes.
    Only /admin/login.html and /api/auth/* are allowed without admin auth.
    Student routes (/student/*) handle their own auth via dependencies.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Allow public routes
        public_paths = [
            "/admin/login.html",
            "/api/auth/login",
            "/api/auth/logout",
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        # Check if path is public
        is_public = any(request.url.path.startswith(path) for path in public_paths)
        
        # Check if it's an API auth endpoint (admin auth)
        if request.url.path.startswith("/api/auth/"):
            is_public = True
        
        # Student routes handle their own auth via dependencies - let them through
        # The /api/student/* endpoints use require_student_auth dependency
        if request.url.path.startswith("/student") or request.url.path.startswith("/api/student"):
            response = await call_next(request)
            return response
        
        # SMS webhook should be public
        if request.url.path.startswith("/api/sms"):
            response = await call_next(request)
            return response
        
        # If public, allow access
        if is_public:
            response = await call_next(request)
            return response
        
        # Check if accessing admin routes
        if request.url.path.startswith("/admin") or request.url.path.startswith("/api/admin"):
            # Check session for admin auth
            if not request.session.get("authenticated"):
                # If it's an API request, return 401 JSON
                if request.url.path.startswith("/api/"):
                    return JSONResponse(
                        {"detail": "Not authenticated"},
                        status_code=status.HTTP_401_UNAUTHORIZED
                    )
                # Otherwise redirect to login
                return RedirectResponse(url="/admin/login.html", status_code=302)
        
        # Continue with request
        response = await call_next(request)
        return response
