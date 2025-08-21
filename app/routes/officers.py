from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.routes.supabase_client import supabase

router = APIRouter()

@router.get("/queries")
def get_all_queries():
    """
    Get all farmer queries with farmer details and replies
    """
    try:
        response = supabase.table("queries").select("""
            id,
            query_text,
            image_url,
            status,
            urgency,
            created_at,
            farmer_id,
            profiles(full_name,email),
            replies(id,response_text,created_at,officer_id)
        """).order("created_at", desc=True).execute()

        if not response.data:
            return []

        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch queries: {str(e)}")
    
    
class ReplyRequest(BaseModel):
    query_id: int
    officer_id: str
    response_text: str
    audio_path: str | None = None


# app/routes/officers.py
@router.post("/reply")
def submit_reply(payload: dict):
    try:
        query_id = payload.get("query_id")
        officer_id = payload.get("officer_id")
        response_text = payload.get("response_text")
        audio_path = payload.get("audio_path")

        # 1. Insert reply
        supabase.table("replies").insert({
            "query_id": query_id,
            "officer_id": officer_id,
            "response_text": response_text,
            "audio_path": audio_path
        }).execute()

        # 2. Update query status -> "answered"
        supabase.table("queries").update({
            "status": "answered"
        }).eq("id", query_id).execute()

        return {"success": True, "message": "Reply submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit reply: {str(e)}")

