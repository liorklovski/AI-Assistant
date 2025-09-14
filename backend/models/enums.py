"""
Enums for the AI Chat Assistant application
"""

from enum import Enum


class JobStatus(str, Enum):
    """Status of a job (message or file processing)"""
    PENDING = "pending"
    PROCESSING = "processing" 
    DONE = "done"
    ERROR = "error"


class JobType(str, Enum):
    """Type of job being processed"""
    MESSAGE = "message"
    FILE = "file"
