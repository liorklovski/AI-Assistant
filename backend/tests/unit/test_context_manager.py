"""
Unit tests for Smart Context Management system
"""

import pytest
from utils.context_manager import ConversationContext, get_optimized_context


class TestConversationContext:
    """Test the ConversationContext class"""
    
    def setup_method(self):
        """Setup test context manager"""
        self.context_manager = ConversationContext(
            max_context_length=1000,
            max_messages=10
        )
    
    def test_empty_conversation(self):
        """Test handling of empty conversation"""
        result = self.context_manager.optimize_context([], "Test message")
        
        assert result["optimized_context"] == []
        assert result["user_info"] == {}
        assert result["context_summary"] == "Starting new conversation"
        assert result["total_length"] == 0
        assert result["optimization_applied"] is False
    
    def test_user_info_extraction(self):
        """Test extraction of user information from messages"""
        messages = [
            {
                "type": "message",
                "user_message": "Hi, my name is Alice and I love programming",
                "ai_response": "Nice to meet you Alice!",
                "status": "done",
                "created_at": "2024-01-01T10:00:00"
            },
            {
                "type": "message", 
                "user_message": "I hate debugging complex algorithms",
                "ai_response": "I understand debugging can be frustrating",
                "status": "done",
                "created_at": "2024-01-01T10:01:00"
            }
        ]
        
        result = self.context_manager.optimize_context(messages, "What do you remember about me?")
        
        assert result["user_info"]["name"] == "Alice"
        assert "programming" in result["user_info"]["preferences"]
        assert "debugging complex algorithms" in result["user_info"]["dislikes"]
        assert "Alice" in result["context_summary"]
    
    def test_message_scoring(self):
        """Test message importance scoring"""
        # Create a message with important keywords
        important_message = {
            "type": "message",
            "user_message": "Remember that my name is important and I need help urgently",
            "ai_response": "I'll remember that",
            "status": "done",
            "created_at": "2024-01-01T10:00:00"
        }
        
        # Create a regular message
        regular_message = {
            "type": "message",
            "user_message": "Just chatting about random stuff",
            "ai_response": "Sure thing",
            "status": "done", 
            "created_at": "2024-01-01T09:00:00"
        }
        
        important_score = self.context_manager._calculate_message_score(important_message, 1, 2)
        regular_score = self.context_manager._calculate_message_score(regular_message, 0, 2)
        
        # Important message should score higher due to keywords and recency
        assert important_score > regular_score
    
    def test_context_length_optimization(self):
        """Test context length optimization when messages are too long"""
        # Create many long messages
        long_messages = []
        for i in range(20):
            long_messages.append({
                "type": "message",
                "user_message": "This is a very long message " * 20,  # Long message
                "ai_response": "I understand " * 10,
                "status": "done",
                "created_at": f"2024-01-01T{10+i:02d}:00:00"
            })
        
        # Set a small context limit to force optimization
        small_context_manager = ConversationContext(max_context_length=500, max_messages=5)
        result = small_context_manager.optimize_context(long_messages, "Test")
        
        assert len(result["optimized_context"]) <= 5  # Respects max_messages
        assert result["total_length"] <= 500  # Respects max_context_length
        assert result["optimization_applied"] is True  # Optimization was needed
    
    def test_context_summary_generation(self):
        """Test automatic context summary generation"""
        messages = [
            {
                "type": "message",
                "user_message": "My name is Bob and this is important to remember",
                "ai_response": "Got it Bob",
                "status": "done",
                "created_at": "2024-01-01T10:00:00"
            }
        ]
        
        result = self.context_manager.optimize_context(messages, "Test")
        summary = result["context_summary"]
        
        assert "Bob" in summary
        assert "Messages: 1" in summary
        assert "important" in summary
    
    def test_file_context_handling(self):
        """Test handling of file uploads in context"""
        messages = [
            {
                "type": "file",
                "original_filename": "data.csv",
                "file_type": ".csv",
                "file_size": 1024,
                "analysis_result": "CSV file with data analysis",
                "status": "done",
                "created_at": "2024-01-01T10:00:00"
            },
            {
                "type": "message",
                "user_message": "What did that file contain?",
                "ai_response": "The CSV file contained data analysis results",
                "status": "done",
                "created_at": "2024-01-01T10:01:00"
            }
        ]
        
        result = self.context_manager.optimize_context(messages, "Tell me more")
        
        assert len(result["optimized_context"]) == 2
        assert any(msg.get("type") == "file" for msg in result["optimized_context"])
        assert any(msg.get("type") == "message" for msg in result["optimized_context"])
    
    def test_global_get_optimized_context_function(self):
        """Test the global get_optimized_context function"""
        messages = [
            {
                "type": "message",
                "user_message": "I'm testing the global function",
                "ai_response": "Test successful",
                "status": "done",
                "created_at": "2024-01-01T10:00:00"
            }
        ]
        
        result = get_optimized_context(messages, "Test global function")
        
        assert "optimized_context" in result
        assert "user_info" in result  
        assert "context_summary" in result
        assert "total_length" in result
        assert "optimization_applied" in result
        assert len(result["optimized_context"]) <= len(messages)
