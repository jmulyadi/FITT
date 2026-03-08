from fastapi import APIRouter, HTTPException
from groq import Groq
from pydantic import BaseModel
import os

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Message(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@router.post("/chat", tags=["Groq"])
async def groq_chat(request: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key is not configured")

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Prepend the system prompt, then append the conversation history
        full_messages = [
            {
                "role": "system",
                "content": "You are FITT, a helpful fitness and nutrition assistant. Help users with workout plans, exercise advice, and meal guidance."
            }
        ] + [{"role": m.role, "content": m.content} for m in request.messages]

        chat_completion = client.chat.completions.create(
            messages=full_messages,
            model="llama-3.3-70b-versatile",
        )

        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interacting with Groq: {str(e)}")