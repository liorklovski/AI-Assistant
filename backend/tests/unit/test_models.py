"""
Unit tests for data models and enums
"""

import pytest
from datetime import datetime
from models import JobStatus, JobType, MessageJob, FileJob, MessageRequest, UnifiedJobResponse


class TestEnums:
    """Test enum definitions"""
    
    def test_job_status_values(self):
        """Test JobStatus enum has correct values"""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.PROCESSING == "processing"
        assert JobStatus.DONE == "done"
        assert JobStatus.ERROR == "error"
    
    def test_job_type_values(self):
        """Test JobType enum has correct values"""
        assert JobType.MESSAGE == "message"
        assert JobType.FILE == "file"


class TestModels:
    """Test Pydantic model validation and creation"""
    
    def test_message_request_validation(self):
        """Test MessageRequest model validation"""
        # Valid request
        request = MessageRequest(message="Hello world")
        assert request.message == "Hello world"
        
        # Empty message should still work (validation happens at API level)
        empty_request = MessageRequest(message="")
        assert empty_request.message == ""
    
    def test_message_job_creation(self):
        """Test MessageJob model creation and validation"""
        now = datetime.utcnow()
        
        job = MessageJob(
            id="test-123",
            user_message="Test message",
            status=JobStatus.PENDING,
            created_at=now
        )
        
        assert job.id == "test-123"
        assert job.user_message == "Test message"
        assert job.status == JobStatus.PENDING
        assert job.ai_response is None
        assert job.created_at == now
        assert job.completed_at is None
    
    def test_file_job_creation(self):
        """Test FileJob model creation and validation"""
        now = datetime.utcnow()
        
        job = FileJob(
            id="file-123",
            original_filename="test.txt",
            stored_filename="uuid-test.txt",
            file_type=".txt",
            file_size=1024,
            status=JobStatus.PENDING,
            created_at=now
        )
        
        assert job.id == "file-123"
        assert job.original_filename == "test.txt"
        assert job.stored_filename == "uuid-test.txt"
        assert job.file_type == ".txt"
        assert job.file_size == 1024
        assert job.status == JobStatus.PENDING
        assert job.analysis_result is None
    
    def test_unified_job_response_message(self):
        """Test UnifiedJobResponse for message jobs"""
        now = datetime.utcnow()
        
        response = UnifiedJobResponse(
            job_id="msg-123",
            status=JobStatus.DONE,
            job_type="message",
            user_message="Hello",
            ai_response="Hi there!",
            created_at=now
        )
        
        assert response.job_id == "msg-123"
        assert response.status == JobStatus.DONE
        assert response.job_type == "message"
        assert response.user_message == "Hello"
        assert response.ai_response == "Hi there!"
        assert response.original_filename is None
    
    def test_unified_job_response_file(self):
        """Test UnifiedJobResponse for file jobs"""
        now = datetime.utcnow()
        
        response = UnifiedJobResponse(
            job_id="file-123",
            status=JobStatus.DONE,
            job_type="file",
            original_filename="document.pdf",
            file_type=".pdf",
            file_size=2048,
            analysis_result="Document analysis completed",
            created_at=now
        )
        
        assert response.job_id == "file-123"
        assert response.status == JobStatus.DONE
        assert response.job_type == "file"
        assert response.original_filename == "document.pdf"
        assert response.file_type == ".pdf"
        assert response.file_size == 2048
        assert response.analysis_result == "Document analysis completed"
        assert response.user_message is None
