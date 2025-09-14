"""
Routes package for AI Chat Assistant API endpoints
"""

from .health import router as health_router
from .messages import router as messages_router
from .files import router as files_router  
from .chat import router as chat_router
from .test import router as test_router

__all__ = [
    "health_router",
    "messages_router", 
    "files_router",
    "chat_router",
    "test_router"
]
