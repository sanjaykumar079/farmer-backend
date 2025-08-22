# app/routes/farmers.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
from app.routes.supabase_client import supabase
import logging
import uuid

router = APIRouter()
log = logging.getLogger(__name__)

def _ensure_farmer_exists(farmer_id: str) -> Dict[str, Any]:
    prof = supabase.table("profiles").select("id, role, full_name, email").eq("id", farmer_id).limit(1).execute()
    if not prof.data:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return prof.data[0]

@router.get("/my-queries/{farmer_id}")
def get_my_queries(farmer_id: str):
    _ensure_farmer_exists(farmer_id)

    qres = (
        supabase.table("queries")
        .select("id,query_text,image_url,status,urgency,created_at")
        .eq("farmer_id", farmer_id)
        .order("created_at", desc=True)
        .execute()
    )
    queries = qres.data or []

    # bring replies for these queries
    q_ids = [q["id"] for q in queries]
    replies_by_qid = {}
    if q_ids:
        rres = supabase.table("replies") \
            .select("id,query_id,officer_id,response_text,created_at") \
            .in_("query_id", q_ids).order("created_at", desc=True).execute()
        for r in rres.data or []:
            replies_by_qid.setdefault(r["query_id"], []).append(r)

    # attach replies
    for q in queries:
        q["replies"] = replies_by_qid.get(q["id"], [])

    return {"ok": True, "data": queries}

@router.post("/submit-query")
async def submit_query(
    farmer_id: str = Form(...),
    query_text: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    _ensure_farmer_exists(farmer_id)

    image_url = None
    if image:
        # store under a deterministic key
        key = f"queries/{farmer_id}/{uuid.uuid4()}-{image.filename}"
        storage.from_("public").upload(file=image.file, path=key, file_options={"content_type": image.content_type})
        # public URL
        image_url = f"{storage.public_url('public')}/{key}".replace("//public/", "/public/")

    ins = supabase.table("queries").insert({
        "farmer_id": farmer_id,
        "query_text": query_text.strip(),
        "image_url": image_url,
        "status": "pending",
        "urgency": "medium"
    }).execute()

    if not ins.data:
        raise HTTPException(status_code=500, detail="Failed to create query")

    return {"ok": True, "query": ins.data[0]}
