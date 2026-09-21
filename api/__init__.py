# api/__init__.py
"""FastAPI application entry point.
Implements the endpoints defined in Phase P4.
Uses SQLite (stdlib) for persistent storage of scenarios and runs.
All paths are relative to the project root.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import router

app = FastAPI(title="DVRP Lab API", version="0.1.0")
origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS","*").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(router, prefix="/api/v1")
