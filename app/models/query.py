from pydantic import BaseModel
from typing import Optional

class Query(BaseModel):
    id: int
    farmer_id: str
    query_text: str
    image_url: Optional[str]
