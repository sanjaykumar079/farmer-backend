import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# Load your trained model (adjust path as needed)
MODEL_PATH = "models/disease_detection_model.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define your CNN architecture (match your training model)
class DiseaseDetectionCNN(nn.Module):
    def __init__(self, num_classes=10):  # Adjust based on your classes
        super(DiseaseDetectionCNN, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )
    
    def forward(self, x):
        x = self.conv_layers(x)
        x = self.classifier(x)
        return x

# Load model once at startup
try:
    model = DiseaseDetectionCNN(num_classes=10)  # Adjust based on your classes
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    logger.info("Disease detection model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    model = None

# Define your disease classes
DISEASE_CLASSES = [
    "Healthy",
    "Bacterial Blight",
    "Brown Spot", 
    "Leaf Blast",
    "Tungro",
    "Bacterial Leaf Streak",
    "Red Stripe",
    "Sheath Blight",
    "Yellow Dwarf",
    "Blast"
]

# Image preprocessing pipeline
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_disease(image_bytes: bytes) -> dict:
    """
    Predict disease from image bytes using CNN model
    """
    try:
        if model is None:
            return {
                "error": "Model not loaded",
                "prediction": "Unable to analyze image",
                "confidence": 0.0
            }
        
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        # Make prediction
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            confidence, predicted_class = torch.max(probabilities, 1)
            
        predicted_disease = DISEASE_CLASSES[predicted_class.item()]
        confidence_score = confidence.item()
        
        # Get top 3 predictions
        top_probs, top_indices = torch.topk(probabilities[0], k=min(3, len(DISEASE_CLASSES)))
        top_predictions = [
            {
                "disease": DISEASE_CLASSES[idx.item()],
                "confidence": prob.item()
            }
            for prob, idx in zip(top_probs, top_indices)
        ]
        
        return {
            "prediction": predicted_disease,
            "confidence": confidence_score,
            "top_predictions": top_predictions,
            "recommendations": get_treatment_recommendation(predicted_disease, confidence_score)
        }
        
    except Exception as e:
        logger.error(f"Error in disease prediction: {e}")
        return {
            "error": f"Prediction failed: {str(e)}",
            "prediction": "Unable to analyze image",
            "confidence": 0.0
        }

def get_treatment_recommendation(disease: str, confidence: float) -> str:
    """
    Get treatment recommendations based on predicted disease
    """
    if confidence < 0.7:
        return "Prediction confidence is low. Please consult with an agricultural expert for accurate diagnosis."
    
    treatments = {
        "Healthy": "Your crop appears healthy! Continue with regular care and monitoring.",
        "Bacterial Blight": "Apply copper-based bactericide. Remove affected leaves and improve air circulation.",
        "Brown Spot": "Use fungicide spray and ensure proper field drainage. Avoid overhead irrigation.",
        "Leaf Blast": "Apply systemic fungicide immediately. Remove infected plant debris.",
        "Tungro": "This is a viral disease spread by insects. Use insecticides to control vectors and remove infected plants.",
        "Bacterial Leaf Streak": "Apply streptomycin-based bactericide. Improve field sanitation.",
        "Red Stripe": "Apply appropriate fungicide and ensure balanced nutrition.",
        "Sheath Blight": "Use fungicide treatment and maintain proper spacing between plants.",
        "Yellow Dwarf": "Viral disease - remove infected plants immediately and control insect vectors.",
        "Blast": "Apply systemic fungicide and improve drainage. Consider resistant varieties."
    }
    
    return treatments.get(disease, "Consult with agricultural expert for proper treatment.")