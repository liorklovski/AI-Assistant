"""
AI Service for handling external AI API calls (Gemini and DeepAI)
"""

import asyncio
import requests
import google.generativeai as genai
from config import Config
from utils.context_manager import get_optimized_context
from utils.logger import ai_logger


class AIService:
    """Modular AI service with Gemini + DeepAI backup and retry logic"""
    
    @staticmethod
    async def get_gemini_response_with_retry(user_message: str, chat_history: list = None, max_retries: int = Config.GEMINI_MAX_RETRIES) -> str:
        """Get response from Gemini API with optimized context and retry logic"""
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Use smart context optimization
                context_data = get_optimized_context(chat_history or [], user_message)
                optimized_messages = context_data["optimized_context"]
                user_info = context_data["user_info"]
                context_summary = context_data["context_summary"]
                
                ai_logger.info(f"Smart Context optimized: {context_summary} | Length: {context_data['total_length']} chars | Optimized: {context_data['optimization_applied']}")
                
                # Build conversation context with optimized messages
                context_messages = []
                if optimized_messages:
                    for msg in optimized_messages:
                        if msg.get('type') == 'message' and msg.get('status') == 'done':
                            context_messages.append(f"User: {msg.get('user_message', '')}")
                            if msg.get('ai_response'):
                                context_messages.append(f"AI: {msg.get('ai_response', '')}")
                        elif msg.get('type') == 'file' and msg.get('status') == 'done':
                            context_messages.append(f"User uploaded file: {msg.get('original_filename', 'unknown')} ({msg.get('file_type', 'unknown')})")
                            if msg.get('analysis_result'):
                                context_messages.append(f"AI: {msg.get('analysis_result', '')}")

                # Create enhanced prompt with user info and optimized context
                if context_messages or user_info:
                    conversation_context = "\n".join(context_messages) if context_messages else "This is the start of our conversation."
                    
                    # Add user info if available
                    user_context = ""
                    if user_info:
                        info_parts = []
                        if user_info.get("name"):
                            info_parts.append(f"The user's name is {user_info['name']}")
                        if user_info.get("preferences"):
                            info_parts.append(f"They like: {', '.join(user_info['preferences'][:3])}")
                        if user_info.get("dislikes"):
                            info_parts.append(f"They dislike: {', '.join(user_info['dislikes'][:3])}")
                        
                        if info_parts:
                            user_context = f"\n\nImportant user information: {'. '.join(info_parts)}."
                    
                    prompt = f"""You are a helpful AI assistant. Here is our conversation context (intelligently optimized):

{conversation_context}{user_context}

User: {user_message}

Please respond to the user's latest message in a conversational and helpful way, taking into account our conversation history and any user information above. Be personal and contextual in your response."""
                else:
                    prompt = f"""You are a helpful AI assistant. Please respond to this message in a conversational and helpful way:

User: {user_message}

Provide a clear, concise, and helpful response."""
                
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                ai_logger.warning(f"Gemini API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)  # Brief delay before retry
        
        raise Exception("All Gemini retry attempts failed")
    
    @staticmethod
    async def get_deepai_response(user_message: str, chat_history: list = None, max_retries: int = Config.DEEPAI_MAX_RETRIES) -> str:
        """Get response from DeepAI API with optimized context and retry logic"""
        for attempt in range(max_retries):
            try:
                # Use smart context optimization (simplified for DeepAI)
                context_data = get_optimized_context(chat_history or [], user_message)
                optimized_messages = context_data["optimized_context"][-3:]  # Last 3 for DeepAI
                user_info = context_data["user_info"]
                
                ai_logger.info(f"DeepAI Context prepared: {len(optimized_messages)} optimized messages | User info: {bool(user_info)}")
                
                # Build simplified context for DeepAI
                context_text = f"Answer this question helpfully: {user_message}"
                
                if optimized_messages or user_info:
                    context_parts = []
                    
                    # Add user info first
                    if user_info.get("name"):
                        context_parts.append(f"User name: {user_info['name']}")
                    
                    # Add recent optimized messages
                    for msg in optimized_messages:
                        if msg.get('type') == 'message' and msg.get('status') == 'done':
                            context_parts.append(f"Previous - User: {msg.get('user_message', '')}")
                            if msg.get('ai_response'):
                                context_parts.append(f"Previous - AI: {msg.get('ai_response', '')[:80]}...")
                    
                    if context_parts:
                        context_text = f"Context: {' | '.join(context_parts)} \n\nCurrent question: {user_message}"
                
                response = requests.post(
                    "https://api.deepai.org/api/text-generator",
                    data={'text': context_text},
                    headers={'api-key': Config.DEEPAI_API_KEY},
                    timeout=Config.API_TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('output', '').strip()
                else:
                    raise Exception(f"DeepAI API returned status {response.status_code}")
                    
            except Exception as e:
                ai_logger.warning(f"DeepAI API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)  # Brief delay before retry
        
        raise Exception("All DeepAI retry attempts failed")
    
    @staticmethod  
    async def get_gemini_file_analysis_with_retry(filename: str, file_type: str, file_size: int, file_path: str = None, max_retries: int = Config.GEMINI_MAX_RETRIES) -> str:
        """Get file analysis from Gemini API with retry logic"""
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Create analysis prompt based on file type
                if file_type in ['.txt', '.pdf', '.docx']:
                    prompt = f"""Analyze this document file:
- Filename: {filename}
- Type: {file_type}
- Size: {file_size} bytes

Please provide a brief analysis of what this document likely contains based on its characteristics. Focus on the document type, estimated content, and general insights."""
                elif file_type in ['.jpg', '.jpeg', '.png']:
                    prompt = f"""Analyze this image file:
- Filename: {filename}
- Type: {file_type}  
- Size: {file_size} bytes

Please provide a brief analysis of this image file based on its characteristics."""
                elif file_type in ['.csv', '.json']:
                    prompt = f"""Analyze this data file:
- Filename: {filename}
- Type: {file_type}
- Size: {file_size} bytes

Please provide a brief analysis of this data file and what it likely contains."""
                else:
                    prompt = f"""Analyze this file:
- Filename: {filename}
- Type: {file_type}
- Size: {file_size} bytes

Please provide a brief analysis of this file based on its characteristics."""
                
                response = model.generate_content(prompt)
                return f"📁 {response.text.strip()}"
            except Exception as e:
                ai_logger.warning(f"Gemini file analysis attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)
        
        raise Exception("All Gemini file analysis attempts failed")
    
    @staticmethod
    async def get_deepai_file_analysis(filename: str, file_type: str, file_size: int, max_retries: int = Config.DEEPAI_MAX_RETRIES) -> str:
        """Get file analysis from DeepAI API with retry logic"""
        for attempt in range(max_retries):
            try:
                # Create analysis prompt for DeepAI
                prompt = f"Analyze this {file_type} file named '{filename}' with size {file_size} bytes. Provide insights about its likely content and purpose."
                
                response = requests.post(
                    "https://api.deepai.org/api/text-generator",
                    data={'text': prompt},
                    headers={'api-key': Config.DEEPAI_API_KEY},
                    timeout=Config.API_TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get('output', '').strip()
                    return f"📁 {analysis}"
                else:
                    raise Exception(f"DeepAI API returned status {response.status_code}")
                    
            except Exception as e:
                ai_logger.warning(f"DeepAI file analysis attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)
        
        raise Exception("All DeepAI file analysis attempts failed")
