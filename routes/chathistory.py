from fastapi import APIRouter, HTTPException
from database import chat_history_collection
from models.chathistory import ChatHistory
from bson import ObjectId

router = APIRouter()

@router.post("/")
async def create_chat_history(chat_history: ChatHistory):
    """Create a new chat history record."""
    chat_history_dict = chat_history.dict(by_alias=True)
    result = await chat_history_collection.insert_one(chat_history_dict)
    return {"id": str(result.inserted_id), "message": "Chat history created successfully"}

@router.get("/{user_id}")
async def get_chat_history(user_id: str):
    """Retrieve chat history for a user."""
    chat_history = await chat_history_collection.find({"user_id": ObjectId(user_id)}).to_list(100)
    if not chat_history:
        raise HTTPException(status_code=404, detail="No chat history found for this user")
    return [{"id": str(history["_id"]), **history} for history in chat_history]