"""
Job models for tracking message and file processing
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .enums import JobStatus


class MessageJob(BaseModel):
    """Model for tracking message processing jobs"""
    id: str
    user_message: str
    ai_response: Optional[str] = None
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class FileJob(BaseModel):
    """Model for tracking file processing jobs"""
    id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    analysis_result: Optional[str] = None
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
