# app/routes/officers.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.routes.supabase_client import supabase
import logging

router = APIRouter()
log = logging.getLogger(__name__)

# ---------- MODELS ----------

class SubmitReplyReq(BaseModel):
    query_id: int
    officer_id: str  # uuid
    response_text: str
    # NOTE: your replies table has 5 columns (id, query_id, officer_id, response_text, created_at)
    # If later you add audio_url, you can uncomment this and the insert will include it when present.
    # audio_url: Optional[str] = None

# ---------- HELPERS ----------

def fetch_query(query_id: int) -> Dict[str, Any]:
    q = supabase.table("queries").select("*").eq("id", query_id).limit(1).execute()
    if not q.data:
        raise HTTPException(status_code=404, detail=f"Query {query_id} not found")
    return q.data[0]

def fetch_profile(user_id: str) -> Dict[str, Any]:
    p = supabase.table("profiles").select("id, role, full_name, email").eq("id", user_id).limit(1).execute()
    if not p.data:
        raise HTTPException(status_code=404, detail=f"Profile {user_id} not found")
    return p.data[0]

# ---------- ROUTES ----------

@router.get("/queries")
def get_all_queries():
    """
    Returns all queries with basic farmer info and any replies.
    Keep the select minimal to avoid “failed to parse select parameter” errors.
    """
    # queries + farmer basics
    qres = (
        supabase.table("queries")
        .select("id,farmer_id,query_text,image_url,status,urgency,created_at")
        .order("created_at", desc=True)
        .execute()
    )
    queries = qres.data or []

    # map farmer_id -> profile
    farmer_ids = list({q["farmer_id"] for q in queries if q.get("farmer_id")})
    profiles_by_id = {}
    if farmer_ids:
        pres = supabase.table("profiles") \
            .select("id,full_name,email") \
            .in_("id", farmer_ids).execute()
        for p in pres.data or []:
            profiles_by_id[p["id"]] = p

    # attach replies (many) for each query
    q_ids = [q["id"] for q in queries]
    replies_by_qid = {}
    if q_ids:
        rres = supabase.table("replies") \
            .select("id,query_id,officer_id,response_text,created_at") \
            .in_("query_id", q_ids).order("created_at", desc=True).execute()
        for r in rres.data or []:
            replies_by_qid.setdefault(r["query_id"], []).append(r)

    # final merge
    out = []
    for q in queries:
        out.append({
            **q,
            "farmer": profiles_by_id.get(q["farmer_id"]),
            "replies": replies_by_qid.get(q["id"], [])
        })
    return {"ok": True, "data": out}


@router.post("/reply")
def submit_reply(body: SubmitReplyReq):
    """
    Insert a reply row and mark the query as answered.
    Important: only insert columns that actually exist.
    """
    # Verify both sides exist (helps surface clean 404 instead of 500)
    q = fetch_query(body.query_id)
    officer = fetch_profile(body.officer_id)

    # Insert reply (only existing columns)
    payload = {
        "query_id": body.query_id,
        "officer_id": body.officer_id,
        "response_text": body.response_text.strip(),
    }
    ins = supabase.table("replies").insert(payload).execute()
    if not ins.data:
        raise HTTPException(status_code=500, detail="Insert reply failed")

    # Update query status -> answered (don’t touch constraint order or extra columns)
    supabase.table("queries").update({"status": "answered"}).eq("id", body.query_id).execute()

    # Return a clean JSON document (don’t return raw client object)
    return {
        "ok": True,
        "reply": ins.data[0],
        "query": {k: q[k] for k in ["id", "farmer_id", "status", "created_at", "query_text", "image_url", "urgency"] if k in q},
        "officer": {"id": officer["id"], "full_name": officer.get("full_name"), "email": officer.get("email")}
    }
