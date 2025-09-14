"""
File Service for handling file uploads, validation, and processing
"""

import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from fastapi import UploadFile
import aiofiles

from models import FileJob, JobStatus
from core.constants import MAX_FILE_SIZE, ALLOWED_FILE_TYPES, UPLOAD_DIRECTORY
from .ai_processor import AIProcessor
from utils.logger import file_logger


class FileService:
    """Service for handling file operations"""
    
    # In-memory file job store (MVP - use database in production)
    file_jobs: Dict[str, FileJob] = {}
    
    @staticmethod
    def validate_file(file: UploadFile) -> Optional[str]:
        """Validate uploaded file and return error message if invalid"""
        # Check file size
        if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
            return f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        
        # Check file extension
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in ALLOWED_FILE_TYPES:
                allowed_types = ', '.join(sorted(ALLOWED_FILE_TYPES))
                return f"File type '{file_extension}' not supported. Allowed types: {allowed_types}"
        else:
            return "Filename is required"
        
        return None
    
    @staticmethod
    async def save_file(file: UploadFile) -> tuple[str, str, int]:
        """
        Save uploaded file to disk and return (stored_filename, file_type, file_size)
        """
        # Generate unique filename to prevent conflicts
        original_filename = file.filename or "unknown"
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = Path(UPLOAD_DIRECTORY) / unique_filename
        
        # Save file
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            file_size = len(content)
            await f.write(content)
        
        return unique_filename, file_extension, file_size
    
    @staticmethod
    async def create_file_job(original_filename: str, stored_filename: str, file_type: str, file_size: int) -> str:
        """Create a new file processing job and return job ID"""
        job_id = str(uuid.uuid4())
        
        # Create file job
        file_job = FileJob(
            id=job_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=file_type,
            file_size=file_size,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        FileService.file_jobs[job_id] = file_job
        
        # Start background processing
        asyncio.create_task(FileService.process_file_job_background(job_id))
        
        return job_id
    
    @staticmethod
    async def process_file_job_background(job_id: str):
        """Background task to process file job"""
        try:
            job = FileService.file_jobs.get(job_id)
            if not job:
                return
                
            # Update status to processing
            job.status = JobStatus.PROCESSING
            
            # Get file analysis
            file_path = Path(UPLOAD_DIRECTORY) / job.stored_filename
            analysis_result = await AIProcessor.get_file_analysis(
                job.original_filename, job.file_type, job.file_size, str(file_path)
            )
            
            # Update job with result
            job.analysis_result = analysis_result
            job.status = JobStatus.DONE
            job.completed_at = datetime.utcnow()
            
            # Clean up file after processing (for MVP)
            FileService._cleanup_file(job.stored_filename)
            
        except Exception as e:
            # Handle errors
            if job_id in FileService.file_jobs:
                FileService.file_jobs[job_id].status = JobStatus.ERROR
                FileService.file_jobs[job_id].analysis_result = f"Error processing file: {str(e)}"
                FileService.file_jobs[job_id].completed_at = datetime.utcnow()
    
    @staticmethod
    def _cleanup_file(stored_filename: str):
        """Clean up uploaded file"""
        try:
            file_path = Path(UPLOAD_DIRECTORY) / stored_filename
            if file_path.exists():
                file_path.unlink()
                file_logger.info(f"Cleaned up file: {stored_filename}")
        except Exception as e:
            file_logger.warning(f"Failed to cleanup file {stored_filename}: {str(e)}")
    
    @staticmethod
    def get_file_job(job_id: str) -> Optional[FileJob]:
        """Get file job by ID"""
        return FileService.file_jobs.get(job_id)
    
    @staticmethod
    def get_all_file_jobs() -> Dict[str, FileJob]:
        """Get all file jobs"""
        return FileService.file_jobs.copy()
    
    @staticmethod
    def clear_all_file_jobs():
        """Clear all file jobs and clean up files"""
        # Clean up any remaining files
        for job in FileService.file_jobs.values():
            FileService._cleanup_file(job.stored_filename)
        
        # Clear the jobs dictionary
        FileService.file_jobs.clear()
        file_logger.info("Cleared all file jobs and cleaned up files")
