from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional

class ChatHistory(BaseModel):
    user_id: ObjectId
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    topic: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types like ObjectId
        json_encoders = {ObjectId: str}  # Convert ObjectId to string for JSON serialization