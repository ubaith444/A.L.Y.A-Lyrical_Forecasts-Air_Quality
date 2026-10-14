"""
FastAPI entry point alias for Render deployment.
Supports: uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

import sys
import os

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workspace_dir = os.path.dirname(backend_dir)
for p in [backend_dir, workspace_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.main import app
except ImportError:
    from main import app

__all__ = ["app"]
