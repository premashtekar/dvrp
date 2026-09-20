# api/main.py
"""FastAPI entry point.
Run with:
    uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from . import app  # re-export FastAPI instance defined in api/__init__.py
