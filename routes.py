from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from ai.gemini import ask_gemini

# Models and Schemas
from models.user_profile import UserProfile
from models.workout import Workout
from models.goal import Goal
from models.rest_day import RestDay
from models.chart import Chart
from schemas import (
    SyncWorkoutsRequest,
    SyncGoalsRequest,
    SyncRestDaysRequest,
    SyncChartsRequest
)

router = APIRouter()

class AskAgentRequest(BaseModel):
    message: str

@router.post("/ask-agent")
def ask_agent(request: AskAgentRequest):
    response = ask_gemini(request.message)
    return {"response": response}

def sync_user_profile(db: Session, user_data):
    user = db.query(UserProfile).filter(UserProfile.id == user_data.id).first()
    if user:
        for key, value in user_data.model_dump().items():
            setattr(user, key, value)
    else:
        user = UserProfile(**user_data.model_dump())
        db.add(user)
    db.commit()
    return user

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
