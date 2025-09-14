"""
Test endpoints for verifying AI fallback system
"""

from fastapi import APIRouter

from config import Config
from services import AIProcessor

router = APIRouter(prefix="/test", tags=["test"])


@router.post("/fallback-gemini-fail")
async def test_gemini_failure():
    """Test endpoint: Force Gemini to fail, should use DeepAI backup"""
    original_key = None
    try:
        # Temporarily disable Gemini by setting invalid API key
        original_key = Config.GEMINI_API_KEY
        Config.GEMINI_API_KEY = "invalid_key_to_force_failure"
        
        # Test message processing
        test_message = "This is a test to verify DeepAI backup works"
        result = await AIProcessor.get_ai_response(test_message)
        
        # Restore original key
        Config.GEMINI_API_KEY = original_key
        
        return {
            "test": "gemini_failure_deepai_backup",
            "success": True,
            "message": test_message,
            "ai_response": result,
            "expected_behavior": "Should use DeepAI when Gemini fails"
        }
    except Exception as e:
        if original_key:
            Config.GEMINI_API_KEY = original_key  # Restore key on error
        return {
            "test": "gemini_failure_deepai_backup", 
            "success": False,
            "error": str(e)
        }


@router.post("/fallback-both-fail")
async def test_both_apis_failure():
    """Test endpoint: Force both APIs to fail, should show friendly UX message"""
    original_gemini = None
    original_deepai = None
    try:
        # Temporarily disable both APIs
        original_gemini = Config.GEMINI_API_KEY
        original_deepai = Config.DEEPAI_API_KEY
        
        Config.GEMINI_API_KEY = "invalid_gemini_key"
        Config.DEEPAI_API_KEY = "invalid_deepai_key"
        
        # Test message processing
        test_message = "This should trigger friendly UX fallback message"
        result = await AIProcessor.get_ai_response(test_message)
        
        # Restore original keys
        Config.GEMINI_API_KEY = original_gemini
        Config.DEEPAI_API_KEY = original_deepai
        
        return {
            "test": "both_apis_failure_friendly_ux",
            "success": True,
            "message": test_message,
            "ai_response": result,
            "expected_behavior": "Should show friendly UX message when both APIs fail"
        }
    except Exception as e:
        # Restore keys on error
        if original_gemini:
            Config.GEMINI_API_KEY = original_gemini
        if original_deepai:
            Config.DEEPAI_API_KEY = original_deepai
        return {
            "test": "both_apis_failure_friendly_ux",
            "success": False, 
            "error": str(e)
        }


@router.post("/fallback-file-analysis")
async def test_file_fallback():
    """Test endpoint: Test file analysis fallback chain"""
    original_gemini = None
    original_deepai = None
    try:
        # Test with normal APIs first
        result_normal = await AIProcessor.get_file_analysis("test.txt", ".txt", 100)
        
        # Test with forced failure
        original_gemini = Config.GEMINI_API_KEY
        original_deepai = Config.DEEPAI_API_KEY
        
        Config.GEMINI_API_KEY = "invalid_key"
        Config.DEEPAI_API_KEY = "invalid_key"
        
        result_fallback = await AIProcessor.get_file_analysis("test.txt", ".txt", 100)
        
        # Restore keys
        Config.GEMINI_API_KEY = original_gemini
        Config.DEEPAI_API_KEY = original_deepai
        
        return {
            "test": "file_analysis_fallback",
            "success": True,
            "normal_result": result_normal[:100] + "..." if len(result_normal) > 100 else result_normal,
            "fallback_result": result_fallback[:100] + "..." if len(result_fallback) > 100 else result_fallback,
            "comparison": "Normal uses AI, fallback shows friendly message"
        }
    except Exception as e:
        # Restore keys on error
        if original_gemini:
            Config.GEMINI_API_KEY = original_gemini
        if original_deepai:
            Config.DEEPAI_API_KEY = original_deepai
        return {
            "test": "file_analysis_fallback",
            "success": False,
            "error": str(e)
        }
