import os
from fastapi import APIRouter, HTTPException, Form
from database import users_collection
import bcrypt
import jwt  # Ensure this is from PyJWT
from dotenv import load_dotenv
from pydantic import EmailStr, BaseModel
import datetime

load_dotenv()
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    phone_number: str

@router.post("/signup")
async def signup(
    email: EmailStr = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    phone_number: str = Form(...)
):
    print("Received form data:", {"email": email, "password": password, "username": username, "phone_number": phone_number})

    # Check if the user already exists
    if await users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Insert the user into the database
    await users_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
        "phone_number": phone_number,
        "created_at": datetime.datetime.utcnow()
    })

    return {"message": "User registered successfully"}

@router.post("/login")
async def login(
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    # Find the user in the database
    db_user = await users_collection.find_one({"email": email})
    if not db_user or not bcrypt.checkpw(password.encode(), db_user["password"].encode()):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate a JWT token
    token = jwt.encode({"email": email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token, "user_id": str(db_user["_id"])}
