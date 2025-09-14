"""
Constants for the AI Chat Assistant application
"""

from pathlib import Path

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {
    '.txt', '.pdf', '.docx', '.jpg', '.jpeg', '.png', '.csv', '.json'
}
UPLOAD_DIRECTORY = "uploads"

# Ensure upload directory exists
Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)
