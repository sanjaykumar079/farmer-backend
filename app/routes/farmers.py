# app/routes/farmers.py
from fastapi import APIRouter, HTTPException, UploadFile, Form, File, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import uuid
from datetime import datetime
from app.services.supabase_client import supabase
from app.services.ai_service import get_ai_response, analyze_image
from app.models.query import QueryCreate, QueryResponse
from app.utils.validators import validate_file_type, validate_file_size

router = APIRouter()
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000, description="Query text between 10-1000 characters")
    language: str = Field(default="en", pattern="^(en|hi|te)$", description="Language code: en, hi, or te")
    crop_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    urgency: str = Field(default="medium", pattern="^(low|medium|high)$")

class QuerySubmission(BaseModel):
    farmer_id: str = Field(..., description="Authenticated user ID")
    query_text: str = Field(..., min_length=10, max_length=1000)
    crop_type: Optional[str] = None
    location: Optional[str] = None
    urgency: str = "medium"
    image_url: Optional[str] = None

@router.post("/query", response_model=dict)
async def submit_query(query: QueryRequest):
    """
    Submit a farming query and get AI-powered response
    """
    try:
        logger.info(f"Processing query in {query.language}: {query.text[:50]}...")
        
        # Get AI response in the requested language
        ai_response = await get_ai_response(
            query=query.text,
            language=query.language,
            crop_type=query.crop_type,
            location=query.location
        )
        
        # Store query in database for analytics (optional)
        query_record = {
            "id": str(uuid.uuid4()),
            "query_text": query.text,
            "language": query.language,
            "crop_type": query.crop_type,
            "location": query.location,
            "urgency": query.urgency,
            "ai_response": ai_response["response"],
            "confidence_score": ai_response.get("confidence", 0.0),
            "created_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        # Save to database (handle errors gracefully)
        try:
            result = supabase.table("farmer_queries").insert(query_record).execute()
            logger.info(f"Query saved to database with ID: {query_record['id']}")
        except Exception as db_error:
            logger.error(f"Failed to save query to database: {str(db_error)}")
            # Continue anyway - don't fail the request for database issues
        
        return {
            "success": True,
            "query_id": query_record["id"],
            "response": ai_response["response"],
            "language": query.language,
            "confidence": ai_response.get("confidence", 0.0),
            "suggestions": ai_response.get("suggestions", []),
            "timestamp": query_record["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Error processing farmer query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to process your query",
                "error_type": "processing_error",
                "suggestion": "Please try again with a simpler question"
            }
        )

@router.post("/query-with-image")
async def submit_query_with_image(
    query_text: str = Form(..., min_length=10, max_length=1000),
    language: str = Form(default="en", regex="^(en|hi|te)$"),
    crop_type: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    urgency: str = Form(default="medium", regex="^(low|medium|high)$"),
    image: Optional[UploadFile] = File(None)
):
    """
    Submit a farming query with optional image attachment
    """
    try:
        image_analysis = None
        image_url = None
        
        # Process image if provided
        if image:
            # Validate image
            if not validate_file_type(image.filename, allowed_types=['jpg', 'jpeg', 'png', 'webp']):
                raise HTTPException(status_code=400, detail="Invalid file type. Use JPG, PNG, or WebP")
            
            if not validate_file_size(image.size, max_size_mb=5):
                raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
            
            # Read image content
            image_content = await image.read()
            
            # Upload to storage
            file_path = f"farmer-queries/{uuid.uuid4()}_{image.filename}"
            storage_result = supabase.storage.from_("farmer-images").upload(file_path, image_content)
            
            if storage_result.get("error"):
                logger.error(f"Failed to upload image: {storage_result['error']}")
                raise HTTPException(status_code=500, detail="Failed to upload image")
            
            # Get public URL
            image_url = supabase.storage.from_("farmer-images").get_public_url(file_path).get("publicURL")
            
            # Analyze image with AI
            image_analysis = await analyze_image(image_content, language)
            
            logger.info(f"Image uploaded and analyzed: {file_path}")
        
        # Combine text query with image analysis
        combined_query = query_text
        if image_analysis:
            combined_query += f"\n\nImage analysis: {image_analysis['description']}"
        
        # Get AI response
        ai_response = await get_ai_response(
            query=combined_query,
            language=language,
            crop_type=crop_type,
            location=location,
            has_image=image is not None,
            image_analysis=image_analysis
        )
        
        # Create comprehensive response
        response_data = {
            "success": True,
            "query_id": str(uuid.uuid4()),
            "response": ai_response["response"],
            "language": language,
            "confidence": ai_response.get("confidence", 0.0),
            "image_url": image_url,
            "image_analysis": image_analysis,
            "suggestions": ai_response.get("suggestions", []),
            "recommended_actions": ai_response.get("actions", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query with image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to process your query with image",
                "error_type": "processing_error"
            }
        )

@router.get("/query-history/{farmer_id}")
async def get_query_history(
    farmer_id: str,
    limit: int = 10,
    offset: int = 0,
    language: Optional[str] = None
):
    """
    Get farmer's query history with pagination
    """
    try:
        query_builder = supabase.table("farmer_queries").select("*")
        
        # Filter by farmer_id if authentication is implemented
        # query_builder = query_builder.eq("farmer_id", farmer_id)
        
        if language:
            query_builder = query_builder.eq("language", language)
        
        result = query_builder.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "queries": result.data,
            "total": len(result.data),
            "has_more": len(result.data) == limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching query history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch query history"
        )

@router.get("/popular-topics")
async def get_popular_topics(language: str = "en"):
    """
    Get popular farming topics for quick access
    """
    topics_by_language = {
        "en": [
            {"id": 1, "title": "Crop Disease Diagnosis", "icon": "🦠", "category": "health"},
            {"id": 2, "title": "Pest Control Solutions", "icon": "🐛", "category": "protection"},
            {"id": 3, "title": "Irrigation Management", "icon": "💧", "category": "water"},
            {"id": 4, "title": "Soil Health Testing", "icon": "🌱", "category": "soil"},
            {"id": 5, "title": "Harvest Timing", "icon": "🌾", "category": "harvest"},
            {"id": 6, "title": "Weather Impact", "icon": "🌤️", "category": "weather"}
        ],
        "hi": [
            {"id": 1, "title": "फसल रोग निदान", "icon": "🦠", "category": "health"},
            {"id": 2, "title": "कीट नियंत्रण समाधान", "icon": "🐛", "category": "protection"},
            {"id": 3, "title": "सिंचाई प्रबंधन", "icon": "💧", "category": "water"},
            {"id": 4, "title": "मिट्टी स्वास्थ्य परीक्षण", "icon": "🌱", "category": "soil"},
            {"id": 5, "title": "फसल का समय", "icon": "🌾", "category": "harvest"},
            {"id": 6, "title": "मौसम का प्रभाव", "icon": "🌤️", "category": "weather"}
        ],
        "te": [
            {"id": 1, "title": "పంట వ్యాధి నిర్ధారణ", "icon": "🦠", "category": "health"},
            {"id": 2, "title": "కీటకాల నియంత్రణ పరిష్కారాలు", "icon": "🐛", "category": "protection"},
            {"id": 3, "title": "నీటిపారుదల నిర్వహణ", "icon": "💧", "category": "water"},
            {"id": 4, "title": "మట్టి ఆరోగ్య పరీక్ష", "icon": "🌱", "category": "soil"},
            {"id": 5, "title": "కోత సమయం", "icon": "🌾", "category": "harvest"},
            {"id": 6, "title": "వాతావరణ ప్రభావం", "icon": "🌤️", "category": "weather"}
        ]
    }
    
    return {
        "success": True,
        "language": language,
        "topics": topics_by_language.get(language, topics_by_language["en"])
    }