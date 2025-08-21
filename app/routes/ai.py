from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.services.disease_detection import predict_disease
from app.services.chatbot import get_chatbot_response
from app.services.tts_service import text_to_speech
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/disease-detect")
async def disease_detect(
    image: UploadFile = File(...),
    additional_info: str = Form(None)
):
    """
    Detect plant disease from uploaded image
    """
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (max 10MB)
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Get prediction
        prediction_result = predict_disease(contents)
        
        # Add additional context if provided
        if additional_info and prediction_result.get("prediction"):
            enhanced_response = f"""
            **Disease Analysis:** {prediction_result['prediction']} 
            (Confidence: {prediction_result['confidence']:.2%})
            
            **Your Additional Info:** {additional_info}
            
            **Recommendations:** {prediction_result.get('recommendations', 'Consult agricultural expert.')}
            """
            prediction_result['enhanced_response'] = enhanced_response
            
        return {
            "success": True,
            "result": prediction_result,
            "filename": image.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disease detection error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@router.post("/chatbot")
def chatbot(query: str):
    response = get_chatbot_response(query)
    return {"chatbot_response": response}

@router.post("/tts")
def tts(text: str):
    audio_url = text_to_speech(text)
    return {"audio_url": audio_url}