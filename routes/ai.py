import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from ai.agent import ask_agent, get_or_create_conversation, AVAILABLE_MODELS
from ai.prompts import WEEKLY_DIGEST_PROMPT
from models.user_profile import UserProfile
from models.weekly_digest import WeeklyDigest
from models.conversation import Conversation
from utils import logger

router = APIRouter()

@router.get("/models/available")
async def get_available_models():
    return AVAILABLE_MODELS

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
        
    if not request.conversation_id:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_conversations_count = (
            db.query(Conversation)
            .filter(
                Conversation.user_sync_token == user.sync_token,
                Conversation.created_at >= today_start
            )
            .count()
        )
        if daily_conversations_count >= 3:
            raise HTTPException(status_code=429, detail="Daily conversation limit reached. You can only create 3 conversations per day.")

    async def event_generator():
        try:
            if not request.conversation_id:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Generating conversation...'})}\n\n"
                
            conversation = await get_or_create_conversation(request.message, user, request.conversation_id, db)
            yield f"data: {json.dumps({'type': 'conversation_id', 'id': conversation.id, 'title': conversation.title})}\n\n"

            async for update in ask_agent(
                message=request.message, 
                user=user, 
                conversation=conversation, 
                db=db,
                continue_conversation=request.continue_conversation
            ):
                yield update
        except Exception as e:
            print(f"Error generating response: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class GenerateWeeklyDigestRequest(BaseModel):
    sync_token: str

@router.post("/generate-weekly-digest")
async def generate_weekly_digest(request: GenerateWeeklyDigestRequest, db: Session = Depends(get_db)):
    logger.info("Received generate-weekly-digest request", extra={"sync_token": request.sync_token})
    user = db.query(UserProfile).filter(UserProfile.sync_token == request.sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating digest...'})}\n\n"
            
            message = WEEKLY_DIGEST_PROMPT.replace("{{current_date}}", datetime.now().strftime("%Y-%m-%d"))
            conversation = await get_or_create_conversation(message, user, None, db, title="Weekly Digest")
            yield f"data: {json.dumps({'type': 'conversation_id', 'id': conversation.id, 'title': conversation.title})}\n\n"

            final_response_text = ""
            async for update in ask_agent(
                message=message, 
                user=user, 
                conversation=conversation, 
                db=db,
                continue_conversation=False
            ):
                yield update
                
                # Intercept the final response to save the weekly digest
                if update.startswith("data: ") and '"type": "final_response"' in update:
                    data = json.loads(update[6:].strip())
                    final_response_text = data.get("text", "")
                    
            if final_response_text:
                new_digest = WeeklyDigest(
                    user_sync_token=user.sync_token,
                    digest=final_response_text
                )
                db.add(new_digest)
                
                # Delete the temporary conversation
                db.delete(conversation)
                db.commit()
                
        except Exception as e:
            print(f"Error generating response: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/weekly-digests")
async def get_weekly_digests(sync_token: str, db: Session = Depends(get_db)):
    logger.info("Received get-weekly-digests request", extra={"sync_token": sync_token})
    
    # Verify user ownership and fetch digests
    digests = (
        db.query(WeeklyDigest.created_at, WeeklyDigest.digest)
        .filter(WeeklyDigest.user_sync_token == sync_token)
        .order_by(WeeklyDigest.created_at.desc())
        .all()
    )
    
    # Format response as a list of dictionaries
    return [{"created_at": d.created_at, "digest": d.digest} for d in digests]
