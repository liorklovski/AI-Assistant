"""
Integration tests for Smart Context Management flow
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import time

from main import app


class TestSmartContextFlow:
    """Test the complete Smart Context Management flow"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        # Clear any existing chat history
        self.client.delete("/chat/clear")
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.client.delete("/chat/clear")
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self):
        """Test complete conversation with context building and optimization"""
        
        with patch('services.AIProcessor.get_ai_response', new_callable=AsyncMock) as mock_ai:
            # Mock AI responses that demonstrate context awareness
            mock_responses = [
                "Hi Alice! Nice to meet you!",
                "That's great that you love machine learning, Alice!",
                "Sure Alice, I remember you mentioned you love machine learning!"
            ]
            mock_ai.side_effect = mock_responses
            
            # Step 1: User introduces themselves
            response1 = self.client.post("/messages", json={
                "message": "Hi, my name is Alice and I love machine learning"
            })
            assert response1.status_code == 200
            job1_id = response1.json()["job_id"]
            
            # Wait for processing
            self._wait_for_job_completion(job1_id)
            
            # Step 2: User asks about preferences
            response2 = self.client.post("/messages", json={
                "message": "What do you know about my interests?"
            })
            assert response2.status_code == 200
            job2_id = response2.json()["job_id"]
            
            # Wait for processing
            self._wait_for_job_completion(job2_id)
            
            # Step 3: Test memory
            response3 = self.client.post("/messages", json={
                "message": "Do you remember what I love?"
            })
            assert response3.status_code == 200
            job3_id = response3.json()["job_id"]
            
            # Wait for processing
            self._wait_for_job_completion(job3_id)
            
            # Verify context analytics
            analytics_response = self.client.get("/context/analytics")
            assert analytics_response.status_code == 200
            
            analytics = analytics_response.json()
            assert analytics["conversation_stats"]["total_messages"] == 3
            assert analytics["user_profile"]["name"] == "Alice"
            assert "machine learning" in analytics["user_profile"]["preferences"][0]
            assert "Alice" in analytics["context_optimization"]["context_summary"]
    
    def test_context_optimization_endpoint(self):
        """Test context optimization endpoint with sample data"""
        # First create some conversation history
        with patch('services.AIProcessor.get_ai_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "Test response"
            
            # Create several messages
            for i in range(5):
                response = self.client.post("/messages", json={
                    "message": f"Message {i}: Testing context optimization"
                })
                job_id = response.json()["job_id"]
                self._wait_for_job_completion(job_id)
        
        # Test optimization
        response = self.client.post("/context/optimize", params={
            "test_message": "What have we discussed?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "test_message" in data
        assert "original_context" in data
        assert "optimized_context" in data
        assert "compression_ratio" in data
        assert data["original_context"]["message_count"] >= 5
    
    @pytest.mark.ai
    def test_ai_fallback_chain_integration(self):
        """Test the complete AI fallback chain"""
        # Test Gemini failure → DeepAI backup
        response = self.client.post("/test/fallback-gemini-fail")
        assert response.status_code == 200
        
        data = response.json()
        assert data["test"] == "gemini_failure_deepai_backup"
        assert "ai_response" in data
        
        # Test both APIs failure → Friendly message
        response = self.client.post("/test/fallback-both-fail")
        assert response.status_code == 200
        
        data = response.json()
        assert data["test"] == "both_apis_failure_friendly_ux"
        assert "technical difficulties" in data["ai_response"].lower()
    
    def test_file_upload_and_context_integration(self):
        """Test file upload integration with context system"""
        # Create a test file
        files = {"file": ("test.txt", b"This is test content", "text/plain")}
        
        with patch('services.AIProcessor.get_file_analysis', new_callable=AsyncMock) as mock_analysis:
            mock_analysis.return_value = "📁 Test file analysis result"
            
            response = self.client.post("/files", files=files)
            assert response.status_code == 200
            
            file_job_id = response.json()["job_id"]
            self._wait_for_job_completion(file_job_id)
            
            # Check if file appears in context analytics
            analytics_response = self.client.get("/context/analytics")
            analytics = analytics_response.json()
            
            assert analytics["conversation_stats"]["file_uploads"] == 1
            assert analytics["conversation_insights"]["file_interaction_rate"] > 0
    
    def test_chat_persistence_across_requests(self):
        """Test that chat history persists across different API calls"""
        with patch('services.AIProcessor.get_ai_response', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "Test response"
            
            # Send first message
            response1 = self.client.post("/messages", json={"message": "First message"})
            job1_id = response1.json()["job_id"]
            self._wait_for_job_completion(job1_id)
            
            # Send second message
            response2 = self.client.post("/messages", json={"message": "Second message"})
            job2_id = response2.json()["job_id"]
            self._wait_for_job_completion(job2_id)
            
            # Check chat history contains both messages
            history_response = self.client.get("/chat/history")
            history = history_response.json()
            
            assert len(history["messages"]) == 2
            messages = history["messages"]
            assert messages[0]["user_message"] == "First message"
            assert messages[1]["user_message"] == "Second message"
    
    def _wait_for_job_completion(self, job_id: str, max_attempts: int = 10):
        """Helper method to wait for job completion"""
        for _ in range(max_attempts):
            response = self.client.get(f"/messages/{job_id}")
            if response.status_code == 200:
                job_data = response.json()
                if job_data["status"] in ["done", "error"]:
                    return job_data
            time.sleep(0.5)
        
        raise TimeoutError(f"Job {job_id} did not complete within timeout")


class TestErrorHandling:
    """Test error handling across the application"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_malformed_requests(self):
        """Test handling of malformed requests"""
        # Missing required fields
        response = self.client.post("/messages", json={})
        assert response.status_code == 422
        
        # Wrong data types
        response = self.client.post("/messages", json={"message": 123})
        assert response.status_code == 422
    
    def test_large_file_upload(self):
        """Test handling of oversized file uploads"""
        # Create large fake file content
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB (over limit)
        files = {"file": ("large.txt", large_content, "text/plain")}
        
        response = self.client.post("/files", files=files)
        assert response.status_code in [400, 413]  # Bad Request or Payload Too Large
    
    def test_nonexistent_endpoints(self):
        """Test requests to non-existent endpoints"""
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
        
        response = self.client.post("/invalid/endpoint")
        assert response.status_code == 404
