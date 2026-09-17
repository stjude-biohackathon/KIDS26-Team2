from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles # <-- NEW
import os # <-- NEW

from agent import run_agent_turn 

# Create the static folder if it doesn't exist so Docker doesn't crash!
os.makedirs("static", exist_ok=True)

app = FastAPI()

# Mount the folder so Next.js can read the images
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    session_id: str = "clinical_session_1" 

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    def generate():
        for chunk in run_agent_turn(req.prompt, req.session_id):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")