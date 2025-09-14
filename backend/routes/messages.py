"""
Message processing endpoints
"""

from fastapi import APIRouter, HTTPException

from models import MessageRequest, UnifiedJobResponse
from utils import MessageService
from services import FileService

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=dict)
async def create_message_job(request: MessageRequest):
    """Submit user message and create processing job"""
    try:
        # Validate input
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Create new job
        job_id = await MessageService.create_message_job(request.message.strip())
        
        return {"job_id": job_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=UnifiedJobResponse)
async def get_job(job_id: str):
    """Get status and result of message or file job"""
    try:
        job = MessageService.get_message_job(job_id)
        if job:
            return UnifiedJobResponse(
                job_id=job.id,
                status=job.status,
                job_type="message",
                user_message=job.user_message,
                ai_response=job.ai_response,
                created_at=job.created_at,
                completed_at=job.completed_at
            )
        
        # Check if it's a file job
        file_job = FileService.get_file_job(job_id)
        if file_job:
            return UnifiedJobResponse(
                job_id=file_job.id,
                status=file_job.status,
                job_type="file",
                original_filename=file_job.original_filename,
                file_type=file_job.file_type,
                file_size=file_job.file_size,
                analysis_result=file_job.analysis_result,
                created_at=file_job.created_at,
                completed_at=file_job.completed_at
            )
            
        raise HTTPException(status_code=404, detail="Job not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_all_jobs():
    """List all jobs (for debugging/monitoring)"""
    message_jobs = MessageService.get_all_message_jobs()
    file_jobs = FileService.get_all_file_jobs()
    
    message_job_list = [
        {
            "job_id": job.id,
            "type": "message",
            "status": job.status,
            "content": job.user_message[:50] + "..." if len(job.user_message) > 50 else job.user_message,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
        for job in message_jobs.values()
    ]
    
    file_job_list = [
        {
            "job_id": job.id,
            "type": "file",
            "status": job.status,
            "content": f"{job.original_filename} ({job.file_size} bytes)",
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
        for job in file_jobs.values()
    ]
    
    return {
        "total_message_jobs": len(message_jobs),
        "total_file_jobs": len(file_jobs),
        "jobs": sorted(
            message_job_list + file_job_list,
            key=lambda x: x['created_at'],
            reverse=True
        )
    }


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (cleanup)"""
    message_jobs = MessageService.get_all_message_jobs()
    file_jobs = FileService.get_all_file_jobs()
    
    if job_id in message_jobs:
        del MessageService.message_jobs[job_id]
        return {"message": "Message job deleted successfully"}
    elif job_id in file_jobs:
        # Clean up file if it still exists
        job = file_jobs[job_id]
        FileService._cleanup_file(job.stored_filename)
        
        del FileService.file_jobs[job_id]
        return {"message": "File job deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")
