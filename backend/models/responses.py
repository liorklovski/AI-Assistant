"""
Response models for the AI Chat Assistant API
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .enums import JobStatus


class MessageResponse(BaseModel):
    """Response model for message jobs"""
    job_id: str
    status: JobStatus
    user_message: str
    ai_response: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class FileResponse(BaseModel):
    """Response model for file jobs"""
    job_id: str
    status: JobStatus
    original_filename: str
    file_type: str
    file_size: int
    analysis_result: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class UnifiedJobResponse(BaseModel):
    """Unified response model for both message and file jobs"""
    job_id: str
    status: JobStatus
    job_type: str  # "message" or "file"
    # Message fields
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    # File fields  
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    analysis_result: Optional[str] = None
    # Common fields
    created_at: datetime
    completed_at: Optional[datetime] = None
