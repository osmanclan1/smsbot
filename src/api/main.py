"""
FastAPI main application with Mangum handler for Lambda.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets

from api.routes import sms, admin, trigger, auth, student_auth, student
from api.middleware.auth import AuthMiddleware

app = FastAPI(title="SMS Bot API", version="1.0.0")

# Session middleware (must be added before auth middleware)
# Generate a secret key for sessions
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_urlsafe(32))
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=86400,  # 24 hours
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (protects admin routes)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(student_auth.router, prefix="/api/student/auth", tags=["student-auth"])
app.include_router(student.router, prefix="/api/student", tags=["student"])
app.include_router(sms.router, prefix="/api/sms", tags=["sms"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(trigger.router, prefix="/api/admin", tags=["trigger"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SMS Bot API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/debug/aws")
async def debug_aws():
    """Debug endpoint to check AWS configuration."""
    import os
    import boto3
    
    profile = os.getenv('AWS_PROFILE') or 'rise-admin4'
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        # Try to access DynamoDB
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table('smsbot-conversations')
        table.load()
        
        return {
            "status": "ok",
            "profile": profile,
            "region": region,
            "account": identity.get('Account'),
            "user": identity.get('Arn'),
            "table_status": "accessible"
        }
    except Exception as e:
        return {
            "status": "error",
            "profile": profile,
            "region": region,
            "error": str(e)
        }


# Serve admin dashboard (for local development)
# In Lambda, static files should be served via S3 + CloudFront
admin_dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "admin", "dist")
admin_src_path = os.path.join(os.path.dirname(__file__), "..", "..", "admin", "src")

# Check if dist exists (built files), otherwise fall back to src for dev
if os.path.exists(admin_dist_path):
    try:
        # Mount admin dist directory (production build)
        app.mount("/admin", StaticFiles(directory=admin_dist_path, html=True), name="admin")
        
        @app.get("/admin")
        async def admin_index():
            """Serve admin dashboard."""
            return FileResponse(os.path.join(admin_dist_path, "index.html"))
            
        @app.get("/admin/login.html")
        async def admin_login():
            """Serve login page."""
            return FileResponse(os.path.join(admin_dist_path, "login.html"))
    except Exception as e:
        print(f"Warning: Could not mount admin dashboard from dist: {e}")
        pass
elif os.path.exists(admin_src_path):
    try:
        # Fallback to src directory (development)
        app.mount("/admin", StaticFiles(directory=admin_src_path, html=True), name="admin")
        
        @app.get("/admin")
        async def admin_index():
            """Serve admin dashboard."""
            return FileResponse(os.path.join(admin_src_path, "index.html"))
            
        @app.get("/admin/login.html")
        async def admin_login():
            """Serve login page."""
            return FileResponse(os.path.join(admin_src_path, "login.html"))
    except Exception as e:
        print(f"Warning: Could not mount admin dashboard: {e}")
        pass  # Skip if can't mount (e.g., in Lambda)


# Serve student portal (for local development)
student_dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "student", "dist")
student_src_path = os.path.join(os.path.dirname(__file__), "..", "..", "student", "src")

# Check if dist exists (built files), otherwise fall back to src for dev
if os.path.exists(student_dist_path):
    try:
        # Mount student dist directory (production build)
        app.mount("/student", StaticFiles(directory=student_dist_path, html=True), name="student")
        
        @app.get("/student")
        async def student_index():
            """Serve student portal."""
            return FileResponse(os.path.join(student_dist_path, "index.html"))
            
        @app.get("/student/login.html")
        async def student_login():
            """Serve student login page."""
            return FileResponse(os.path.join(student_dist_path, "login.html"))
    except Exception as e:
        print(f"Warning: Could not mount student portal from dist: {e}")
        pass
elif os.path.exists(student_src_path):
    try:
        # Fallback to src directory (development)
        app.mount("/student", StaticFiles(directory=student_src_path, html=True), name="student")
        
        @app.get("/student")
        async def student_index():
            """Serve student portal."""
            return FileResponse(os.path.join(student_src_path, "index.html"))
            
        @app.get("/student/login.html")
        async def student_login():
            """Serve student login page."""
            return FileResponse(os.path.join(student_src_path, "login.html"))
    except Exception as e:
        print(f"Warning: Could not mount student portal: {e}")
        pass


# Lambda handler using Mangum
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # For local development without mangum
    handler = None
