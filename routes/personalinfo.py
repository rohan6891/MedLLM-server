from fastapi import APIRouter, HTTPException
from database import personal_info_collection
from models.personalinfo import PersonalInfo
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/")
async def create_personal_info(personal_info: PersonalInfo):
    """Create a new personal info record."""
    # Check if the user already has personal info
    existing_info = await personal_info_collection.find_one({"user_id": personal_info.user_id})
    if existing_info:
        raise HTTPException(status_code=400, detail="Personal info already exists for this user.")

    # Insert the new personal info
    personal_info_dict = personal_info.dict(by_alias=True)
    print(personal_info_dict)
    result = await personal_info_collection.insert_one(personal_info_dict)
    return {"id": str(result.inserted_id), "message": "Personal info created successfully"}

@router.put("/{user_id}")
async def update_personal_info(user_id: str, personal_info: PersonalInfo):
    """Update personal info for a user."""
    # Check if the personal info exists
    existing_info = await personal_info_collection.find_one({"user_id": ObjectId(user_id)})
    if not existing_info:
        raise HTTPException(status_code=404, detail="Personal info not found for this user.")

    # Update the personal info
    update_data = personal_info.dict(exclude_unset=True)  # Only update fields provided in the request
    update_data["updated_at"] = datetime.utcnow()  # Update the timestamp
    result = await personal_info_collection.update_one({"user_id": ObjectId(user_id)}, {"$set": update_data})

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update personal info.")
    return {"message": "Personal info updated successfully"}