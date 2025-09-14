"""
Main application entry point for AI Chat Assistant
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

from config import Config
from utils.logger import main_logger
from routes import (
    health_router,
    messages_router,
    files_router,
    chat_router,
    test_router
)
from routes.context import router as context_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Chat Assistant MVP",
    version="1.0.0",
    description="Enterprise-grade AI chat system with file upload and robust fallback mechanisms"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI if configured
if Config.GEMINI_API_KEY and not Config.USE_DUMMY_AI:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    main_logger.info("Gemini AI initialized successfully")
else:
    main_logger.warning("Using dummy AI responses - set GEMINI_API_KEY and USE_DUMMY_AI=false for real AI")

# Include routers
app.include_router(health_router)
app.include_router(messages_router)
app.include_router(files_router)
app.include_router(chat_router)
app.include_router(context_router)
app.include_router(test_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Chat Assistant MVP",
        "version": "1.0.0",
        "description": "Enterprise-grade AI chat system with file upload and robust fallback mechanisms",
        "endpoints": {
            "health": "/health",
            "messages": "/messages",
            "files": "/files",
            "chat": "/chat",
            "context": "/context",
            "docs": "/docs"
        },
        "features": [
            "Google Gemini AI integration",
            "DeepAI backup system", 
            "Robust fallback mechanisms",
            "Smart context management",
            "File upload and analysis",
            "Chat persistence",
            "Beautiful React frontend",
            "Conversation analytics"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
