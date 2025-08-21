# app/routes/farmers.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from datetime import datetime
import uuid
import logging
from .supabase_client import supabase

router = APIRouter()
logger = logging.getLogger("farmers")

BUCKET = "farmer-queries"          # must exist
FOLDER = "query-images"            # folder inside bucket

def _ensure_farmer_exists(farmer_id: str):
    prof = supabase.table("profiles").select("id, role").eq("id", farmer_id).limit(1).execute()
    if not prof.data:
        raise HTTPException(status_code=404, detail="Farmer profile not found. Please login again.")
    if prof.data[0].get("role") != "farmer":
        raise HTTPException(status_code=403, detail="Only farmers can submit queries")

# app/routes/farmers.py
@router.get("/my-queries/{farmer_id}")
def get_my_queries(farmer_id: str):
    try:
        response = supabase.table("queries").select(
            """
            id,
            farmer_id,
            query_text,
            image_url,
            urgency,
            status,
            created_at,
            replies(id, officer_id, response_text, audio_path, created_at)
            """
        ).eq("farmer_id", farmer_id).order("created_at", desc=True).execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch queries: {str(e)}")



@router.get("/dashboard-stats/{farmer_id}")
def dashboard_stats(farmer_id: str):
    _ensure_farmer_exists(farmer_id)
    total = supabase.rpc("count_queries_by_farmer", {"fid": farmer_id}).execute().data if hasattr(supabase, "rpc") else None
    # fallback simple counts if you don't have the RPC
    q = supabase.table("queries").select("id").eq("farmer_id", farmer_id).execute().data or []
    r = supabase.table("replies").select("id").in_("query_id", [row["id"] for row in q] or [-1]).execute().data or []
    return {"total_queries": len(q), "total_replies": len(r)}

@router.post("/submit-query")
async def submit_query(
    farmer_id: str = Form(...),
    query_text: str = Form(...),
    urgency: str = Form("medium"),
    image: Optional[UploadFile] = File(None)
):
    _ensure_farmer_exists(farmer_id)

    image_url = None
    if image and image.filename:
        content = await image.read()
        ext = image.filename.split(".")[-1].lower() if "." in image.filename else "jpg"
        unique = f"{farmer_id}_{uuid.uuid4()}.{ext}"
        path = f"{FOLDER}/{unique}"

        up = supabase.storage.from_(BUCKET).upload(path, content)
        if getattr(up, "error", None):
            raise HTTPException(status_code=500, detail=f"Image upload failed: {up.error}")

        url_dict = supabase.storage.from_(BUCKET).get_public_url(path)
        image_url = url_dict.get("publicUrl") if isinstance(url_dict, dict) else str(url_dict)

    query_data = {
        "farmer_id": farmer_id,
        "query_text": query_text,
        "image_url": image_url,
        "urgency": urgency,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        ins = supabase.table("queries").insert(query_data).execute()
        if not ins.data:
            raise Exception(getattr(ins, "error", "Unknown insert error"))
        query_id = ins.data[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save query: {e}")

    return {"message": "query submitted successfully", "query_id": query_id, "image_url": image_url}
