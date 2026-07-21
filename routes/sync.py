from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

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
    SyncChartsRequest,
    UserProfileSchema
)
from utils import sync_user_profile, logger, get_obj_hash

router = APIRouter()

@router.post("/workouts")
def sync_workouts(request: SyncWorkoutsRequest, db: Session = Depends(get_db)):
    logger.info("Received sync workouts request", extra={
        "sync_token": request.user.sync_token,
        "request_data": [w.model_dump() for w in request.data]
    })
    user = sync_user_profile(db, request.user)
    
    for w_data in request.data:
        obj_hash = get_obj_hash(user.sync_token, w_data.id)
        workout = db.query(Workout).filter(
            Workout.sync_id == obj_hash
        ).first()
        
        w_dict = w_data.model_dump()
        w_dict.pop('id', None)
        
        if workout:
            for key, value in w_dict.items():
                setattr(workout, key, value)
        else:
            workout = Workout(**w_dict, user_sync_token=user.sync_token, sync_id=obj_hash)
            db.add(workout)
            
    db.commit()
    
    return {"status": "success"}

@router.post("/goals")
def sync_goals(request: SyncGoalsRequest, db: Session = Depends(get_db)):
    logger.info("Received sync goals request", extra={
        "sync_token": request.user.sync_token,
        "request_data": [g.model_dump() for g in request.data]
    })
    user = sync_user_profile(db, request.user)
    
    for g_data in request.data:
        obj_hash = get_obj_hash(user.sync_token, g_data.id)
        goal = db.query(Goal).filter(
            Goal.sync_id == obj_hash
        ).first()
        
        g_dict = g_data.model_dump()
        g_dict.pop('id', None)
        
        if goal:
            for key, value in g_dict.items():
                setattr(goal, key, value)
        else:
            goal = Goal(**g_dict, user_sync_token=user.sync_token, sync_id=obj_hash)
            db.add(goal)
            
    db.commit()
    
    return {"status": "success"}

@router.post("/rest-days")
def sync_rest_days(request: SyncRestDaysRequest, db: Session = Depends(get_db)):
    logger.info("Received sync rest-days request", extra={
        "sync_token": request.user.sync_token,
        "request_data": [rd.model_dump() for rd in request.data]
    })
    user = sync_user_profile(db, request.user)
    
    for rd_data in request.data:
        obj_hash = get_obj_hash(user.sync_token, rd_data.id)
        rd = db.query(RestDay).filter(
            RestDay.sync_id == obj_hash
        ).first()
        
        rd_dict = rd_data.model_dump()
        rd_dict.pop('id', None)
        
        if rd:
            for key, value in rd_dict.items():
                setattr(rd, key, value)
        else:
            rd = RestDay(**rd_dict, user_sync_token=user.sync_token, sync_id=obj_hash)
            db.add(rd)
            
    db.commit()
    
    return {"status": "success"}

@router.post("/charts")
def sync_charts(request: SyncChartsRequest, db: Session = Depends(get_db)):
    logger.info("Received sync charts request", extra={
        "sync_token": request.user.sync_token,
        "request_data": [c.model_dump() for c in request.data]
    })
    user = sync_user_profile(db, request.user)
    
    for c_data in request.data:
        obj_hash = get_obj_hash(user.sync_token, c_data.id)
        chart = db.query(Chart).filter(
            Chart.sync_id == obj_hash
        ).first()
        
        c_dict = c_data.model_dump()
        c_dict.pop('id', None)
        
        if chart:
            for key, value in c_dict.items():
                setattr(chart, key, value)
        else:
            chart = Chart(**c_dict, user_sync_token=user.sync_token, sync_id=obj_hash)
            db.add(chart)
            
    db.commit()
    
    return {"status": "success"}

@router.post("/user")
def sync_user(request: UserProfileSchema, db: Session = Depends(get_db)):
    logger.info("Received sync user request", extra={
        "sync_token": request.sync_token,
    })
    user = sync_user_profile(db, request)
    return {"status": "success"}

@router.delete("/delete-user-data")
def delete_user_data(sync_token: str, db: Session = Depends(get_db)):
    logger.info("Received delete user data request", extra={"sync_token": sync_token})
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
    
    stats["workouts_deleted"] = db.query(Workout).filter(Workout.user_sync_token == user.sync_token).delete()
    stats["rest_days_deleted"] = db.query(RestDay).filter(RestDay.user_sync_token == user.sync_token).delete()
    stats["goals_deleted"] = db.query(Goal).filter(Goal.user_sync_token == user.sync_token).delete()
    stats["charts_deleted"] = db.query(Chart).filter(Chart.user_sync_token == user.sync_token).delete()
    
    conversation_ids = [c.id for c in db.query(Conversation).filter(Conversation.user_sync_token == user.sync_token).all()]
    if conversation_ids:
        stats["conversation_messages_deleted"] = db.query(ConversationMessage).filter(ConversationMessage.conversation_id.in_(conversation_ids)).delete(synchronize_session=False)
        
    stats["conversations_deleted"] = db.query(Conversation).filter(Conversation.user_sync_token == user.sync_token).delete()
    stats["user_profile_deleted"] = db.query(UserProfile).filter(UserProfile.id == user.id).delete()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "User data successfully deleted",
        "statistics": stats
    }
