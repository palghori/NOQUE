"""
NOQUE — AI-Powered Legacy Codebase Explainer & Modernizer
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from db import init_db
from routers.jobs import router as jobs_router

# Read allowed origins from environment, fallback to wildcard for easy deployment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    from config import get_settings
    settings = get_settings()
    db_url = settings.async_database_url
    # Mask the password in the URL for logging
    masked = db_url
    if "@" in db_url:
        prefix = db_url.split("://")[0]
        after_at = db_url.split("@")[1]
        masked = f"{prefix}://***:***@{after_at}"
    print(f"[NOQUE] Database URL: {masked}")
    print(f"[NOQUE] Gemini Model: {settings.GEMINI_MODEL}")
    print(f"[NOQUE] Gemini API Key set: {bool(settings.GEMINI_API_KEY)}")
    await init_db()
    print(f"[NOQUE] Database tables initialized successfully")
    yield


app = FastAPI(
    title="NOQUE API",
    description="AI-Powered Legacy Codebase Explainer & Modernizer",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs_router)


@app.get("/")
async def root():
    return {"message": "NOQUE API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
