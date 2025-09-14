"""
Message Service for handling message processing and storage
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from models import MessageJob, JobStatus
from services import AIProcessor
from services.file_service import FileService
from utils.logger import ai_logger


class MessageService:
    """Service for handling message operations"""
    
    # In-memory message job store (MVP - use database in production)
    message_jobs: Dict[str, MessageJob] = {}
    
    @staticmethod
    async def create_message_job(user_message: str) -> str:
        """Create a new message processing job and return job ID"""
        job_id = str(uuid.uuid4())
        
        # Create message job
        message_job = MessageJob(
            id=job_id,
            user_message=user_message,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        MessageService.message_jobs[job_id] = message_job
        
        # Start background processing
        asyncio.create_task(MessageService.process_message_job_background(job_id))
        
        return job_id
    
    @staticmethod
    async def process_message_job_background(job_id: str):
        """Background task to process message job with chat history context"""
        try:
            job = MessageService.message_jobs.get(job_id)
            if not job:
                return
                
            # Update status to processing
            job.status = JobStatus.PROCESSING
            
            # Build chat history for context (exclude current message)
            chat_history = MessageService._build_chat_history(job_id)
            
            # Log context information
            ai_logger.info(f"Processing message with {len(chat_history)} context items")
            if chat_history:
                last_item = chat_history[-1]
                if last_item.get('user_message'):
                    ai_logger.debug(f"Last context item: {last_item['user_message']}")
                else:
                    ai_logger.debug(f"Last context item: File: {last_item.get('original_filename', 'unknown')}")
            
            # Get AI response with full context
            ai_response = await AIProcessor.get_ai_response(job.user_message, chat_history)
            
            # Update job with result
            job.ai_response = ai_response
            job.status = JobStatus.DONE
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            # Handle errors
            if job_id in MessageService.message_jobs:
                MessageService.message_jobs[job_id].status = JobStatus.ERROR
                MessageService.message_jobs[job_id].ai_response = f"Error processing message: {str(e)}"
                MessageService.message_jobs[job_id].completed_at = datetime.utcnow()
    
    @staticmethod
    def _build_chat_history(exclude_job_id: str = None) -> List[dict]:
        """Build chat history for AI context"""
        chat_history = []
        
        # Get all previous messages (completed ones)
        all_messages = []
        for msg_job in MessageService.message_jobs.values():
            if msg_job.id != exclude_job_id and msg_job.status == JobStatus.DONE:
                all_messages.append({
                    'type': 'message',
                    'user_message': msg_job.user_message,
                    'ai_response': msg_job.ai_response,
                    'status': 'done',
                    'created_at': msg_job.created_at.isoformat()
                })
        
        # Get all previous file jobs (completed ones)
        for file_job in FileService.file_jobs.values():
            if file_job.status == JobStatus.DONE:
                all_messages.append({
                    'type': 'file',
                    'original_filename': file_job.original_filename,
                    'file_type': file_job.file_type,
                    'file_size': file_job.file_size,
                    'analysis_result': file_job.analysis_result,
                    'status': 'done',
                    'created_at': file_job.created_at.isoformat()
                })
        
        # Sort by creation time to get chronological order
        chat_history = sorted(all_messages, key=lambda x: x['created_at'])
        
        return chat_history
    
    @staticmethod
    def get_message_job(job_id: str) -> Optional[MessageJob]:
        """Get message job by ID"""
        return MessageService.message_jobs.get(job_id)
    
    @staticmethod
    def get_all_message_jobs() -> Dict[str, MessageJob]:
        """Get all message jobs"""
        return MessageService.message_jobs.copy()
    
    @staticmethod
    def clear_all_message_jobs():
        """Clear all message jobs"""
        MessageService.message_jobs.clear()
        ai_logger.info("Cleared all message jobs")
