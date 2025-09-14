"""
Request models for the AI Chat Assistant API
"""

from pydantic import BaseModel


class MessageRequest(BaseModel):
    """Request model for sending a message"""
    message: str
