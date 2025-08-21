# app/services/ai_service.py
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import re

logger = logging.getLogger(__name__)

# Multilingual knowledge base for farming
FARMING_KNOWLEDGE = {
    "diseases": {
        "en": {
            "leaf_spot": {
                "symptoms": ["yellow spots on leaves", "brown patches", "wilting"],
                "treatment": "Apply fungicide spray every 7 days. Remove affected leaves. Improve air circulation.",
                "prevention": "Avoid overhead watering, ensure proper spacing between plants."
            },
            "blight": {
                "symptoms": ["dark spots", "yellowing leaves", "plant death"],
                "treatment": "Use copper-based fungicide. Remove infected plants immediately.",
                "prevention": "Crop rotation, avoid wet conditions, resistant varieties."
            },
            "rust": {
                "symptoms": ["orange/brown spots", "leaf drop", "stunted growth"],
                "treatment": "Apply sulfur-based fungicide. Improve drainage.",
                "prevention": "Plant resistant varieties, avoid overhead irrigation."
            }
        },
        "hi": {
            "leaf_spot": {
                "symptoms": ["पत्तियों पर पीले धब्बे", "भूरे पैच", "मुरझाना"],
                "treatment": "हर 7 दिन में फंगीसाइड स्प्रे करें। प्रभावित पत्तियों को हटा दें। हवा का संचार बेहतर करें।",
                "prevention": "ऊपर से पानी देने से बचें, पौधों के बीच उचित दूरी रखें।"
            },
            "blight": {
                "symptoms": ["काले धब्बे", "पत्तियों का पीला होना", "पौधे की मृत्यु"],
                "treatment": "कॉपर आधारित फंगीसाइड का उपयोग करें। संक्रमित पौधों को तुरंत हटा दें।",
                "prevention": "फसल चक्र, गीली स्थितियों से बचें, प्रतिरोधी किस्में।"
            },
            "rust": {
                "symptoms": ["नारंगी/भूरे धब्बे", "पत्ती गिरना", "बौनी वृद्धि"],
                "treatment": "सल्फर आधारित फंगीसाइड लगाएं। जल निकासी में सुधार करें।",
                "prevention": "प्रतिरोधी किस्में लगाएं, ऊपरी सिंचाई से बचें।"
            }
        },
        "te": {
            "leaf_spot": {
                "symptoms": ["ఆకులపై పసుపు మచ్చలు", "గోధుమ రంగు పాచెస్", "వాడిపోవడం"],
                "treatment": "ప్రతి 7 రోజులకు ఫంగిసైడ్ స్ప్రే చేయండి. ప్రభావిత ఆకులను తొలగించండి. గాలి సర్క్యులేషన్ మెరుగుపరచండి.",
                "prevention": "పైనుండి నీరు పోయడం మానండి, మొక్కల మధ్య సరైన దూరం ఉంచండి."
            },
            "blight": {
                "symptoms": ["ముదురు మచ్చలు", "ఆకుల పసుపు రంగు", "మొక్క మరణం"],
                "treatment": "కాపర్ ఆధారిత ఫంగిసైడ్ వాడండి. వ్యాధిగ్రస్త మొక్కలను వెంటనే తొలగించండి.",
                "prevention": "పంట మార్పిడి, తడి పరిస్థితులను నివారించండి, నిరోధక రకాలు."
            },
            "rust": {
                "symptoms": ["నారింజ/గోధుమ మచ్చలు", "ఆకు రాలుట", "కుంగిపోయిన పెరుగుదల"],
                "treatment": "సల్ఫర్ ఆధారిత ఫంగిసైడ్ వేయండి. డ్రైనేజీ మెరుగుపరచండి.",
                "prevention": "నిరోధక రకాలను నాటండి, పైనుండి నీరందించడం మానండి."
            }
        }
    },
    "pests": {
        "en": {
            "aphids": {
                "identification": "Small green/black insects on leaves and stems",
                "treatment": "Use neem oil spray or insecticidal soap. Release ladybugs.",
                "prevention": "Companion planting with marigolds, regular inspection."
            },
            "whiteflies": {
                "identification": "Tiny white flying insects under leaves",
                "treatment": "Yellow sticky traps, neem oil, remove affected leaves.",
                "prevention": "Good air circulation, avoid over-fertilizing with nitrogen."
            }
        },
        "hi": {
            "aphids": {
                "identification": "पत्तियों और तनों पर छोटे हरे/काले कीड़े",
                "treatment": "नीम का तेल स्प्रे या कीटनाशक साबुन का उपयोग करें। लेडीबग्स छोड़ें।",
                "prevention": "गेंदे के साथ साथी रोपण, नियमित निरीक्षण।"
            },
            "whiteflies": {
                "identification": "पत्तियों के नीचे छोटे सफेद उड़ने वाले कीड़े",
                "treatment": "पीले चिपचिपे जाल, नीम का तेल, प्रभावित पत्तियों को हटाएं।",
                "prevention": "अच्छा हवा का संचार, नाइट्रोजन के साथ अधिक उर्वरक से बचें।"
            }
        },
        "te": {
            "aphids": {
                "identification": "ఆకులు మరియు కాండాలపై చిన్న ఆకుపచ్చ/నలుపు కీటకాలు",
                "treatment": "వేప నూనె స్ప్రే లేదా కీటక నాశక సబ్బు వాడండి. లేడీబగ్స్ వదిలించండి.",
                "prevention": "మేరిగోల్డ్స్ తో కంపానియన్ ప్లాంటింగ్, రెగ్యులర్ ఇన్స్పెక్షన్."
            },
            "whiteflies": {
                "identification": "ఆకుల కింద చిన్న తెల్ల ఎగిరే కీటకాలు",
                "treatment": "పసుపు అంటుకునే ట్రాప్స్, వేప నూనె, ప్రభావిత ఆకులను తొలగించండి.",
                "prevention": "మంచి గాలి సర్క్యులేషన్, నైట్రోజన్ తో ఎక్కువ ఎరువు వేయడం మానండి."
            }
        }
    }
}

# Response templates by language
RESPONSE_TEMPLATES = {
    "en": {
        "greeting": "Hello! I'm your AI farming assistant. I'll help you with your agricultural questions.",
        "disease_detected": "Based on your description, this appears to be {disease}. Here's what I recommend:",
        "pest_identified": "I've identified this as a {pest} problem. Here's the treatment plan:",
        "general_advice": "Here's some general advice for your farming question:",
        "need_more_info": "To provide better assistance, I need more details about:",
        "confidence_low": "I'm not entirely certain about this diagnosis. I recommend consulting with a local agricultural expert.",
        "follow_up": "Please monitor the situation and update me in {days} days."
    },
    "hi": {
        "greeting": "नमस्ते! मैं आपका AI कृषि सहायक हूं। मैं आपके कृषि प्रश्नों में मदद करूंगा।",
        "disease_detected": "आपके विवरण के आधार पर, यह {disease} लगता है। यहां मेरी सिफारिश है:",
        "pest_identified": "मैंने इसे {pest} समस्या के रूप में पहचाना है। यहां उपचार योजना है:",
        "general_advice": "आपके कृषि प्रश्न के लिए यहां कुछ सामान्य सलाह है:",
        "need_more_info": "बेहतर सहायता प्रदान करने के लिए, मुझे इसके बारे में और विवरण चाहिए:",
        "confidence_low": "मुझे इस निदान के बारे में पूरी तरह से यकीन नहीं है। मैं स्थानीय कृषि विशेषज्ञ से सलाह लेने की सलाह देता हूं।",
        "follow_up": "कृपया स्थिति की निगरानी करें और {days} दिनों में मुझे अपडेट करें।"
    },
    "te": {
        "greeting": "నమస్కారం! నేను మీ AI వ్యవసాయ సహాయకుడను. మీ వ్యవసాయ ప్రశ్నలలో నేను సహాయం చేస్తాను.",
        "disease_detected": "మీ వివరణ ఆధారంగా, ఇది {disease} గా కనిపిస్తోంది. ఇక్కడ నా సిఫార్సు:",
        "pest_identified": "నేను దీనిని {pest} సమస్యగా గుర్తించాను. ఇక్కడ చికిత్స ప్రణాళిక:",
        "general_advice": "మీ వ్యవసాయ ప్రశ్నకు ఇక్కడ కొంత సాధారణ సలహా:",
        "need_more_info": "మెరుగైన సహాయాన్ని అందించడానికి, దీని గురించి మరిన్ని వివరాలు అవసరం:",
        "confidence_low": "ఈ నిర్ధారణ గురించి నాకు పూర్తి నిశ్చయత లేదు. స్థానిక వ్యవసాయ నిపుణుడిని సంప్రదించాలని నేను సిఫార్సు చేస్తున్నాను.",
        "follow_up": "దయచేసి పరిస్థితిని పర్యవేక్షించండి మరియు {days} రోజుల్లో నాకు అప్‌డేట్ చేయండి।"
    }
}

async def get_ai_response(
    query: str,
    language: str = "en",
    crop_type: Optional[str] = None,
    location: Optional[str] = None,
    has_image: bool = False,
    image_analysis: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate AI response for farmer queries with multilingual support
    """
    try:
        logger.info(f"Processing AI query in {language}: {query[:100]}...")
        
        # Normalize language code
        lang = language.lower() if language.lower() in ['en', 'hi', 'te'] else 'en'
        
        # Get response templates for the language
        templates = RESPONSE_TEMPLATES.get(lang, RESPONSE_TEMPLATES['en'])
        
        # Initialize response structure
        response = {
            "response": "",
            "confidence": 0.7,
            "suggestions": [],
            "actions": [],
            "language": lang,
            "response_type": "general"
        }
        
        # Analyze query content
        query_lower = query.lower()
        
        # Check for disease-related keywords
        disease_keywords = {
            "en": ["yellow", "spots", "brown", "wilting", "dying", "diseased", "fungus", "mold"],
            "hi": ["पीला", "धब्बे", "भूरा", "मुरझाना", "मरना", "रोगग्रस्त", "फंगस"],
            "te": ["పసుపు", "మచ్చలు", "గోధుమ", "వాడిపోవడం", "చనిపోవడం", "వ్యాధిగ్రస్త", "ఫంగస్"]
        }
        
        # Check for pest-related keywords
        pest_keywords = {
            "en": ["insects", "bugs", "pests", "eating", "holes", "aphids", "caterpillars"],
            "hi": ["कीड़े", "कीट", "खाना", "छेद", "एफिड्स", "कैटरपिलर"],
            "te": ["కీటకాలు", "బగ్స్", "తినడం", "రంధ్రాలు", "అఫిడ్స్", "గొంగళి పురుగులు"]
        }
        
        detected_issue = None
        issue_type = None
        
        # Disease detection
        for disease, info in FARMING_KNOWLEDGE["diseases"].get(lang, {}).items():
            for symptom in info["symptoms"]:
                if any(keyword in query_lower for keyword in symptom.lower().split()):
                    detected_issue = disease
                    issue_type = "disease"
                    response["confidence"] = 0.8
                    break
            if detected_issue:
                break
        
        # Pest detection if no disease found
        if not detected_issue:
            for pest, info in FARMING_KNOWLEDGE["pests"].get(lang, {}).items():
                if pest.lower() in query_lower:
                    detected_issue = pest
                    issue_type = "pest"
                    response["confidence"] = 0.8
                    break
        
        # Generate response based on detected issue
        if detected_issue and issue_type:
            if issue_type == "disease":
                disease_info = FARMING_KNOWLEDGE["diseases"][lang][detected_issue]
                response["response"] = templates["disease_detected"].format(disease=detected_issue) + "\n\n"
                response["response"] += f"**{_translate('Treatment', lang)}:** {disease_info['treatment']}\n\n"
                response["response"] += f"**{_translate('Prevention', lang)}:** {disease_info['prevention']}"
                response["response_type"] = "disease_diagnosis"
                
                response["actions"] = [
                    _translate("Apply recommended treatment", lang),
                    _translate("Monitor progress daily", lang),
                    _translate("Remove affected plant parts", lang)
                ]
                
            elif issue_type == "pest":
                pest_info = FARMING_KNOWLEDGE["pests"][lang][detected_issue]
                response["response"] = templates["pest_identified"].format(pest=detected_issue) + "\n\n"
                response["response"] += f"**{_translate('Identification', lang)}:** {pest_info['identification']}\n\n"
                response["response"] += f"**{_translate('Treatment', lang)}:** {pest_info['treatment']}\n\n"
                response["response"] += f"**{_translate('Prevention', lang)}:** {pest_info['prevention']}"
                response["response_type"] = "pest_control"
                
                response["actions"] = [
                    _translate("Apply pest control measures", lang),
                    _translate("Set up monitoring traps", lang),
                    _translate("Check plants regularly", lang)
                ]
        
        else:
            # General farming advice
            response["response"] = templates["general_advice"] + "\n\n"
            
            # Provide context-based advice
            if crop_type:
                crop_advice = _get_crop_specific_advice(crop_type, lang)
                response["response"] += crop_advice + "\n\n"
            
            if location:
                location_advice = _get_location_specific_advice(location, lang)
                response["response"] += location_advice + "\n\n"
            
            # Add image analysis if available
            if image_analysis:
                response["response"] += f"**{_translate('Image Analysis', lang)}:** {image_analysis.get('description', '')}\n\n"
                if image_analysis.get('recommendations'):
                    response["response"] += f"**{_translate('Recommendations', lang)}:** {image_analysis['recommendations']}"
            
            # Generic helpful advice
            generic_advice = _get_generic_advice(query_lower, lang)
            response["response"] += generic_advice
            
            response["confidence"] = 0.6
            response["response_type"] = "general_advice"
        
        # Add follow-up suggestions
        response["suggestions"] = _generate_suggestions(query_lower, lang, detected_issue)
        
        # Add follow-up reminder if confidence is high enough
        if response["confidence"] > 0.7:
            response["response"] += f"\n\n{templates['follow_up'].format(days=7)}"
        elif response["confidence"] < 0.6:
            response["response"] += f"\n\n{templates['confidence_low']}"
        
        logger.info(f"AI response generated with confidence: {response['confidence']}")
        return response
        
    except Exception as e:
        logger.error(f"Error in AI response generation: {str(e)}")
        # Fallback response
        fallback_responses = {
            "en": "I'm sorry, I encountered an error processing your query. Please try rephrasing your question or contact support.",
            "hi": "मुझे खेद है, आपकी समस्या को संसाधित करने में मुझे एक त्रुटि का सामना करना पड़ा। कृपया अपने प्रश्न को दोबारा लिखें या सहायता से संपर्क करें।",
            "te": "క్షమించండి, మీ ప్రశ్నను ప్రాసెస్ చేయడంలో నాకు లోపం ఎదురైంది. దయచేసి మీ ప్రశ్నను మళ్లీ రాయండి లేదా సహాయాన్ని సంప్రదించండి."
        }
        
        return {
            "response": fallback_responses.get(language, fallback_responses["en"]),
            "confidence": 0.1,
            "suggestions": [],
            "actions": [],
            "language": language,
            "response_type": "error",
            "error": True
        }

async def analyze_image(image_content: bytes, language: str = "en") -> Dict[str, Any]:
    """
    Analyze uploaded farming images (placeholder for actual ML model)
    """
    try:
        # Placeholder analysis - in production, use actual ML model
        # This would integrate with services like Google Vision, AWS Rekognition, or custom models
        
        analysis_results = {
            "en": {
                "description": "Image shows healthy green vegetation with some yellowing on lower leaves, possibly indicating nutrient deficiency or natural aging.",
                "recommendations": "Consider soil testing for nutrient levels. Ensure adequate watering and check for signs of pest damage.",
                "detected_issues": ["leaf_yellowing", "possible_nutrient_deficiency"],
                "confidence": 0.75
            },
            "hi": {
                "description": "छवि स्वस्थ हरी वनस्पति दिखाती है जिसमें निचली पत्तियों पर कुछ पीलापन है, संभवतः पोषक तत्वों की कमी या प्राकृतिक उम्र बढ़ने का संकेत है।",
                "recommendations": "पोषक तत्वों के स्तर के लिए मिट्टी परीक्षण पर विचार करें। पर्याप्त पानी सुनिश्चित करें और कीट क्षति के संकेतों की जांच करें।",
                "detected_issues": ["पत्ती पीलापन", "संभावित पोषक कमी"],
                "confidence": 0.75
            },
            "te": {
                "description": "చిత్రం ఆరోగ్యకరమైన ఆకుపచ్చ వృక్షసంపదను చూపిస్తుంది, దిగువ ఆకులపై కొంత పసుపు రంగు ఉంది, బహుశా పోషక లోపం లేదా సహజ వృద్ధాప్యాన్ని సూచిస్తుంది.",
                "recommendations": "పోషక స్థాయిల కోసం మట్టి పరీక్షను పరిగణించండి. తగిన నీరు అందించడాన్ని నిర్ధారించండి మరియు కీటకాల నష్టం యొక్క సంకేతాలను తనిఖీ చేయండి.",
                "detected_issues": ["ఆకు పసుపు రంగు", "సంభావ్య పోషక లోపం"],
                "confidence": 0.75
            }
        }
        
        lang = language.lower() if language.lower() in ['en', 'hi', 'te'] else 'en'
        result = analysis_results.get(lang, analysis_results['en'])
        
        logger.info(f"Image analysis completed for language: {lang}")
        return result
        
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        return {
            "description": "Unable to analyze image at this time",
            "recommendations": "Please try uploading the image again or describe the issue in text",
            "detected_issues": [],
            "confidence": 0.0,
            "error": True
        }

def _translate(text: str, language: str) -> str:
    """Helper function for basic translations"""
    translations = {
        "Treatment": {"hi": "उपचार", "te": "చికిత్స"},
        "Prevention": {"hi": "बचाव", "te": "నివారణ"},
        "Identification": {"hi": "पहचान", "te": "గుర్తింపు"},
        "Image Analysis": {"hi": "छवि विश्लेषण", "te": "చిత్ర విశ్లేషణ"},
        "Recommendations": {"hi": "सिफारिशें", "te": "సిఫార్సులు"},
        "Apply recommended treatment": {"hi": "अनुशंसित उपचार लागू करें", "te": "సిఫార్సు చేయబడిన చికిత్సను వర్తింపజేయండి"},
        "Monitor progress daily": {"hi": "दैनिक प्रगति की निगरानी करें", "te": "రోజువారీ పురోగతిని పర్యవేక్షించండి"},
        "Remove affected plant parts": {"hi": "प्रभावित पौधे के हिस्सों को हटाएं", "te": "ప్రభావిత మొక్క భాగాలను తొలగించండి"},
        "Apply pest control measures": {"hi": "कीट नियंत्रण उपाय लागू करें", "te": "కీటకాల నియంత్రణ చర్యలను వర్తింపజేయండి"},
        "Set up monitoring traps": {"hi": "निगरानी जाल स्थापित करें", "te": "పర్యవేక్షణ ట్రాప్లను ఏర్పాతు చేయండి"},
        "Check plants regularly": {"hi": "नियमित रूप से पौधों की जांच करें", "te": "మొక్కలను క్రమం తప్పకుండా తనిఖీ చేయండి"}
    }
    
    if language in translations.get(text, {}):
        return translations[text][language]
    return text

def _get_crop_specific_advice(crop_type: str, language: str) -> str:
    """Get crop-specific advice"""
    crop_advice = {
        "en": {
            "tomato": "For tomatoes, ensure consistent watering and support with stakes. Watch for blight and hornworms.",
            "wheat": "Wheat requires good drainage and regular fertilization. Monitor for rust and aphids.",
            "rice": "Rice needs consistent water levels and good soil preparation. Watch for blast disease.",
            "cotton": "Cotton requires warm weather and careful pest management, especially for bollworms."
        },
        "hi": {
            "tomato": "टमाटर के लिए, लगातार पानी देना और दांव के साथ सहारा सुनिश्चित करें। ब्लाइट और हॉर्नवॉर्म पर नजर रखें।",
            "wheat": "गेहूं को अच्छी जल निकासी और नियमित उर्वरीकरण की आवश्यकता होती है। जंग और एफिड्स के लिए निगरानी करें।",
            "rice": "चावल को लगातार पानी के स्तर और अच्छी मिट्टी की तैयारी की आवश्यकता होती है। ब्लास्ट रोग पर नजर रखें।",
            "cotton": "कपास को गर्म मौसम और सावधान कीट प्रबंधन की आवश्यकता होती है, विशेष रूप से बॉलवॉर्म के लिए।"
        },
        "te": {
            "tomato": "టమాటాల కోసం, స్థిరమైన నీరు అందించడం మరియు కొట్లతో మద్దతు అందించడాన్ని నిర్ధారించండి. బ్లైట్ మరియు హార్న్‌వార్మ్‌లను గమనించండి.",
            "wheat": "గోధుమలకు మంచి డ్రైనేజీ మరియు క్రమం తప్పకుండా ఎరువులు అవసరం. రస్ట్ మరియు అఫిడ్స్ కోసం పర్యవేక్షించండి.",
            "rice": "బియ్యానికి స్థిరమైన నీటి స్థాయిలు మరియు మంచి నేల తయారీ అవసరం. బ్లాస్ట్ వ్యాధిని గమనించండి.",
            "cotton": "పత్తికి వెచ్చని వాతావరణం మరియు జాగ్రత్తగా పెస్ట్ మేనేజ్‌మెంట్ అవసరం, ముఖ్యంగా బోల్‌వార్మ్‌ల కోసం."
        }
    }
    
    lang = language.lower()
    crop = crop_type.lower()
    
    return crop_advice.get(lang, crop_advice["en"]).get(crop, "")

def _get_location_specific_advice(location: str, language: str) -> str:
    """Get location-specific farming advice"""
    # This would typically integrate with weather APIs and regional farming data
    location_advice = {
        "en": f"For your location in {location}, consider the local climate conditions and seasonal patterns.",
        "hi": f"{location} में आपके स्थान के लिए, स्थानीय जलवायु परिस्थितियों और मौसमी पैटर्न पर विचार करें।",
        "te": f"{location} లో మీ ప్రాంతానికి, స్థానిక వాతావరణ పరిస్థితులు మరియు కాలానుగుణ నమూనాలను పరిగణించండి."
    }
    
    return location_advice.get(language.lower(), location_advice["en"])

def _get_generic_advice(query: str, language: str) -> str:
    """Generate generic farming advice based on query keywords"""
    generic_advice = {
        "en": {
            "water": "Proper watering is crucial - water deeply but less frequently to encourage root growth.",
            "soil": "Healthy soil is the foundation of good farming. Consider soil testing and organic amendments.",
            "fertilizer": "Use balanced fertilizers based on soil test results. Organic options are often beneficial.",
            "weather": "Monitor weather conditions and adjust farming practices accordingly."
        },
        "hi": {
            "water": "उचित पानी देना महत्वपूर्ण है - जड़ों की वृद्धि को प्रोत्साहित करने के लिए गहराई से लेकिन कम बार पानी दें।",
            "soil": "स्वस्थ मिट्टी अच्छी खेती की नींव है। मिट्टी परीक्षण और जैविक संशोधन पर विचार करें।",
            "fertilizer": "मिट्टी परीक्षण परिणामों के आधार पर संतुलित उर्वरक का उपयोग करें। जैविक विकल्प अक्सर फायदेमंद होते हैं।",
            "weather": "मौसम की स्थिति की निगरानी करें और तदनुसार कृषि प्रथाओं को समायोजित करें।"
        },
        "te": {
            "water": "సరైన నీరు అందించడం కీలకం - వేరుల పెరుగుదలను ప్రోత్సహించడానికి లోతుగా కానీ తక్కువ తరచుగా నీరు ఇవ్వండి.",
            "soil": "ఆరోగ్యకరమైన మట్టి మంచి వ్యవసాయానికి పునాది. మట్టి పరీక్ష మరియు సేంద్రీయ సవరణలను పరిగణించండి.",
            "fertilizer": "మట్టి పరీక్ష ఫలితాల ఆధారంగా సమతుల్య ఎరువులను ఉపయోగించండి. సేంద్రీయ ఎంపికలు తరచుగా ప్రయోజనకరంగా ఉంటాయి.",
            "weather": "వాతావరణ పరిస్థితులను పర్యవేక్షించండి మరియు దాని ప్రకారం వ్యవసాయ పద్ధతులను సర్దుబాటు చేయండి."
        }
    }
    
    lang = language.lower()
    advice_dict = generic_advice.get(lang, generic_advice["en"])
    
    for keyword, advice in advice_dict.items():
        if keyword in query:
            return advice
    
    # Default generic advice
    default_advice = {
        "en": "Focus on soil health, proper irrigation, and regular monitoring for the best results.",
        "hi": "सर्वोत्तम परिणामों के लिए मिट्टी के स्वास्थ्य, उचित सिंचाई और नियमित निगरानी पर ध्यान दें।",
        "te": "ఉత్తమ ఫలితాల కోసం మట్టి ఆరోగ్యం, సరైన నీటిపారుదల మరియు క్రమం తప్పకుండా పర్యవేక్షణపై దృష్టి పెట్టండి."
    }
    
    return default_advice.get(lang, default_advice["en"])

def _generate_suggestions(query: str, language: str, detected_issue: str = None) -> List[str]:
    """Generate helpful suggestions based on the query"""
    suggestions = {
        "en": [
            "Consider taking photos of affected areas for better diagnosis",
            "Monitor the situation for 3-5 days before taking action",
            "Consult with local agricultural extension officers",
            "Check soil moisture levels regularly",
            "Keep detailed records of treatments applied"
        ],
        "hi": [
            "बेहतर निदान के लिए प्रभावित क्षेत्रों की तस्वीरें लेने पर विचार करें",
            "कार्रवाई करने से पहले 3-5 दिनों तक स्थिति की निगरानी करें",
            "स्थानीय कृषि विस्तार अधिकारियों से सलाह लें",
            "मिट्टी की नमी के स्तर की नियमित जांच करें",
            "लागू किए गए उपचारों का विस्तृत रिकॉर्ड रखें"
        ],
        "te": [
            "మెరుగైన నిర్ధారణ కోసం ప్రభావిత ప్రాంతాల ఫోటోలు తీయడాన్ని పరిగణించండి",
            "చర్య తీసుకునే ముందు 3-5 రోజులు పరిస్థితిని పర్యవేక్షించండి",
            "స్థానిక వ్యవసాయ విస్తరణ అధికారులతో సంప్రదించండి",
            "మట్టి తేమ స్థాయిలను క్రమం తప్పకుండా తనిఖీ చేయండి",
            "వర్తించే చికిత్సల వివరణాత్మక రికార్డులను ఉంచండి"
        ]
    }
    
    lang = language.lower()
    return suggestions.get(lang, suggestions["en"])[:3]  # Return top 3 suggestions