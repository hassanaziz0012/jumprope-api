from fastapi import APIRouter
from pydantic import BaseModel
from ai.gemini import ask_gemini

router = APIRouter()

class AskAgentRequest(BaseModel):
    message: str

@router.post("/ask-agent")
def ask_agent(request: AskAgentRequest):
    response = ask_gemini(request.message)
    return {"response": response}
