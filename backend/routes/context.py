"""
Context analytics and management endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from utils.context_manager import get_optimized_context
from utils import MessageService
from services import FileService

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/analytics")
async def get_context_analytics():
    """Get detailed analytics about conversation context optimization"""
    try:
        # Get all messages and files
        message_jobs = MessageService.get_all_message_jobs()
        file_jobs = FileService.get_all_file_jobs()
        
        # Build complete chat history
        all_items = []
        
        # Add message jobs
        for job in message_jobs.values():
            if job.status.value == "done":  # Only completed jobs
                all_items.append({
                    "type": "message",
                    "user_message": job.user_message,
                    "ai_response": job.ai_response,
                    "status": "done",
                    "created_at": job.created_at.isoformat()
                })
        
        # Add file jobs
        for job in file_jobs.values():
            if job.status.value == "done":  # Only completed jobs
                all_items.append({
                    "type": "file",
                    "original_filename": job.original_filename,
                    "file_type": job.file_type,
                    "file_size": job.file_size,
                    "analysis_result": job.analysis_result,
                    "status": "done",
                    "created_at": job.created_at.isoformat()
                })
        
        # Sort by creation time
        all_items.sort(key=lambda x: x['created_at'])
        
        if not all_items:
            return {
                "total_messages": 0,
                "context_optimization": "No messages to analyze",
                "user_info": {},
                "recommendations": ["Start a conversation to see context analytics"]
            }
        
        # Get context optimization for current conversation
        current_context = get_optimized_context(all_items, "")
        
        # Calculate analytics
        total_chars = sum(
            len(msg.get('user_message', '')) + len(msg.get('ai_response', ''))
            for msg in all_items
        )
        
        optimized_chars = current_context["total_length"]
        compression_ratio = (1 - optimized_chars / max(total_chars, 1)) * 100
        
        # Analyze conversation patterns
        user_questions = sum(1 for msg in all_items if msg.get('user_message', '').endswith('?'))
        file_uploads = sum(1 for msg in all_items if msg.get('type') == 'file')
        
        return {
            "conversation_stats": {
                "total_messages": len(all_items),
                "total_characters": total_chars,
                "optimized_characters": optimized_chars,
                "compression_ratio_percent": round(compression_ratio, 2),
                "user_questions": user_questions,
                "file_uploads": file_uploads
            },
            "context_optimization": {
                "optimization_applied": current_context["optimization_applied"],
                "context_summary": current_context["context_summary"],
                "messages_in_context": len(current_context["optimized_context"]),
                "total_messages_available": len(all_items)
            },
            "user_profile": current_context["user_info"],
            "conversation_insights": {
                "question_rate": round((user_questions / max(len(all_items), 1)) * 100, 1),
                "avg_message_length": round(total_chars / max(len(all_items), 1), 1),
                "file_interaction_rate": round((file_uploads / max(len(all_items), 1)) * 100, 1)
            },
            "recommendations": _generate_context_recommendations(current_context, all_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing context: {str(e)}")


@router.post("/optimize")
async def optimize_current_context(test_message: str = "What can you tell me about our conversation?"):
    """Test context optimization with a sample message"""
    try:
        # Get current conversation
        message_jobs = MessageService.get_all_message_jobs()
        file_jobs = FileService.get_all_file_jobs()
        
        # Build chat history
        all_items = []
        for job in message_jobs.values():
            if job.status.value == "done":
                all_items.append({
                    "type": "message",
                    "user_message": job.user_message,
                    "ai_response": job.ai_response,
                    "status": "done",
                    "created_at": job.created_at.isoformat()
                })
        
        for job in file_jobs.values():
            if job.status.value == "done":
                all_items.append({
                    "type": "file",
                    "original_filename": job.original_filename,
                    "file_type": job.file_type,
                    "file_size": job.file_size,
                    "analysis_result": job.analysis_result,
                    "status": "done",
                    "created_at": job.created_at.isoformat()
                })
        
        all_items.sort(key=lambda x: x['created_at'])
        
        # Get optimization results
        optimization = get_optimized_context(all_items, test_message)
        
        return {
            "test_message": test_message,
            "original_context": {
                "message_count": len(all_items),
                "total_length": sum(
                    len(msg.get('user_message', '')) + len(msg.get('ai_response', ''))
                    for msg in all_items
                )
            },
            "optimized_context": {
                "message_count": len(optimization["optimized_context"]),
                "total_length": optimization["total_length"],
                "optimization_applied": optimization["optimization_applied"]
            },
            "user_info": optimization["user_info"],
            "context_summary": optimization["context_summary"],
            "compression_ratio": round(
                (1 - optimization["total_length"] / max(sum(
                    len(msg.get('user_message', '')) + len(msg.get('ai_response', ''))
                    for msg in all_items
                ), 1)) * 100, 2
            ) if all_items else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing context: {str(e)}")


def _generate_context_recommendations(context_data: Dict[str, Any], all_messages: list) -> list:
    """Generate intelligent recommendations based on context analysis"""
    recommendations = []
    
    # Check conversation length
    if len(all_messages) > 50:
        recommendations.append("Consider starting a new conversation topic for optimal context management")
    
    # Check if user info is detected
    if not context_data["user_info"]:
        recommendations.append("Try introducing yourself (e.g., 'My name is...') for more personalized responses")
    
    # Check optimization effectiveness
    if context_data["optimization_applied"]:
        recommendations.append("Context optimization is active - AI focuses on most relevant conversation parts")
    
    # Check for file interactions
    file_count = sum(1 for msg in all_messages if msg.get('type') == 'file')
    if file_count == 0:
        recommendations.append("Try uploading a file to see AI-powered document analysis")
    
    # Check question engagement
    question_count = sum(1 for msg in all_messages if msg.get('user_message', '').endswith('?'))
    if question_count < len(all_messages) * 0.3:
        recommendations.append("Ask more questions to get the most out of the AI assistant")
    
    return recommendations if recommendations else ["Great conversation! Keep chatting for optimal AI interactions"]
