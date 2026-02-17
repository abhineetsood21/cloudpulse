"""
CloudPulse - AWS Cost Monitoring API

Main FastAPI application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.api.v2 import v2_router
from app.api.schemas import HealthResponse
from app.core.config import get_settings
from app.core.database import engine, Base

# Import all models so Base.metadata.create_all() discovers every table
import app.models.models  # noqa: F401
import app.models.v2  # noqa: F401
import app.models.providers  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="CloudPulse",
    description="Simple, affordable AWS cost monitoring for startups and small teams.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CloudFormation templates, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")


@app.on_event("startup")
async def on_startup():
    """Create database tables on startup if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "CloudPulse",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
