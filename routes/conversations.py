from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from models.user_profile import UserProfile
from models.conversation import Conversation

from utils import logger

router = APIRouter()

@router.get("/")
def get_conversations(sync_token: str, db: Session = Depends(get_db)):
    logger.info("Received get conversations request", extra={"sync_token": sync_token})
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    conversations = db.query(Conversation).filter(Conversation.user_sync_token == user.sync_token).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } 
        for c in conversations
    ]

@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, sync_token: str, db: Session = Depends(get_db)):
    logger.info("Received get conversation request", extra={"conversation_id": conversation_id, "sync_token": sync_token})
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_sync_token == user.sync_token
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")
        
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_results": m.tool_results,
                "created_at": m.created_at
            }
            for m in conversation.messages
        ]
    }

@router.delete("/{conversation_id}/delete")
def delete_conversation(conversation_id: str, sync_token: str, db: Session = Depends(get_db)):
    logger.info("Received delete conversation request", extra={"conversation_id": conversation_id, "sync_token": sync_token})
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    db.delete(conversation)
    db.commit()
    
    return {"status": "success", "message": "Conversation deleted successfully"}
