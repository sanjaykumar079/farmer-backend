from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    role: str  # farmer or officer
