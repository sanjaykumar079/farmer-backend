from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase

router = APIRouter()

@router.post("/login")
def login(user_token: str):
    """
    Handles login via Supabase Auth (Google Oauth).
    """
    user = supabase.auth.get_user(user_token)
    return {"user": user}
