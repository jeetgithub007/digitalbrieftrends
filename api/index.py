"""
Vercel serverless entry point.
Exposes the FastAPI `app` at top level for Vercel's Python runtime.
"""
import sys
import os

# Add the project root to Python path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app  # noqa: E402, F401 — FastAPI app instance
