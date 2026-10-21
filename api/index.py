"""
Vercel Serverless Function Entrypoint for AICTE ONE FastAPI Backend
"""
import sys
import os

# Add root directory to python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app

# Vercel ASGI handler
handler = app
