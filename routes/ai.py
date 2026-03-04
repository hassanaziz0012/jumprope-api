import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from ai.gemini import ask_gemini
from models.user_profile import UserProfile
from utils import logger

router = APIRouter()

class AskAgentRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    sync_token: str
    continue_conversation: Optional[bool] = False

@router.post("/ask-agent")
async def ask_agent(request: AskAgentRequest, db: Session = Depends(get_db)):
    logger.info("Received ask-agent request", extra={"sync_token": request.sync_token, "conversation_id": request.conversation_id})
    user = db.query(UserProfile).filter(UserProfile.sync_token == request.sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    async def event_generator():
        try:
            async for update in ask_gemini(
                message=request.message, 
                user=user, 
                conversation_id=request.conversation_id, 
                db=db,
                continue_conversation=request.continue_conversation
            ):
                yield update
        except Exception as e:
            print(f"Error generating response: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
