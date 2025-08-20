from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, farmers, officers, ai

app = FastAPI(title="Farmer-Horticulture-Interface API")

# Enable CORS (frontend → backend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change later to specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(farmers.router, prefix="/farmers", tags=["Farmers"])
app.include_router(officers.router, prefix="/officers", tags=["Officers"])
app.include_router(ai.router, prefix="/ai", tags=["AI Services"])

@app.get("/")
def root():
    return {"message": "Farmer-Horticulture-Interface API running 🚜"}
