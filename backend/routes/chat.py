"""
Chat history and management endpoints
"""

from fastapi import APIRouter

from utils import MessageService
from services import FileService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history")
async def get_chat_history():
    """Get all messages and files for frontend persistence"""
    all_items = []
    
    # Add message jobs
    message_jobs = MessageService.get_all_message_jobs()
    for job in message_jobs.values():
        all_items.append({
            "id": job.id,
            "type": "message", 
            "user_message": job.user_message,
            "ai_response": job.ai_response,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })
    
    # Add file jobs  
    file_jobs = FileService.get_all_file_jobs()
    for job in file_jobs.values():
        all_items.append({
            "id": job.id,
            "type": "file",
            "original_filename": job.original_filename,
            "file_type": job.file_type,
            "file_size": job.file_size,
            "analysis_result": job.analysis_result,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })
    
    # Sort by creation time
    all_items.sort(key=lambda x: x['created_at'])
    
    return {
        "success": True,
        "messages": all_items
    }


@router.delete("/clear")
async def clear_all_chat():
    """Clear all messages and files from memory"""
    # Clear all jobs and clean up files
    MessageService.clear_all_message_jobs()
    FileService.clear_all_file_jobs()
    
    return {
        "success": True,
        "message": "Chat history cleared successfully"
    }
