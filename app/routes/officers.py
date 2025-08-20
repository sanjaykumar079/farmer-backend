from fastapi import APIRouter
from app.services.supabase_client import supabase

router = APIRouter()

@router.get("/get-queries")
def get_queries():
    response = supabase.table("queries").select("*").execute()
    return response.data

@router.post("/reply")
def reply(query_id: int, officer_id: str, response_text: str):
    supabase.table("replies").insert({
        "query_id": query_id,
        "officer_id": officer_id,
        "response_text": response_text
    }).execute()
    return {"message": "Reply sent successfully"}
