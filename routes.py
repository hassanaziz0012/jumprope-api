import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from ai.gemini import ask_gemini

# Models and Schemas
from models.user_profile import UserProfile
from models.workout import Workout
from models.goal import Goal
from models.rest_day import RestDay
from models.chart import Chart
from models.conversation import Conversation, ConversationMessage
from schemas import (
    SyncWorkoutsRequest,
    SyncGoalsRequest,
    SyncRestDaysRequest,
    SyncChartsRequest
)
from utils import sync_user_profile

router = APIRouter()

class AskAgentRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    sync_token: str
    continue_conversation: Optional[bool] = False

@router.post("/ask-agent")
async def ask_agent(request: AskAgentRequest, db: Session = Depends(get_db)):
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

@router.post("/sync/workouts")
def sync_workouts(request: SyncWorkoutsRequest, db: Session = Depends(get_db)):
    user = sync_user_profile(db, request.user)
    
    for w_data in request.data:
        workout = db.query(Workout).filter(
            Workout.id == w_data.id,
            Workout.user_profile_id == user.id
        ).first()
        
        if workout:
            for key, value in w_data.model_dump().items():
                setattr(workout, key, value)
        else:
            workout = Workout(**w_data.model_dump(), user_profile_id=user.id)
            db.add(workout)
            
    db.commit()
    return {"status": "success"}

@router.post("/sync/goals")
def sync_goals(request: SyncGoalsRequest, db: Session = Depends(get_db)):
    user = sync_user_profile(db, request.user)
    
    for g_data in request.data:
        goal = db.query(Goal).filter(
            Goal.id == g_data.id,
            Goal.user_profile_id == user.id
        ).first()
        
        if goal:
            for key, value in g_data.model_dump().items():
                setattr(goal, key, value)
        else:
            goal = Goal(**g_data.model_dump(), user_profile_id=user.id)
            db.add(goal)
            
    db.commit()
    return {"status": "success"}

@router.post("/sync/rest-days")
def sync_rest_days(request: SyncRestDaysRequest, db: Session = Depends(get_db)):
    user = sync_user_profile(db, request.user)
    
    for rd_data in request.data:
        rd = db.query(RestDay).filter(
            RestDay.date == rd_data.date,
            RestDay.user_profile_id == user.id
        ).first()
        
        if not rd:
            rd = RestDay(date=rd_data.date, user_profile_id=user.id)
            db.add(rd)
            
    db.commit()
    return {"status": "success"}

@router.post("/sync/charts")
def sync_charts(request: SyncChartsRequest, db: Session = Depends(get_db)):
    user = sync_user_profile(db, request.user)
    
    for c_data in request.data:
        chart = db.query(Chart).filter(
            Chart.id == c_data.id,
            Chart.user_profile_id == user.id
        ).first()
        
        if chart:
            for key, value in c_data.model_dump().items():
                setattr(chart, key, value)
        else:
            chart = Chart(**c_data.model_dump(), user_profile_id=user.id)
            db.add(chart)
            
    db.commit()
    return {"status": "success"}

@router.get("/conversations")
def get_conversations(sync_token: str, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    conversations = db.query(Conversation).filter(Conversation.user_profile_id == user.id).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        } 
        for c in conversations
    ]

@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, sync_token: str, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_profile_id == user.id
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

@router.delete("/sync/delete-user-data")
def delete_user_data(sync_token: str, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.sync_token == sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    stats = {
        "workouts_deleted": 0,
        "rest_days_deleted": 0,
        "goals_deleted": 0,
        "charts_deleted": 0,
        "conversation_messages_deleted": 0,
        "conversations_deleted": 0,
        "user_profile_deleted": 0
    }
    
    stats["workouts_deleted"] = db.query(Workout).filter(Workout.user_profile_id == user.id).delete()
    stats["rest_days_deleted"] = db.query(RestDay).filter(RestDay.user_profile_id == user.id).delete()
    stats["goals_deleted"] = db.query(Goal).filter(Goal.user_profile_id == user.id).delete()
    stats["charts_deleted"] = db.query(Chart).filter(Chart.user_profile_id == user.id).delete()
    
    conversation_ids = [c.id for c in db.query(Conversation).filter(Conversation.user_profile_id == user.id).all()]
    if conversation_ids:
        stats["conversation_messages_deleted"] = db.query(ConversationMessage).filter(ConversationMessage.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        
    stats["conversations_deleted"] = db.query(Conversation).filter(Conversation.user_profile_id == user.id).delete()
    stats["user_profile_deleted"] = db.query(UserProfile).filter(UserProfile.id == user.id).delete()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "User data successfully deleted",
        "statistics": stats
    }

@router.delete("/conversations/{conversation_id}/delete")
def delete_conversation(conversation_id: str, sync_token: str, db: Session = Depends(get_db)):
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
