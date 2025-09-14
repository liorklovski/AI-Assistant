"""
Unit tests for File Service functionality
"""

import pytest
from unittest.mock import Mock, patch, mock_open, AsyncMock
from pathlib import Path
import tempfile
import os
from datetime import datetime

from services.file_service import FileService
from models import FileJob, JobStatus
from core.constants import MAX_FILE_SIZE, ALLOWED_FILE_TYPES


class TestFileValidation:
    """Test file validation logic"""
    
    def test_validate_file_valid_type(self):
        """Test validation passes for allowed file types"""
        # Mock file object
        mock_file = Mock()
        mock_file.filename = "document.pdf"
        mock_file.size = 1024  # 1KB
        
        result = FileService.validate_file(mock_file)
        assert result is None  # No error
    
    def test_validate_file_invalid_type(self):
        """Test validation fails for disallowed file types"""
        mock_file = Mock()
        mock_file.filename = "malware.exe"
        mock_file.size = 1024
        
        result = FileService.validate_file(mock_file)
        assert result is not None
        assert "not supported" in result
        assert ".exe" in result
    
    def test_validate_file_too_large(self):
        """Test validation fails for oversized files"""
        mock_file = Mock()
        mock_file.filename = "huge_file.txt"
        mock_file.size = MAX_FILE_SIZE + 1  # Just over the limit
        
        result = FileService.validate_file(mock_file)
        assert result is not None
        assert "exceeds maximum" in result
    
    def test_validate_file_no_filename(self):
        """Test validation fails when no filename provided"""
        mock_file = Mock()
        mock_file.filename = None
        mock_file.size = 1024
        
        result = FileService.validate_file(mock_file)
        assert result is not None
        assert "Filename is required" in result
    
    def test_allowed_file_types_coverage(self):
        """Test all allowed file types are properly validated"""
        for file_type in ALLOWED_FILE_TYPES:
            mock_file = Mock()
            mock_file.filename = f"test{file_type}"
            mock_file.size = 1024
            
            result = FileService.validate_file(mock_file)
            assert result is None, f"File type {file_type} should be allowed"


class TestFileOperations:
    """Test file operations and job management"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear any existing jobs
        FileService.file_jobs.clear()
    
    def teardown_method(self):
        """Cleanup after tests"""
        FileService.file_jobs.clear()
    
    @pytest.mark.asyncio
    async def test_save_file(self):
        """Test file saving functionality"""
        # Mock file object
        mock_file = Mock()
        mock_file.filename = "test_document.pdf"
        mock_file.read = AsyncMock(return_value=b"fake file content")
        
        # Mock aiofiles with proper async context manager
        mock_async_file = AsyncMock()
        mock_async_file.write = AsyncMock()
        
        with patch("aiofiles.open", return_value=mock_async_file):
            stored_filename, file_type, file_size = await FileService.save_file(mock_file)
            
            assert file_type == ".pdf"
            assert file_size == len(b"fake file content")
            assert stored_filename.endswith(".pdf")
            assert stored_filename != mock_file.filename  # Should be unique
    
    @pytest.mark.asyncio
    async def test_create_file_job(self):
        """Test file job creation"""
        with patch('asyncio.create_task') as mock_task:
            job_id = await FileService.create_file_job(
                original_filename="test.txt",
                stored_filename="uuid-test.txt", 
                file_type=".txt",
                file_size=100
            )
            
            assert job_id is not None
            assert job_id in FileService.file_jobs
            
            job = FileService.file_jobs[job_id]
            assert job.original_filename == "test.txt"
            assert job.stored_filename == "uuid-test.txt"
            assert job.file_type == ".txt"
            assert job.file_size == 100
            assert job.status == JobStatus.PENDING
            
            # Should start background processing
            mock_task.assert_called_once()
    
    def test_get_file_job(self):
        """Test retrieving file job by ID"""
        # Create a test job directly
        job = FileJob(
            id="test-job",
            original_filename="test.txt",
            stored_filename="stored.txt",
            file_type=".txt",
            file_size=100,
            status=JobStatus.DONE,
            created_at=datetime.utcnow()
        )
        FileService.file_jobs["test-job"] = job
        
        retrieved_job = FileService.get_file_job("test-job")
        assert retrieved_job is not None
        assert retrieved_job.id == "test-job"
        
        # Test non-existent job
        non_existent = FileService.get_file_job("non-existent")
        assert non_existent is None
    
    def test_clear_all_file_jobs(self):
        """Test clearing all file jobs"""
        # Add some test jobs
        for i in range(3):
            job = FileJob(
                id=f"job-{i}",
                original_filename=f"file{i}.txt",
                stored_filename=f"stored{i}.txt",
                file_type=".txt",
                file_size=100,
                status=JobStatus.DONE,
                created_at=datetime.utcnow()
            )
            FileService.file_jobs[f"job-{i}"] = job
        
        assert len(FileService.file_jobs) == 3
        
        with patch.object(FileService, '_cleanup_file') as mock_cleanup:
            FileService.clear_all_file_jobs()
            
            assert len(FileService.file_jobs) == 0
            assert mock_cleanup.call_count == 3  # Should cleanup all files
    
    def test_file_cleanup(self):
        """Test file cleanup functionality"""
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.unlink") as mock_unlink:
            
            FileService._cleanup_file("test-file.txt")
            mock_unlink.assert_called_once()
    
    def test_file_cleanup_missing_file(self):
        """Test file cleanup when file doesn't exist"""
        with patch("pathlib.Path.exists", return_value=False), \
             patch("pathlib.Path.unlink") as mock_unlink:
            
            # Should not raise error
            FileService._cleanup_file("non-existent.txt")
            mock_unlink.assert_not_called()
