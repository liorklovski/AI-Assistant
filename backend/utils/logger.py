import logging
import sys
from datetime import datetime

def setup_logger(name: str = "ai_chat_app", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Create global logger instances for different components
main_logger = setup_logger("ai_chat.main")
ai_logger = setup_logger("ai_chat.ai_service") 
context_logger = setup_logger("ai_chat.context")
file_logger = setup_logger("ai_chat.file_service")
api_logger = setup_logger("ai_chat.api")
