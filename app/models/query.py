from pydantic import BaseModel
from typing import Optional

class Query(BaseModel):
    id: int
    farmer_id: str
    query_text: str
    image_url: Optional[str]


class QueryCreate(BaseModel):
    farmer_id: int
    question: str
    
class QueryResponse(BaseModel):
    id: int
    question: str
    answer: str