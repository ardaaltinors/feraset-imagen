"""Configuration settings for the application."""

import logging
from typing import Dict, Any


class Config:
    """Application configuration."""
    
    # Firebase settings
    PROJECT_ID = "demo-project"
    
    # Firestore collections
    COLLECTIONS = {
        "styles": "styles",
        "colors": "colors", 
        "sizes": "sizes",
        "users": "users",
        "images": "images",
        "generation_requests": "generation_requests"
    }
    
    # Logging configuration
    LOG_LEVEL = logging.INFO
    
    # Firebase Functions settings
    MAX_INSTANCES = 10
    
    @classmethod
    def get_collection_name(cls, collection: str) -> str:
        """Get collection name from config."""
        return cls.COLLECTIONS.get(collection, collection)


def setup_logging() -> None:
    """Setup application logging."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )