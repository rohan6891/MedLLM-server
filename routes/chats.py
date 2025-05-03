from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from database import chats_collection
from models.chats import Chats
from bson import ObjectId
import httpx
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os
import shutil
import base64
import nest_asyncio
from llama_parse import LlamaParse
from groq import Groq
from typing import List
import mimetypes

router = APIRouter()

# Load FAISS index and metadata
index = faiss.read_index("/home/rohan6891/Desktop/projects/MedLLM/server/routes/embeddings/medical_index2.faiss")  # Ensure this file exists
with open("/home/rohan6891/Desktop/projects/MedLLM/server/routes/embeddings/metadata2.json", "r") as f:  # Ensure this file exists
    metadata = json.load(f)

# Initialize Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Model API URL
MODEL_API_URL = "https://3182-34-124-160-229.ngrok-free.app/predict/"  # Replace with the actual model API URL

# Directory for uploaded files
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Apply nest_asyncio
nest_asyncio.apply()

# Initialize LlamaParse and Groq clients
parser = LlamaParse(
    api_key="llx-xfcUfT4Ox7zkHzOE58j0qNDVBZKaFT8Shwc9UufNapFpJFca",
    result_type="markdown",
    verbose=True,
    language="en",
    num_workers=4
)

groq_client = Groq(api_key="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")

# Function to retrieve relevant documents
def retrieve_documents(query, top_k=2):
    """Retrieve top-k relevant documents using FAISS."""
    query_embedding = model.encode([query], convert_to_numpy=True)[0]
    distances, indices = index.search(np.array([query_embedding]), top_k)
    retrieved_docs = [metadata[idx]["text"] for idx in indices[0] if idx < len(metadata)]
    return retrieved_docs

async def process_pdf_content(file_path: str) -> str:
    """Process PDF file using LlamaParse and Groq"""
    try:
        # Parse PDF
        with open(file_path, "rb") as f:
            documents = parser.load_data(f)
        
        markdown_content = "\n".join([doc.text for doc in documents])
        markdown_content = markdown_content[:100000]  # Truncate if needed

        # Get summary from Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Analyze the following document content and provide a summary:\n\n{markdown_content}"
                }]
            }],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return ""

@router.post("/")
async def handle_chat(
    session_id: str = Form(...),
    user_id: str = Form(...),
    content: str = Form(None),
    files: List[UploadFile] = File(None)
):
    """Handle chat messages with multiple file uploads"""
    try:
        # Create user directory in uploads folder
        user_upload_dir = os.path.join(UPLOAD_DIR, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)

        # Process uploaded files
        pdf_contents = []
        image_paths = []

        if files:
            for file in files:
                # Get file mimetype
                mime_type, _ = mimetypes.guess_type(file.filename)
                
                # Save file
                file_path = os.path.join(user_upload_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # Process based on file type
                if mime_type == 'application/pdf':
                    pdf_content = await process_pdf_content(file_path)
                    if pdf_content:
                        pdf_contents.append(pdf_content)
                elif mime_type and mime_type.startswith('image/'):
                    image_paths.append(file_path)
                else:
                    os.remove(file_path)  # Remove unsupported file
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported file type: {file.filename}. Only PDFs and images are allowed."
                    )

        # Combine all content
        context = ""
        if content:
            retrieved_docs = retrieve_documents(content, top_k=2)
            if retrieved_docs:
                context = "\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(retrieved_docs)])

        # Combine question with PDF content and context
        pdf_summaries = "\n\nPDF Summaries:\n" + "\n".join(pdf_contents) if pdf_contents else ""
        question = f"{content}\n\nContext:\n{context}{pdf_summaries}"

        # Prepare payload for external API
        payload = {"question": question}

        # Add images to payload
        for image_path in image_paths:
            with open(image_path, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                payload["image"] = encoded_image  # Modify if API supports multiple images

        # Forward the payload to the external API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(MODEL_API_URL, data=payload)
                response.raise_for_status()
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Error communicating with model API: {e}")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=response.status_code, detail=f"Model API error: {response.text}")

        # Get the model's response
        model_response = response.json()

        # Save the user input, file (if any), and model response to the database
        chat_dict = {
            "session_id": session_id,
            "user_id": str(user_id),
            "content": content,
            "file": [file.filename for file in files] if files else None,
            "model_response": model_response,
        }
        result = await chats_collection.insert_one(chat_dict)

        # Return the response to the frontend
        return {
            "id": str(result.inserted_id),
            "message": "Chat processed successfully",
            "model_response": model_response,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/{session_id}")
async def get_chats(session_id: str):
    """Retrieve all chats for a session."""
    chats = await chats_collection.find({"session_id": session_id}).to_list(100)
    if not chats:
        raise HTTPException(status_code=404, detail="No chats found for this session")
    return [{"id": str(chat["_id"]), **chat} for chat in chats]

@router.post("/chats/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user_id: str = Form(...)
):
    """Upload a file and return its URL."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return the file URL (adjust based on your hosting setup)
    file_url = f"http://localhost:8000/uploads/{file.filename}"
    return JSONResponse(content={"file_url": file_url, "message": "File uploaded successfully"})

@router.post("/feedback")
async def submit_feedback(
    message_id: str = Form(...),
    feedback_type: str = Form(...)  # "positive" or "negative"
):
    """Submit feedback for a specific message."""
    try:
        result = await chats_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"feedback": feedback_type}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Message not found or feedback not updated")
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {e}")

@router.get("/details/{message_id}")
async def get_message_details(message_id: str):
    """Retrieve details for a specific message."""
    try:
        message = await chats_collection.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving message details: {e}")

@router.get("/download/{message_id}")
async def download_message(message_id: str):
    """Download a message as a text file."""
    try:
        message = await chats_collection.find_one({"_id": ObjectId(message_id)})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        file_path = os.path.join(UPLOAD_DIR, f"{message_id}.txt")
        with open(file_path, "w") as file:
            file.write(message.get("content", ""))
        return FileResponse(file_path, media_type="text/plain", filename=f"{message_id}.txt")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading message: {e}")

