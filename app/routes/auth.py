# app/routes/auth.py
from fastapi import APIRouter
from datetime import datetime
import uuid
from .supabase_client import supabase

router = APIRouter()

@router.post("/create-test-farmer")
def create_test_farmer():
    test_id = "0234234f-1aa4-46b2-8195-a8e99f5d2f1f"  # fixed id used by your frontend
    profile = {
        "id": test_id,
        "role": "farmer",
        "full_name": "Test Farmer",
        "email": "farmer@example.com",
        "location": "Test Village",
        "created_at": datetime.utcnow().isoformat()
    }
    # upsert to avoid duplicates on re-run
    res = supabase.table("profiles").upsert(profile, on_conflict="id").execute()
    return {"message": "farmer ready", "profile": res.data}

@router.post("/create-test-officer")
def create_test_officer():
    officer_id = str(uuid.uuid4())
    profile = {
        "id": officer_id,
        "role": "officer",
        "full_name": "Test Officer",
        "email": "officer@example.com",
        "location": "District HQ",
        "created_at": datetime.utcnow().isoformat()
    }
    res = supabase.table("profiles").insert(profile).execute()
    return {"message": "officer ready", "officer_id": officer_id, "profile": res.data}
