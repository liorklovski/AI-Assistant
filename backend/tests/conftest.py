"""
Pytest configuration and shared fixtures
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock

from main import app
from models import MessageJob, FileJob, JobStatus
from utils.message_service import MessageService
from services.file_service import FileService


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_message_job():
    """Sample message job for testing"""
    return MessageJob(
        id="test-message-123",
        user_message="Hello, this is a test message",
        ai_response="Hello! I'm a test AI response.",
        status=JobStatus.DONE,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )


@pytest.fixture  
def sample_file_job():
    """Sample file job for testing"""
    return FileJob(
        id="test-file-456",
        original_filename="test_document.pdf",
        stored_filename="uuid-test-document.pdf",
        file_type=".pdf",
        file_size=2048,
        analysis_result="This is a test PDF document analysis.",
        status=JobStatus.DONE,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_upload_file():
    """Mock UploadFile for testing"""
    mock_file = Mock()
    mock_file.filename = "test.txt"
    mock_file.size = 1024
    mock_file.read = Mock(return_value=b"test file content")
    return mock_file


@pytest.fixture
def conversation_history():
    """Sample conversation history for context testing"""
    return [
        {
            "type": "message",
            "user_message": "Hi, my name is TestUser",
            "ai_response": "Nice to meet you TestUser!",
            "status": "done",
            "created_at": "2024-01-01T10:00:00"
        },
        {
            "type": "message",
            "user_message": "I love programming and AI",
            "ai_response": "That's wonderful! Programming and AI are fascinating fields.",
            "status": "done", 
            "created_at": "2024-01-01T10:01:00"
        },
        {
            "type": "file",
            "original_filename": "data.csv",
            "file_type": ".csv",
            "file_size": 1024,
            "analysis_result": "CSV contains data analysis results",
            "status": "done",
            "created_at": "2024-01-01T10:02:00"
        }
    ]


@pytest.fixture(autouse=True)
def cleanup_jobs():
    """Automatically cleanup jobs after each test"""
    yield
    # Cleanup after test
    MessageService.message_jobs.clear()
    FileService.file_jobs.clear()


@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing"""
    return "This is a mocked AI response for testing purposes."


@pytest.fixture
def test_config():
    """Test configuration values"""
    return {
        "GEMINI_API_KEY": "test-gemini-key",
        "DEEPAI_API_KEY": "test-deepai-key",
        "USE_DUMMY_AI": True,
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
        "ALLOWED_FILE_TYPES": {'.txt', '.pdf', '.jpg', '.png'}
    }
