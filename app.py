from fastapi import FastAPI
from dotenv import load_dotenv
from routes import router
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
print(os.getenv("GEMINI_API_KEY_1"))

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

app.include_router(router)
