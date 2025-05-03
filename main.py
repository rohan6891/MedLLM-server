from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Routes imports
from routes.auth import router as auth_router
from routes.chats import router as chats_router
from routes.chathistory import router as chathistory_router
from routes.personalinfo import router as personalinfo_router  # Import personalinfo router

app = FastAPI()

# Load environment variables
load_dotenv()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with frontend origin if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chats_router, prefix="/chats", tags=["Chats"])
app.include_router(chathistory_router, prefix="/chathistory", tags=["Chat History"])
app.include_router(personalinfo_router, prefix="/personalinfo", tags=["Personal Info"])  # Add personalinfo router

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)