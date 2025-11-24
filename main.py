"""Tic Tac Toe FastAPI Application."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router as api_router
from app.websocket import router as ws_router

# Create FastAPI application
app = FastAPI(title="Tic Tac Toe API")

# Include routers
app.include_router(api_router)
app.include_router(ws_router)

# Mount static files (must be last to avoid route conflicts)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
