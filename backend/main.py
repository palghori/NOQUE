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

# Read allowed origins from environment, fallback to localhost for dev
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    await init_db()
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
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
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
