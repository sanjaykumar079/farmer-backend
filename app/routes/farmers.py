from fastapi import APIRouter, UploadFile, Form
from app.services.supabase_client import supabase

router = APIRouter()

@router.post("/submit-query")
async def submit_query(
    farmer_id: str = Form(...),
    query_text: str = Form(...),
    image: UploadFile = None
):
    # Upload image to Supabase storage
    image_url = None
    if image:
        content = await image.read()
        file_path = f"queries/{farmer_id}_{image.filename}"
        supabase.storage.from_("farmer-queries").upload(file_path, content)
        image_url = supabase.storage.from_("farmer-queries").get_public_url(file_path)

    # Save query in DB
    supabase.table("queries").insert({
        "farmer_id": farmer_id,
        "query_text": query_text,
        "image_url": image_url
    }).execute()

    return {"message": "Query submitted successfully"}
