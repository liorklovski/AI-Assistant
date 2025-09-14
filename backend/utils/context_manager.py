"""
Intelligent context management for AI conversations
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class ConversationContext:
    def __init__(self, max_context_length: int = 4000, max_messages: int = 20):
        self.max_context_length = max_context_length
        self.max_messages = max_messages
        
        # Context scoring weights
        self.weights = {
            "recency": 0.4,      # Recent messages are more important
            "length": 0.2,       # Longer messages might be more important
            "keywords": 0.3,     # Messages with important keywords
            "user_intent": 0.1   # Messages showing clear user intent
        }
        
        # Important keywords that boost message importance
        self.important_keywords = [
            "important", "remember", "note", "key", "critical", 
            "name", "email", "phone", "address", "password",
            "error", "problem", "issue", "help", "urgent"
        ]
        
        # User intent patterns
        self.intent_patterns = [
            r"my name is (\w+)",
            r"i am (\w+)",
            r"call me (\w+)",
            r"remember that i",
            r"don't forget",
            r"keep in mind"
        ]
    
    def _calculate_message_score(self, message: Dict, index: int, total_messages: int) -> float:
        """Calculate importance score for a message"""
        text = message.get('user_message', '') + ' ' + message.get('ai_response', '')
        text = text.lower()
        
        # Recency score (more recent = higher score)
        recency_score = (total_messages - index) / total_messages
        
        # Length score (normalize to 0-1)
        length_score = min(len(text) / 200, 1.0)  # Cap at 200 chars for score
        
        # Keyword score
        keyword_count = sum(1 for keyword in self.important_keywords if keyword in text)
        keyword_score = min(keyword_count / 3, 1.0)  # Cap at 3 keywords
        
        # Intent score
        intent_score = 0.0
        for pattern in self.intent_patterns:
            if re.search(pattern, text):
                intent_score = 1.0
                break
        
        # Weighted final score
        final_score = (
            self.weights["recency"] * recency_score +
            self.weights["length"] * length_score +
            self.weights["keywords"] * keyword_score +
            self.weights["user_intent"] * intent_score
        )
        
        return final_score
    
    def _extract_user_info(self, messages: List[Dict]) -> Dict[str, str]:
        """Extract persistent user information from conversation"""
        user_info = {}
        
        for message in messages:
            text = message.get('user_message', '').lower()
            
            # Extract name
            name_patterns = [
                r"my name is (\w+)",
                r"i am (\w+)",
                r"call me (\w+)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text)
                if match:
                    user_info["name"] = match.group(1).title()
                    break
            
            # Extract preferences
            if "i like" in text or "i love" in text:
                pref_match = re.search(r"i (?:like|love) ([^.!?]+)", text)
                if pref_match:
                    if "preferences" not in user_info:
                        user_info["preferences"] = []
                    user_info["preferences"].append(pref_match.group(1).strip())
            
            # Extract dislikes
            if "i hate" in text or "i don't like" in text:
                dislike_match = re.search(r"i (?:hate|don't like) ([^.!?]+)", text)
                if dislike_match:
                    if "dislikes" not in user_info:
                        user_info["dislikes"] = []
                    user_info["dislikes"].append(dislike_match.group(1).strip())
        
        return user_info
    
    def optimize_context(self, messages: List[Dict], current_message: str = "") -> Dict[str, Any]:
        """Intelligently optimize conversation context"""
        if not messages:
            return {
                "optimized_context": [],
                "user_info": {},
                "context_summary": "Starting new conversation",
                "total_length": 0,
                "optimization_applied": False
            }
        
        # Score all messages
        scored_messages = []
        for i, message in enumerate(messages):
            score = self._calculate_message_score(message, i, len(messages))
            scored_messages.append((message, score))
        
        # Sort by score (highest first) but keep some recent messages
        scored_messages.sort(key=lambda x: x[1], reverse=True)
        
        # Always include last 3 messages + highest scoring messages
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        important_messages = [msg for msg, score in scored_messages[:5] if msg not in recent_messages]
        
        # Combine and deduplicate
        context_messages = important_messages + recent_messages
        
        # Calculate total context length
        total_length = sum(
            len(msg.get('user_message', '')) + len(msg.get('ai_response', ''))
            for msg in context_messages
        )
        
        # Trim if too long
        if total_length > self.max_context_length:
            context_messages = self._trim_context(context_messages, current_message)
        
        # Extract user information
        user_info = self._extract_user_info(messages)
        
        # Create context summary
        context_summary = self._create_context_summary(messages, user_info)
        
        return {
            "optimized_context": context_messages[-self.max_messages:],  # Limit message count
            "user_info": user_info,
            "context_summary": context_summary,
            "total_length": sum(
                len(msg.get('user_message', '')) + len(msg.get('ai_response', ''))
                for msg in context_messages[-self.max_messages:]
            ),
            "optimization_applied": len(context_messages) < len(messages)
        }
    
    def _trim_context(self, messages: List[Dict], current_message: str) -> List[Dict]:
        """Trim context to fit within length limits"""
        current_length = len(current_message)
        available_length = self.max_context_length - current_length
        
        trimmed_messages = []
        used_length = 0
        
        # Add messages from newest to oldest until we hit the limit
        for message in reversed(messages):
            msg_length = len(message.get('user_message', '')) + len(message.get('ai_response', ''))
            if used_length + msg_length <= available_length:
                trimmed_messages.insert(0, message)  # Insert at beginning to maintain order
                used_length += msg_length
            else:
                break
        
        return trimmed_messages
    
    def _create_context_summary(self, messages: List[Dict], user_info: Dict) -> str:
        """Create a summary of the conversation context"""
        if not messages:
            return "New conversation started"
        
        summary_parts = []
        
        # Add user info if available
        if user_info.get("name"):
            summary_parts.append(f"User: {user_info['name']}")
        
        # Add conversation length
        summary_parts.append(f"Messages: {len(messages)}")
        
        # Add recent topics (keywords from recent messages)
        recent_text = ' '.join([
            msg.get('user_message', '') for msg in messages[-3:]
        ]).lower()
        
        # Extract topics
        topics = []
        for keyword in self.important_keywords:
            if keyword in recent_text:
                topics.append(keyword)
        
        if topics:
            summary_parts.append(f"Recent topics: {', '.join(topics[:3])}")
        
        return " | ".join(summary_parts)

# Global context manager instance
context_manager = ConversationContext()

def get_optimized_context(messages: List[Dict], current_message: str = "") -> Dict[str, Any]:
    """Get optimized conversation context"""
    return context_manager.optimize_context(messages, current_message)
