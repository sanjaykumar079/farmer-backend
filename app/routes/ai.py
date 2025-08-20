from fastapi import APIRouter, UploadFile
from app.services.disease_detection import predict_disease
from app.services.chatbot import get_chatbot_response
from app.services.tts_service import text_to_speech

router = APIRouter()

@router.post("/disease-detect")
async def disease_detect(image: UploadFile):
    contents = await image.read()
    prediction = predict_disease(contents)
    return {"disease_prediction": prediction}

@router.post("/chatbot")
def chatbot(query: str):
    response = get_chatbot_response(query)
    return {"chatbot_response": response}

@router.post("/tts")
def tts(text: str):
    audio_url = text_to_speech(text)
    return {"audio_url": audio_url}
