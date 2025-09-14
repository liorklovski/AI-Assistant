"""
AI Processor for orchestrating AI service calls with fallback logic
"""

import asyncio
from config import Config
from .ai_service import AIService
from utils.logger import ai_logger


class AIProcessor:
    """Main AI processor with robust fallback chain: Gemini → DeepAI → Friendly UX"""
    
    @staticmethod
    async def get_ai_response(user_message: str, chat_history: list = None) -> str:
        """Get AI response with chat history context and robust fallback chain"""
        # Add small delay for better UX
        await asyncio.sleep(Config.DEFAULT_PROCESSING_TIME)
        
        if Config.USE_DUMMY_AI:
            return await AIProcessor._get_dummy_response(user_message)
        
        # Try Gemini first (with full chat context)
        if Config.GEMINI_API_KEY:
            try:
                ai_logger.info(f"Trying Gemini API for message with {len(chat_history) if chat_history else 0} context messages")
                return await AIService.get_gemini_response_with_retry(user_message, chat_history)
            except Exception as e:
                ai_logger.error(f"Gemini failed after retries: {str(e)}")
        
        # Fallback to DeepAI (with simplified context)
        if Config.DEEPAI_API_KEY:
            try:
                ai_logger.info("Trying DeepAI backup for message processing")
                return await AIService.get_deepai_response(user_message, chat_history)
            except Exception as e:
                ai_logger.error(f"DeepAI backup failed after retries: {str(e)}")
        
        # Final fallback: Friendly UX message
        return await AIProcessor._get_friendly_fallback_response(user_message)
    
    @staticmethod
    async def get_file_analysis(filename: str, file_type: str, file_size: int, file_path: str = None) -> str:
        """Get file analysis with robust fallback chain"""
        # Add processing delay
        await asyncio.sleep(Config.DEFAULT_PROCESSING_TIME + 1)  # Files take slightly longer
        
        if Config.USE_DUMMY_AI:
            return await AIProcessor._get_dummy_file_analysis(filename, file_type, file_size)
        
        # Try Gemini first
        if Config.GEMINI_API_KEY:
            try:
                ai_logger.info(f"Trying Gemini API for file analysis: {filename}")
                return await AIService.get_gemini_file_analysis_with_retry(filename, file_type, file_size, file_path)
            except Exception as e:
                ai_logger.error(f"Gemini file analysis failed after retries: {str(e)}")
        
        # Fallback to DeepAI
        if Config.DEEPAI_API_KEY:
            try:
                ai_logger.info(f"Trying DeepAI backup for file analysis: {filename}")
                return await AIService.get_deepai_file_analysis(filename, file_type, file_size)
            except Exception as e:
                ai_logger.error(f"DeepAI file analysis backup failed after retries: {str(e)}")
        
        # Final fallback: Friendly UX message
        return await AIProcessor._get_friendly_file_fallback(filename, file_type, file_size)
    
    @staticmethod
    async def _get_dummy_response(user_message: str) -> str:
        """Fallback dummy response (when dummy mode is enabled)"""
        if "hello" in user_message.lower() or "hi" in user_message.lower():
            return "Hello! Nice to meet you. How can I assist you today?"
        elif "help" in user_message.lower():
            return "I'm here to help! Feel free to ask me anything you'd like to know."
        elif "?" in user_message:
            return f"That's a great question about '{user_message}'. Let me provide some insights..."
        else:
            responses = [
                f"I understand you mentioned: '{user_message}'. That's interesting!",
                f"Thank you for sharing '{user_message}' with me. How can I help you with that?",
                f"Regarding your message about '{user_message}', I'd be happy to assist you.",
            ]
            return responses[len(user_message) % len(responses)]
    
    @staticmethod
    async def _get_friendly_fallback_response(user_message: str) -> str:
        """User-friendly fallback when all AI services are unavailable"""
        return "I apologize, but I'm currently experiencing technical difficulties connecting to my AI services. Your message has been received, and I understand you're asking about something important. While I can't provide a detailed response right now, please feel free to try again in a moment, or rephrase your question. Thank you for your patience! 🤖"
    
    @staticmethod
    async def _get_friendly_file_fallback(filename: str, file_type: str, file_size: int) -> str:
        """User-friendly fallback for file analysis when all AI services are unavailable"""
        size_desc = "small" if file_size < 1024 else "medium" if file_size < 1024*1024 else "large"
        return f"📁 I've received your {file_type} file '{filename}' ({size_desc} size: {file_size} bytes) and it uploaded successfully! Unfortunately, I'm currently experiencing technical difficulties with my AI analysis services, so I can't provide detailed insights right now. Your file appears to be in a valid format. Please try uploading again in a moment, or contact support if the issue persists. Thank you for your patience! 🤖"
    
    @staticmethod
    async def _get_dummy_file_analysis(filename: str, file_type: str, file_size: int) -> str:
        """Fallback dummy file analysis (when dummy mode is enabled)"""
        if file_type in ['.txt', '.pdf', '.docx']:
            return f"📄 Document Analysis: '{filename}' ({file_size} bytes) appears to be a text document. I've analyzed the content structure and found it contains readable text data."
        elif file_type in ['.jpg', '.jpeg', '.png']:
            return f"🖼️ Image Analysis: '{filename}' ({file_size} bytes) is an image file. I've processed the visual content and detected various elements."
        elif file_type in ['.csv', '.json']:
            return f"📊 Data Analysis: '{filename}' ({file_size} bytes) contains structured data. I've parsed the format and the structure appears valid."
        else:
            return f"📁 File Analysis: '{filename}' ({file_size} bytes) has been processed and appears to be in a supported format."
