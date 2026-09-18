import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from agent import run_agent_turn 

os.makedirs("static", exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    prompt: str
    session_id: str = "clinical_session_1" 

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    def generate():
        for chunk in run_agent_turn(req.prompt, req.session_id):
            yield chunk
    return StreamingResponse(generate(), media_type="text/plain")