# app/utils/logging_config.py
import logging
import sys
from datetime import datetime

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create custom formatter
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors for different log levels"""
        
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        RESET = '\033[0m'
        
        def format(self, record):
            if record.levelname in self.COLORS:
                record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            return super().format(record)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler for errors
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    error_handler.setFormatter(file_formatter)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)

# app/utils/validators.py
import re
from typing import List, Optional
import mimetypes

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type based on extension"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in [t.lower() for t in allowed_types]

def validate_file_size(file_size: int, max_size_mb: int = 5) -> bool:
    """Validate file size in MB"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def validate_language_code(language: str) -> bool:
    """Validate language code"""
    return language.lower() in ['en', 'hi', 'te']

def validate_crop_name(crop_name: str) -> bool:
    """Validate crop name (basic validation)"""
    if not crop_name or len(crop_name) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z\s\-\_]+$', crop_name))

def validate_location(location: str) -> bool:
    """Validate location string"""
    if not location or len(location) > 100:
        return False
    return bool(re.match(r'^[a-zA-Z\s\,\-\_\.]+$', location))

# app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.routes.supabase_client import supabase
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes"""
    
    # Routes that don't require authentication
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/health",
        "/translations",
        "/farmers/query",  # Allow public queries for now
        "/farmers/popular-topics"
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip authentication for excluded paths
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Extract token from header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        token = authorization.split(" ")[1]
        
        try:
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Add user info to request state
            request.state.user = user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        return await call_next(request)

# app/models/query.py (Enhanced)
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class QueryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RESOLVED = "resolved"

class LanguageCode(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    TELUGU = "te"

class QueryCreate(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)
    language: LanguageCode = LanguageCode.ENGLISH
    crop_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    farmer_id: Optional[str] = None
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Query text cannot be empty')
        return v.strip()
    
    @validator('crop_type')
    def validate_crop_type(cls, v):
        if v and not v.strip():
            return None
        return v.strip() if v else None

class QueryResponse(BaseModel):
    id: str
    query_text: str
    ai_response: str
    language: LanguageCode
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggestions: List[str] = []
    actions: List[str] = []
    response_type: str
    created_at: datetime
    status: QueryStatus
    
class ImageAnalysis(BaseModel):
    description: str
    recommendations: Optional[str] = None
    detected_issues: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    
class AIResponse(BaseModel):
    response: str
    confidence: float
    suggestions: List[str]
    actions: List[str]
    language: str
    response_type: str
    image_analysis: Optional[ImageAnalysis] = None