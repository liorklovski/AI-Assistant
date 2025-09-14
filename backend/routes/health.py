"""
Health check endpoints
"""

from datetime import datetime
from fastapi import APIRouter

from utils import MessageService
from services import FileService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "active_message_jobs": len(MessageService.message_jobs),
        "active_file_jobs": len(FileService.file_jobs)
    }
