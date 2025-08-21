# main.py
import os
from dotenv import load_dotenv  # ✅ import here

# load environment variables from .env
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import farmers, officers, auth

app = FastAPI(title="Farmer-Horticulture API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(farmers.router, prefix="/farmers", tags=["farmers"])
app.include_router(officers.router, prefix="/officers", tags=["officers"])

@app.get("/")
def health():
    return {"ok": True}
