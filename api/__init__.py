# api/__init__.py
"""FastAPI application entry point.
Implements the endpoints defined in Phase P4.
Uses SQLite (stdlib) for persistent storage of scenarios and runs.
All paths are relative to the project root.
"""

from fastapi import FastAPI
from .routers import router

app = FastAPI(title="DVRP Lab API", version="0.1.0")
app.include_router(router, prefix="/api/v1")
