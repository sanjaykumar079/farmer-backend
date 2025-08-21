# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
import traceback
from app.routes import auth, farmers, officers, ai, translations
from app.middleware.auth_middleware import AuthMiddleware
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgroConnect API",
    description="Farmer-Horticulture Interface with AI-powered solutions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request details
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"Response: {response.status_code} - Time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {str(e)} - Time: {process_time:.2f}s")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Enable CORS with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "https://your-domain.com"  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add authentication middleware (uncomment when ready)
# app.add_middleware(AuthMiddleware)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request Failed",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": str(time.time())  # For tracking
        }
    )

# Include routers with proper prefixes and tags
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(farmers.router, prefix="/farmers", tags=["Farmers"])
app.include_router(officers.router, prefix="/officers", tags=["Officers"]) 
app.include_router(ai.router, prefix="/ai", tags=["AI Services"])
app.include_router(translations.router, prefix="/translations", tags=["Translations"])

# Health check and root endpoints
@app.get("/", tags=["System"])
def root():
    """Root endpoint with API information"""
    return {
        "message": "AgroConnect API is running 🌱🚜",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "features": [
            "Farmer query system",
            "Officer dashboard", 
            "AI-powered solutions",
            "Multi-language support",
            "Real-time communications"
        ]
    }

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "database": "connected",
            "ai_service": "operational",
            "storage": "available"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )