from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserProfileSchema(BaseModel):
    id: Optional[int] = None
    sync_token: str
    name: str
    email: Optional[str] = None
    image: Optional[str] = None
    ai_enabled: Optional[bool] = False
    api_key: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    ai_enabled: Optional[bool] = False
    sync_token: Optional[str] = None

class SignInRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str

class AuthResponse(BaseModel):
    status: str
    sync_token: str
    name: str
    email: Optional[str] = None
    ai_enabled: bool = False

class WorkoutSchema(BaseModel):
    id: int
    date: datetime
    duration: int
    total_skips: int
    avg_skips_per_minute: Optional[float] = None
    trips: int = 0
    calories: Optional[float] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    notes: Optional[str] = None

class GoalSchema(BaseModel):
    id: int
    daily_skips: Optional[int] = None
    weekly_skips: Optional[int] = None
    weekly_workouts: Optional[int] = None
    daily_calories: Optional[int] = None
    weekly_calories: Optional[int] = None
    weekly_duration: Optional[int] = None
    skip_rate_goal: Optional[float] = None

class RestDaySchema(BaseModel):
    date: str

class ChartSchema(BaseModel):
    id: int
    metric: str
    time_range: str
    type: str

class SyncWorkoutsRequest(BaseModel):
    user: UserProfileSchema
    data: List[WorkoutSchema]

class SyncGoalsRequest(BaseModel):
    user: UserProfileSchema
    data: List[GoalSchema]

class SyncRestDaysRequest(BaseModel):
    user: UserProfileSchema
    data: List[RestDaySchema]

class SyncChartsRequest(BaseModel):
    user: UserProfileSchema
    data: List[ChartSchema]
