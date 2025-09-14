"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from main import app


class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "active_message_jobs" in data
        assert "active_file_jobs" in data
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Chat Assistant MVP"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "features" in data
        assert "Smart context management" in data["features"]
    
    def test_create_message_job(self):
        """Test message job creation endpoint"""
        response = self.client.post(
            "/messages",
            json={"message": "Hello AI"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
    
    def test_create_message_job_empty_message(self):
        """Test message job creation with empty message"""
        response = self.client.post(
            "/messages",
            json={"message": ""}
        )
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]
    
    def test_create_message_job_invalid_payload(self):
        """Test message job creation with invalid payload"""
        response = self.client.post(
            "/messages",
            json={"invalid": "field"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_message_job_not_found(self):
        """Test getting non-existent message job"""
        response = self.client.get("/messages/non-existent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_chat_history_empty(self):
        """Test chat history when no messages exist"""
        # Clear any existing data
        self.client.delete("/chat/clear")
        
        response = self.client.get("/chat/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["messages"] == []
    
    def test_clear_chat_history(self):
        """Test clearing chat history"""
        response = self.client.delete("/chat/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cleared successfully" in data["message"]
    
    def test_context_analytics_empty(self):
        """Test context analytics with no messages"""
        # Clear chat first
        self.client.delete("/chat/clear")
        
        response = self.client.get("/context/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_messages"] == 0
        assert "No messages to analyze" in data["context_optimization"]
        assert data["user_info"] == {}
    
    def test_context_optimization(self):
        """Test context optimization endpoint"""
        response = self.client.post("/context/optimize")
        
        assert response.status_code == 200
        data = response.json()
        assert "test_message" in data
        assert "original_context" in data
        assert "optimized_context" in data
        assert "compression_ratio" in data
    
    @pytest.mark.asyncio
    async def test_file_upload_validation(self):
        """Test file upload validation"""
        # Test invalid file type
        files = {"file": ("malware.exe", b"fake content", "application/octet-stream")}
        response = self.client.post("/files", files=files)
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
    
    def test_list_all_jobs_empty(self):
        """Test listing jobs when none exist"""
        # Clear existing jobs
        self.client.delete("/chat/clear")
        
        response = self.client.get("/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_message_jobs"] == 0
        assert data["total_file_jobs"] == 0
        assert data["jobs"] == []


class TestAIFallbackEndpoints:
    """Test AI fallback testing endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @pytest.mark.ai
    def test_fallback_gemini_fail(self):
        """Test Gemini failure fallback endpoint"""
        response = self.client.post("/test/fallback-gemini-fail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["test"] == "gemini_failure_deepai_backup"
        assert "success" in data
        assert "ai_response" in data
    
    @pytest.mark.ai
    def test_fallback_both_fail(self):
        """Test both APIs failure fallback endpoint"""
        response = self.client.post("/test/fallback-both-fail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["test"] == "both_apis_failure_friendly_ux"
        assert "success" in data
        assert "ai_response" in data
    
    @pytest.mark.ai
    def test_fallback_file_analysis(self):
        """Test file analysis fallback endpoint"""
        response = self.client.post("/test/fallback-file-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["test"] == "file_analysis_fallback"
        assert "normal_result" in data
        assert "fallback_result" in data


class TestCORSAndSecurity:
    """Test CORS configuration and basic security"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = self.client.options(
            "/messages",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # Check for CORS headers (FastAPI handles this automatically)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON payloads"""
        response = self.client.post(
            "/messages",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_method_not_allowed(self):
        """Test unsupported HTTP methods"""
        response = self.client.patch("/health")
        
        assert response.status_code == 405  # Method Not Allowed
