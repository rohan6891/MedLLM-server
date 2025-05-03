from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from datetime import datetime
from typing import Optional

class User(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: str  # Add phone number field
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}