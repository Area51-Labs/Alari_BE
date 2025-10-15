"""
User Backend - Main FastAPI Application Entry Point
Handles authentication, user data, goals, and conversations.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS
)
from database import init_db
from routes import auth_routes, goals, conversations, db_health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown logic."""
    logger.info("Starting User Backend...")
    
    # Initialize database tables
    init_db()
    logger.info("Database initialized")
    
    yield
    
    logger.info("Shutting down User Backend")


# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
app.include_router(goals.router, prefix="/goals", tags=["Goals"])
app.include_router(db_health.router, prefix="/db", tags=["Database Health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Alari User Backend",
        "version": API_VERSION,
        "status": "running",
        "description": "User authentication and data management"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )