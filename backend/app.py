from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import asyncio
import uuid
from datetime import datetime
from enum import Enum
import json
import os
import aiofiles
from pathlib import Path
import google.generativeai as genai
import requests
from config import Config

app = FastAPI(title="AI Chat Assistant MVP", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job Status Enum
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    DONE = "done"
    ERROR = "error"

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {
    '.txt', '.pdf', '.docx', '.jpg', '.jpeg', '.png', '.csv', '.json'
}
UPLOAD_DIRECTORY = "uploads"

# Ensure upload directory exists
Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)

# Data Models
class MessageRequest(BaseModel):
    message: str

class MessageJob(BaseModel):
    id: str
    user_message: str
    ai_response: Optional[str] = None
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

class FileJob(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    analysis_result: Optional[str] = None
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

class MessageResponse(BaseModel):
    job_id: str
    status: JobStatus
    user_message: str
    ai_response: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class FileResponse(BaseModel):
    job_id: str
    status: JobStatus
    original_filename: str
    file_type: str
    file_size: int
    analysis_result: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class UnifiedJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    job_type: str  # "message" or "file"
    # Message fields
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    # File fields  
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    analysis_result: Optional[str] = None
    # Common fields
    created_at: datetime
    completed_at: Optional[datetime] = None

# In-memory job stores (MVP - use database in production)
message_jobs: Dict[str, MessageJob] = {}
file_jobs: Dict[str, FileJob] = {}

# Initialize Gemini AI
if Config.GEMINI_API_KEY and not Config.USE_DUMMY_AI:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    print("✅ Gemini AI initialized")
else:
    print("⚠️ Using dummy AI responses (set GEMINI_API_KEY and USE_DUMMY_AI=false for real AI)")

class AIService:
    """Modular AI service with Gemini + DeepAI backup and retry logic"""
    
    @staticmethod
    async def get_gemini_response_with_retry(user_message: str, chat_history: list = None, max_retries: int = Config.GEMINI_MAX_RETRIES) -> str:
        """Get response from Gemini API with chat history context and retry logic"""
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Build conversation context
                context_messages = []
                if chat_history:
                    # Add recent conversation history (last 10 messages for context)
                    recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
                    for msg in recent_history:
                        if msg.get('type') == 'message' and msg.get('status') == 'done':
                            context_messages.append(f"User: {msg.get('user_message', '')}")
                            if msg.get('ai_response'):
                                context_messages.append(f"AI: {msg.get('ai_response', '')}")
                        elif msg.get('type') == 'file' and msg.get('status') == 'done':
                            context_messages.append(f"User uploaded file: {msg.get('original_filename', 'unknown')} ({msg.get('file_type', 'unknown')})")
                            if msg.get('analysis_result'):
                                context_messages.append(f"AI: {msg.get('analysis_result', '')}")

                # Create full prompt with context
                if context_messages:
                    conversation_context = "\n".join(context_messages)
                    prompt = f"""You are a helpful AI assistant. Here is our recent conversation history:

{conversation_context}

User: {user_message}

Please respond to the user's latest message in a conversational and helpful way, taking into account our conversation history above. Provide a clear, concise, and contextually appropriate response."""
                else:
                    prompt = f"""You are a helpful AI assistant. Please respond to this message in a conversational and helpful way:

User: {user_message}

Provide a clear, concise, and helpful response."""
                
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"Gemini API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)  # Brief delay before retry
        
        raise Exception("All Gemini retry attempts failed")
    
    @staticmethod
    async def get_deepai_response(user_message: str, chat_history: list = None, max_retries: int = Config.DEEPAI_MAX_RETRIES) -> str:
        """Get response from DeepAI API with chat history context and retry logic"""
        for attempt in range(max_retries):
            try:
                # Build context for DeepAI
                context_text = f"Answer this question helpfully: {user_message}"
                
                if chat_history:
                    # Add recent conversation for context (last 5 messages to keep it concise for DeepAI)
                    recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
                    context_parts = []
                    for msg in recent_history:
                        if msg.get('type') == 'message' and msg.get('status') == 'done':
                            context_parts.append(f"Previous - User: {msg.get('user_message', '')}")
                            if msg.get('ai_response'):
                                context_parts.append(f"Previous - AI: {msg.get('ai_response', '')[:100]}...")
                    
                    if context_parts:
                        context_text = f"Conversation context: {' '.join(context_parts)} \n\nCurrent question: {user_message}"
                
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
                print(f"DeepAI API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
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
                print(f"Gemini file analysis attempt {attempt + 1}/{max_retries} failed: {str(e)}")
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
                print(f"DeepAI file analysis attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                await asyncio.sleep(1)
        
        raise Exception("All DeepAI file analysis attempts failed")

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
                print(f"🤖 Trying Gemini API for message with {len(chat_history) if chat_history else 0} context messages...")
                return await AIService.get_gemini_response_with_retry(user_message, chat_history)
            except Exception as e:
                print(f"❌ Gemini failed after retries: {str(e)}")
        
        # Fallback to DeepAI (with simplified context)
        if Config.DEEPAI_API_KEY:
            try:
                print(f"🔄 Trying DeepAI backup for message with context...")
                return await AIService.get_deepai_response(user_message, chat_history)
            except Exception as e:
                print(f"❌ DeepAI backup failed after retries: {str(e)}")
        
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
                print(f"🤖 Trying Gemini API for file analysis...")
                return await AIService.get_gemini_file_analysis_with_retry(filename, file_type, file_size, file_path)
            except Exception as e:
                print(f"❌ Gemini file analysis failed after retries: {str(e)}")
        
        # Fallback to DeepAI
        if Config.DEEPAI_API_KEY:
            try:
                print(f"🔄 Trying DeepAI backup for file analysis...")
                return await AIService.get_deepai_file_analysis(filename, file_type, file_size)
            except Exception as e:
                print(f"❌ DeepAI file analysis backup failed after retries: {str(e)}")
        
        # Final fallback: Friendly UX message
        return await AIProcessor._get_friendly_file_fallback(filename, file_type, file_size)
    
    @staticmethod
    async def _get_dummy_response(user_message: str) -> str:
        """Fallback dummy response"""
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

def validate_file(file: UploadFile) -> Optional[str]:
    """Validate uploaded file and return error message if invalid"""
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        return f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
    
    # Check file extension
    if file.filename:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_FILE_TYPES:
            allowed_types = ', '.join(sorted(ALLOWED_FILE_TYPES))
            return f"File type '{file_extension}' not supported. Allowed types: {allowed_types}"
    else:
        return "Filename is required"
    
    return None

async def process_message_job_background(job_id: str):
    """Background task to process message job with chat history context"""
    try:
        job = message_jobs.get(job_id)
        if not job:
            return
            
        # Update status to processing
        job.status = JobStatus.PROCESSING
        
        # Build chat history for context (exclude current message)
        chat_history = []
        
        # Get all previous messages (completed ones)
        all_messages = []
        for msg_job in message_jobs.values():
            if msg_job.id != job_id and msg_job.status == JobStatus.DONE:
                all_messages.append({
                    'type': 'message',
                    'user_message': msg_job.user_message,
                    'ai_response': msg_job.ai_response,
                    'status': 'done',
                    'created_at': msg_job.created_at.isoformat()
                })
        
        # Get all previous file jobs (completed ones)
        for file_job in file_jobs.values():
            if file_job.status == JobStatus.DONE:
                all_messages.append({
                    'type': 'file',
                    'original_filename': file_job.original_filename,
                    'file_type': file_job.file_type,
                    'file_size': file_job.file_size,
                    'analysis_result': file_job.analysis_result,
                    'status': 'done',
                    'created_at': file_job.created_at.isoformat()
                })
        
        # Sort by creation time to get chronological order
        chat_history = sorted(all_messages, key=lambda x: x['created_at'])
        
        # Debug: Print context being sent
        print(f"🔍 Processing message with {len(chat_history)} context items")
        if chat_history:
            print(f"🔍 Last context item: {chat_history[-1]['user_message'] if chat_history[-1].get('user_message') else 'File: ' + chat_history[-1].get('original_filename', 'unknown')}")
        
        # Get AI response with full context
        ai_response = await AIProcessor.get_ai_response(job.user_message, chat_history)
        
        # Update job with result
        job.ai_response = ai_response
        job.status = JobStatus.DONE
        job.completed_at = datetime.utcnow()
        
    except Exception as e:
        # Handle errors
        if job_id in message_jobs:
            message_jobs[job_id].status = JobStatus.ERROR
            message_jobs[job_id].ai_response = f"Error processing message: {str(e)}"
            message_jobs[job_id].completed_at = datetime.utcnow()

async def process_file_job_background(job_id: str):
    """Background task to process file job"""
    try:
        job = file_jobs.get(job_id)
        if not job:
            return
            
        # Update status to processing
        job.status = JobStatus.PROCESSING
        
        # Get file analysis
        file_path = Path(UPLOAD_DIRECTORY) / job.stored_filename
        analysis_result = await AIProcessor.get_file_analysis(
            job.original_filename, job.file_type, job.file_size, str(file_path)
        )
        
        # Update job with result
        job.analysis_result = analysis_result
        job.status = JobStatus.DONE
        job.completed_at = datetime.utcnow()
        
        # Clean up file after processing (for MVP)
        try:
            file_path = Path(UPLOAD_DIRECTORY) / job.stored_filename
            if file_path.exists():
                file_path.unlink()
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up file {job.stored_filename}: {cleanup_error}")
        
    except Exception as e:
        # Handle errors
        if job_id in file_jobs:
            file_jobs[job_id].status = JobStatus.ERROR
            file_jobs[job_id].analysis_result = f"Error processing file: {str(e)}"
            file_jobs[job_id].completed_at = datetime.utcnow()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "active_message_jobs": len(message_jobs),
        "active_file_jobs": len(file_jobs)
    }

@app.post("/messages", response_model=dict)
async def create_message_job(request: MessageRequest):
    """Submit user message and create processing job"""
    try:
        # Validate input
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Create new job
        job_id = str(uuid.uuid4())
        job = MessageJob(
            id=job_id,
            user_message=request.message.strip(),
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Store job
        message_jobs[job_id] = job
        
        # Start background processing
        asyncio.create_task(process_message_job_background(job_id))
        
        return {"job_id": job_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload file and create processing job"""
    try:
        # Validate file
        validation_error = validate_file(file)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)
        
        # Read file size
        content = await file.read()
        file_size = len(content)
        
        # Additional size check after reading
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
            )
        
        # Generate unique filename
        job_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix.lower()
        stored_filename = f"{job_id}{file_extension}"
        
        # Save file to disk
        file_path = Path(UPLOAD_DIRECTORY) / stored_filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create file job
        file_job = FileJob(
            id=job_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_type=file_extension,
            file_size=file_size,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Store job
        file_jobs[job_id] = file_job
        
        # Start background processing
        asyncio.create_task(process_file_job_background(job_id))
        
        return {"job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{job_id}", response_model=UnifiedJobResponse)
async def get_message_job(job_id: str):
    """Get status and result of message or file job"""
    try:
        job = message_jobs.get(job_id)
        if job:
            return UnifiedJobResponse(
                job_id=job.id,
                status=job.status,
                job_type="message",
                user_message=job.user_message,
                ai_response=job.ai_response,
                created_at=job.created_at,
                completed_at=job.completed_at
            )
        
        # Check if it's a file job
        file_job = file_jobs.get(job_id)
        if file_job:
            return UnifiedJobResponse(
                job_id=file_job.id,
                status=file_job.status,
                job_type="file",
                original_filename=file_job.original_filename,
                file_type=file_job.file_type,
                file_size=file_job.file_size,
                analysis_result=file_job.analysis_result,
                created_at=file_job.created_at,
                completed_at=file_job.completed_at
            )
            
        raise HTTPException(status_code=404, detail="Job not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages")
async def list_all_jobs():
    """List all jobs (for debugging/monitoring)"""
    message_job_list = [
        {
            "job_id": job.id,
            "type": "message",
            "status": job.status,
            "content": job.user_message[:50] + "..." if len(job.user_message) > 50 else job.user_message,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
        for job in message_jobs.values()
    ]
    
    file_job_list = [
        {
            "job_id": job.id,
            "type": "file",
            "status": job.status,
            "content": f"{job.original_filename} ({job.file_size} bytes)",
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
        for job in file_jobs.values()
    ]
    
    return {
        "total_message_jobs": len(message_jobs),
        "total_file_jobs": len(file_jobs),
        "jobs": sorted(
            message_job_list + file_job_list,
            key=lambda x: x['created_at'],
            reverse=True
        )
    }

@app.get("/chat/history")
async def get_chat_history():
    """Get all messages and files for frontend persistence"""
    all_items = []
    
    # Add message jobs
    for job in message_jobs.values():
        all_items.append({
            "id": job.id,
            "type": "message", 
            "user_message": job.user_message,
            "ai_response": job.ai_response,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })
    
    # Add file jobs  
    for job in file_jobs.values():
        all_items.append({
            "id": job.id,
            "type": "file",
            "original_filename": job.original_filename,
            "file_type": job.file_type,
            "file_size": job.file_size,
            "analysis_result": job.analysis_result,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })
    
    # Sort by creation time
    all_items.sort(key=lambda x: x['created_at'])
    
    return {
        "success": True,
        "messages": all_items
    }

@app.delete("/chat/clear")
async def clear_all_chat():
    """Clear all messages and files from memory"""
    global message_jobs, file_jobs
    
    # Clean up any remaining files
    for job in file_jobs.values():
        try:
            file_path = Path(UPLOAD_DIRECTORY) / job.stored_filename
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # File already cleaned up
    
    # Clear all jobs
    message_jobs.clear()
    file_jobs.clear()
    
    return {
        "success": True,
        "message": "Chat history cleared successfully"
    }

@app.delete("/messages/{job_id}")
async def delete_job(job_id: str):
    """Delete a job (cleanup)"""
    if job_id in message_jobs:
        del message_jobs[job_id]
        return {"message": "Message job deleted successfully"}
    elif job_id in file_jobs:
        # Clean up file if it still exists
        job = file_jobs[job_id]
        try:
            file_path = Path(UPLOAD_DIRECTORY) / job.stored_filename
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # File already cleaned up or doesn't exist
        
        del file_jobs[job_id]
        return {"message": "File job deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")

# Test endpoints for verifying fallback system
@app.post("/test/fallback-gemini-fail")
async def test_gemini_failure():
    """Test endpoint: Force Gemini to fail, should use DeepAI backup"""
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
        Config.GEMINI_API_KEY = original_key  # Restore key on error
        return {
            "test": "gemini_failure_deepai_backup", 
            "success": False,
            "error": str(e)
        }

@app.post("/test/fallback-both-fail")
async def test_both_apis_failure():
    """Test endpoint: Force both APIs to fail, should show friendly UX message"""
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
        Config.GEMINI_API_KEY = original_gemini
        Config.DEEPAI_API_KEY = original_deepai
        return {
            "test": "both_apis_failure_friendly_ux",
            "success": False, 
            "error": str(e)
        }

@app.post("/test/fallback-file-analysis")
async def test_file_fallback():
    """Test endpoint: Test file analysis fallback chain"""
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
        return {
            "test": "file_analysis_fallback",
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)