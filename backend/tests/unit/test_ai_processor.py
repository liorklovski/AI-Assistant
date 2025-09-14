"""
Unit tests for AI Processor and fallback logic
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import asyncio

from services.ai_processor import AIProcessor
from config import Config


class TestAIProcessor:
    """Test AI processor fallback logic and dummy responses"""
    
    @pytest.mark.asyncio
    async def test_dummy_ai_responses(self):
        """Test dummy AI response generation"""
        # Test greeting
        response = await AIProcessor._get_dummy_response("hello there")
        assert "hello" in response.lower() or "hi" in response.lower()
        
        # Test help request
        response = await AIProcessor._get_dummy_response("help me please")
        assert "help" in response.lower()
        
        # Test question
        response = await AIProcessor._get_dummy_response("What is AI?")
        assert "question" in response.lower()
        
        # Test general message
        response = await AIProcessor._get_dummy_response("just chatting")
        assert len(response) > 0
        assert "chatting" in response or "mentioned" in response
    
    @pytest.mark.asyncio
    async def test_dummy_file_analysis(self):
        """Test dummy file analysis responses"""
        # Test document file
        response = await AIProcessor._get_dummy_file_analysis("document.pdf", ".pdf", 2048)
        assert "📄" in response or "Document" in response
        assert "document.pdf" in response
        assert "2048" in response
        
        # Test image file
        response = await AIProcessor._get_dummy_file_analysis("photo.jpg", ".jpg", 1024)
        assert "🖼️" in response or "Image" in response
        assert "photo.jpg" in response
        
        # Test data file
        response = await AIProcessor._get_dummy_file_analysis("data.csv", ".csv", 512)
        assert "📊" in response or "Data" in response
        assert "data.csv" in response
    
    @pytest.mark.asyncio
    async def test_friendly_fallback_responses(self):
        """Test user-friendly fallback messages"""
        # Test message fallback
        response = await AIProcessor._get_friendly_fallback_response("What is the weather?")
        assert "technical difficulties" in response.lower()
        assert "patience" in response.lower()
        assert "🤖" in response
        
        # Test file fallback
        response = await AIProcessor._get_friendly_file_fallback("report.pdf", ".pdf", 1024)
        assert "technical difficulties" in response.lower()
        assert "report.pdf" in response
        assert "1024" in response
        assert "📁" in response
    
    @pytest.mark.asyncio
    async def test_get_ai_response_dummy_mode(self):
        """Test AI response when in dummy mode"""
        with patch.object(Config, 'USE_DUMMY_AI', True):
            response = await AIProcessor.get_ai_response("Hello AI")
            
            assert isinstance(response, str)
            assert len(response) > 0
            # Should be a dummy response
            assert any(keyword in response.lower() for keyword in ["hello", "hi", "assist", "help"])
    
    @pytest.mark.asyncio
    async def test_get_ai_response_with_context(self):
        """Test AI response with conversation context"""
        chat_history = [
            {
                "type": "message",
                "user_message": "My name is Bob",
                "ai_response": "Nice to meet you Bob",
                "status": "done",
                "created_at": "2024-01-01T10:00:00"
            }
        ]
        
        with patch.object(Config, 'USE_DUMMY_AI', True):
            response = await AIProcessor.get_ai_response("What's my name?", chat_history)
            
            assert isinstance(response, str)
            assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_get_file_analysis_dummy_mode(self):
        """Test file analysis when in dummy mode"""
        with patch.object(Config, 'USE_DUMMY_AI', True):
            response = await AIProcessor.get_file_analysis("test.txt", ".txt", 100)
            
            assert isinstance(response, str)
            assert "test.txt" in response
            assert "100" in response
    
    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_ai_service_fallback_chain(self):
        """Test the complete fallback chain without real API calls"""
        # Mock all AI services to fail
        with patch('services.AIService.get_gemini_response_with_retry', side_effect=Exception("Gemini failed")), \
             patch('services.AIService.get_deepai_response', side_effect=Exception("DeepAI failed")), \
             patch.object(Config, 'GEMINI_API_KEY', 'fake-key'), \
             patch.object(Config, 'DEEPAI_API_KEY', 'fake-key'), \
             patch.object(Config, 'USE_DUMMY_AI', False):
            
            response = await AIProcessor.get_ai_response("Test message")
            
            # Should get friendly fallback message
            assert "technical difficulties" in response.lower()
            assert "patience" in response.lower()
    
    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_file_analysis_fallback_chain(self):
        """Test file analysis fallback chain"""
        # Mock all AI services to fail
        with patch('services.AIService.get_gemini_file_analysis_with_retry', side_effect=Exception("Gemini failed")), \
             patch('services.AIService.get_deepai_file_analysis', side_effect=Exception("DeepAI failed")), \
             patch.object(Config, 'GEMINI_API_KEY', 'fake-key'), \
             patch.object(Config, 'DEEPAI_API_KEY', 'fake-key'), \
             patch.object(Config, 'USE_DUMMY_AI', False):
            
            response = await AIProcessor.get_file_analysis("test.txt", ".txt", 100)
            
            # Should get friendly fallback message
            assert "technical difficulties" in response.lower()
            assert "test.txt" in response
            assert "📁" in response
