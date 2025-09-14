"""
Unit tests for Message Service functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from utils.message_service import MessageService
from models import MessageJob, JobStatus


class TestMessageService:
    """Test message service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        MessageService.message_jobs.clear()
    
    def teardown_method(self):
        """Cleanup after tests"""
        MessageService.message_jobs.clear()
    
    @pytest.mark.asyncio
    async def test_create_message_job(self):
        """Test message job creation"""
        with patch('asyncio.create_task') as mock_task:
            job_id = await MessageService.create_message_job("Hello world")
            
            assert job_id is not None
            assert job_id in MessageService.message_jobs
            
            job = MessageService.message_jobs[job_id]
            assert job.user_message == "Hello world"
            assert job.status == JobStatus.PENDING
            assert job.ai_response is None
            
            # Should start background processing
            mock_task.assert_called_once()
    
    def test_get_message_job(self):
        """Test retrieving message job by ID"""
        # Create test job directly
        job = MessageJob(
            id="test-job",
            user_message="Test message",
            status=JobStatus.DONE,
            created_at=datetime.utcnow()
        )
        MessageService.message_jobs["test-job"] = job
        
        retrieved_job = MessageService.get_message_job("test-job")
        assert retrieved_job is not None
        assert retrieved_job.id == "test-job"
        
        # Test non-existent job
        non_existent = MessageService.get_message_job("non-existent")
        assert non_existent is None
    
    def test_build_chat_history(self):
        """Test chat history building logic"""
        # Add some completed message jobs
        for i in range(3):
            job = MessageJob(
                id=f"msg-{i}",
                user_message=f"Message {i}",
                ai_response=f"Response {i}",
                status=JobStatus.DONE,
                created_at=datetime.utcnow()
            )
            MessageService.message_jobs[f"msg-{i}"] = job
        
        # Add one pending job (should be excluded)
        pending_job = MessageJob(
            id="pending",
            user_message="Pending message",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        MessageService.message_jobs["pending"] = pending_job
        
        chat_history = MessageService._build_chat_history()
        
        # Should only include completed jobs
        assert len(chat_history) == 3
        assert all(msg["status"] == "done" for msg in chat_history)
        assert all(msg["type"] == "message" for msg in chat_history)
        
        # Should exclude specific job ID if provided
        chat_history_excluding = MessageService._build_chat_history("msg-1")
        assert len(chat_history_excluding) == 2
        assert not any(msg["user_message"] == "Message 1" for msg in chat_history_excluding)
    
    def test_clear_all_message_jobs(self):
        """Test clearing all message jobs"""
        # Add test jobs
        for i in range(3):
            job = MessageJob(
                id=f"job-{i}",
                user_message=f"Message {i}",
                status=JobStatus.DONE,
                created_at=datetime.utcnow()
            )
            MessageService.message_jobs[f"job-{i}"] = job
        
        assert len(MessageService.message_jobs) == 3
        
        MessageService.clear_all_message_jobs()
        assert len(MessageService.message_jobs) == 0
    
    def test_get_all_message_jobs(self):
        """Test getting all message jobs"""
        # Add test jobs
        for i in range(2):
            job = MessageJob(
                id=f"job-{i}",
                user_message=f"Message {i}",
                status=JobStatus.DONE,
                created_at=datetime.utcnow()
            )
            MessageService.message_jobs[f"job-{i}"] = job
        
        all_jobs = MessageService.get_all_message_jobs()
        assert len(all_jobs) == 2
        assert isinstance(all_jobs, dict)
        
        # Should be a copy, not the original
        all_jobs.clear()
        assert len(MessageService.message_jobs) == 2  # Original unchanged
    
    @pytest.mark.asyncio
    async def test_process_message_job_background_success(self):
        """Test successful message job processing"""
        # Create test job
        job = MessageJob(
            id="test-job",
            user_message="Hello AI",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        MessageService.message_jobs["test-job"] = job
        
        with patch('services.AIProcessor.get_ai_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "Hello human!"
            
            await MessageService.process_message_job_background("test-job")
            
            # Check job was updated
            processed_job = MessageService.message_jobs["test-job"]
            assert processed_job.status == JobStatus.DONE
            assert processed_job.ai_response == "Hello human!"
            assert processed_job.completed_at is not None
    
    @pytest.mark.asyncio 
    async def test_process_message_job_background_error(self):
        """Test message job processing with error"""
        # Create test job
        job = MessageJob(
            id="error-job",
            user_message="This will fail",
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        MessageService.message_jobs["error-job"] = job
        
        with patch('services.AIProcessor.get_ai_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.side_effect = Exception("AI service failed")
            
            await MessageService.process_message_job_background("error-job")
            
            # Check job was marked as error
            processed_job = MessageService.message_jobs["error-job"]
            assert processed_job.status == JobStatus.ERROR
            assert "Error processing message" in processed_job.ai_response
            assert processed_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_process_nonexistent_job(self):
        """Test processing non-existent job ID"""
        # Should not raise error
        await MessageService.process_message_job_background("non-existent")
        
        # No jobs should be created
        assert len(MessageService.message_jobs) == 0
