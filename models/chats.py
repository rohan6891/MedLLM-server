from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List, Any

class Chats(BaseModel):
    session_id: str
    user_id: str
    content: Optional[str] = None  # Make content optional
    sender: str
    files: Optional[List[Dict[str, str]]] = None  # Store file information
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, str]] = None
    retrieved_docs: Optional[List[str]] = None
    pdf_contents: Optional[List[str]] = None  # Store PDF summaries
    model_response: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True