# app/routes/translations.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
import os
from pathlib import Path

router = APIRouter()

# Translation storage - in production, use database or external service
TRANSLATIONS = {
    "en": {
        "farmer_responses": {
            "greeting": "Hello! I'm here to help with your farming questions.",
            "disease_detected": "I've detected a potential {disease} in your crop. Here's what you should do:",
            "healthy_crop": "Your crop looks healthy! Keep up the good work.",
            "need_more_info": "I need more information to help you better. Can you provide more details about:",
            "treatment_success": "The treatment should show results within {days} days.",
            "follow_up": "Please check back in {days} days and let me know how it's going."
        },
        "officer_templates": {
            "acknowledgment": "Thank you for submitting your query. I'm reviewing it now.",
            "request_details": "To provide better assistance, please provide:",
            "treatment_plan": "Based on your description, here's my recommended treatment plan:",
            "follow_up_required": "Please follow up in {days} days with photos of progress.",
            "success_confirmation": "Great to hear the treatment is working! Continue with the current approach."
        }
    },
    "hi": {
        "farmer_responses": {
            "greeting": "नमस्ते! मैं आपके खेती के सवालों में मदद के लिए यहां हूं।",
            "disease_detected": "मैंने आपकी फसल में संभावित {disease} का पता लगाया है। आपको यह करना चाहिए:",
            "healthy_crop": "आपकी फसल स्वस्थ दिख रही है! अच्छा काम जारी रखें।",
            "need_more_info": "आपकी बेहतर मदद के लिए मुझे अधिक जानकारी चाहिए। क्या आप इसके बारे में और विवरण दे सकते हैं:",
            "treatment_success": "उपचार {days} दिनों के भीतर परिणाम दिखाना चाहिए।",
            "follow_up": "कृपया {days} दिनों में वापस जांच करें और मुझे बताएं कि कैसा चल रहा है।"
        },
        "officer_templates": {
            "acknowledgment": "आपकी समस्या भेजने के लिए धन्यवाद। मैं इसकी समीक्षा कर रहा हूं।",
            "request_details": "बेहतर सहायता प्रदान करने के लिए, कृपया प्रदान करें:",
            "treatment_plan": "आपके विवरण के आधार पर, यहां मेरी सुझावित उपचार योजना है:",
            "follow_up_required": "कृपया {days} दिनों में प्रगति की तस्वीरों के साथ फॉलो अप करें।",
            "success_confirmation": "यह सुनकर खुशी हुई कि उपचार काम कर रहा है! वर्तमान दृष्टिकोण जारी रखें।"
        }
    },
    "te": {
        "farmer_responses": {
            "greeting": "నమస్కారం! మీ వ్యవసాయ ప్రశ్నలలో సహాయం చేయడానికి నేను ఇక్కడ ఉన్నాను.",
            "disease_detected": "మీ పంటలో సంభావ్య {disease} ను గుర్తించాను. మీరు ఇలా చేయాలి:",
            "healthy_crop": "మీ పంట ఆరోగ్యంగా కనిపిస్తోంది! మంచి పని కొనసాగించండి.",
            "need_more_info": "మీకు మెరుగైన సహాయం అందించడానికి నాకు మరింత సమాచారం అవసరం. మీరు దీని గురించి మరిన్ని వివరాలను అందించగలరా:",
            "treatment_success": "చికిత్స {days} రోజుల్లో ఫలితాలు చూపాలి.",
            "follow_up": "దయచేసి {days} రోజుల్లో తిరిగి తనిఖీ చేసి, ఎలా జరుగుతుందో నాకు తెలియజేయండి."
        },
        "officer_templates": {
            "acknowledgment": "మీ ప్రశ్న పంపినందుకు ధన్యవాదాలు. నేను దానిని ఇప్పుడు సమీక్షిస్తున్నాను.",
            "request_details": "మెరుగైన సహాయాన్ని అందించడానికి, దయచేసి అందించండి:",
            "treatment_plan": "మీ వివరణ ఆధారంగా, ఇదిగో నా సిఫార్సు చేసిన చికిత్స ప్రణాళిక:",
            "follow_up_required": "దయచేసి {days} రోజుల్లో పురోగతి ఫోటోలతో తిరిగి సంప్రదించండి.",
            "success_confirmation": "చికిత్స పనిచేస్తుందని విని సంతోషం! ప్రస్తుత విధానాన్ని కొనసాగించండి."
        }
    }
}

@router.get("/")
def get_all_languages():
    """Get all available languages"""
    return {
        "available_languages": list(TRANSLATIONS.keys()),
        "total_languages": len(TRANSLATIONS)
    }

@router.get("/{language}")
def get_translations(language: str):
    """Get translations for a specific language"""
    if language not in TRANSLATIONS:
        raise HTTPException(
            status_code=404, 
            detail=f"Language '{language}' not supported. Available languages: {list(TRANSLATIONS.keys())}"
        )
    
    return {
        "language": language,
        "translations": TRANSLATIONS[language]
    }

@router.get("/{language}/farmer")
def get_farmer_responses(language: str):
    """Get AI response templates for farmers in specified language"""
    if language not in TRANSLATIONS:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return TRANSLATIONS[language]["farmer_responses"]

@router.get("/{language}/officer")  
def get_officer_templates(language: str):
    """Get response templates for officers in specified language"""
    if language not in TRANSLATIONS:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return TRANSLATIONS[language]["officer_templates"]

@router.post("/{language}/translate")
def translate_text(language: str, text: str, category: str = "general"):
    """
    Translate text to specified language using templates
    This is a basic implementation - in production, use proper translation service
    """
    if language not in TRANSLATIONS:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    # Simple keyword-based translation (enhance with proper NLP)
    templates = TRANSLATIONS[language]
    
    # Check if text matches any predefined templates
    if category in templates:
        for key, template in templates[category].items():
            if key.lower() in text.lower():
                return {
                    "original": text,
                    "translated": template,
                    "language": language,
                    "category": category,
                    "template_used": key
                }
    
    # If no template matches, return original (implement proper translation here)
    return {
        "original": text,
        "translated": text,  # Fallback to original
        "language": language,
        "category": category,
        "template_used": None,
        "note": "No translation template found, using original text"
    }