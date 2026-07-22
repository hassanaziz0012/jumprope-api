from fastapi import FastAPI
from dotenv import load_dotenv
from routes import ai, sync, conversations, auth
from utils import logger
from sqladmin import Admin
from database import engine
from admin import (
    WorkoutAdmin,
    GoalAdmin,
    ChartAdmin,
    UserProfileAdmin,
    RestDayAdmin,
    ConversationAdmin,
    ConversationMessageAdmin,
)
import os

load_dotenv()

logger.info("Application starting up...")

app = FastAPI(
    title="JumpRope API",
    description="Backend API for JumpRope Tracker",
    version="0.1.0",
)

admin = Admin(app, engine)
admin.add_view(WorkoutAdmin)
admin.add_view(GoalAdmin)
admin.add_view(ChartAdmin)
admin.add_view(UserProfileAdmin)
admin.add_view(RestDayAdmin)
admin.add_view(ConversationAdmin)
admin.add_view(ConversationMessageAdmin)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ai.router, tags=["AI Agent"])
app.include_router(sync.router, prefix="/sync", tags=["Data Sync"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
