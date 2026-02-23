from fastapi import FastAPI
from dotenv import load_dotenv
from routes import router
import os

load_dotenv()
print(os.getenv("GEMINI_API_KEY_1"))

app = FastAPI(
    title="JumpRope API",
    description="Backend API for JumpRope Tracker",
    version="0.1.0",
)

app.include_router(router)
