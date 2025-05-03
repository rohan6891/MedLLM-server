from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

class PersonalInfo(BaseModel):
    user_id: ObjectId
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    conditions: Optional[str] = None
    lifestyle: Optional[str] = None
    exercise_frequency: Optional[str] = None
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}