"""Configuration settings for the application."""

import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Firebase settings
    PROJECT_ID = os.getenv('PROJECT_ID', 'feraset-imagen')
    REGION = os.getenv('REGION', 'us-central1')
    
    # Firestore collections
    COLLECTIONS = {
        "styles": "styles",
        "colors": "colors", 
        "sizes": "sizes",
        "users": "users",
        "images": "images",
        "generation_requests": "generation_requests",
        "reports": "reports"
    }
    
    # Logging configuration
    LOG_LEVEL = logging.INFO
    
    # Firebase Functions settings
    MAX_INSTANCES = 10
    
    # Cloud Tasks configuration
    TASK_QUEUE_CONFIG = {
        "retry_config": {
            "max_attempts": 5,
            "min_backoff_seconds": 60,
            "max_backoff_seconds": 300
        },
        "rate_limits": {
            "max_concurrent_dispatches": 10,
            "max_dispatches_per_second": 2
        }
    }
    
    # Generation processing settings
    GENERATION_CONFIG = {
        "timeout_seconds": 180,  # 3 min
        "max_queue_size": 1000,
        "priority_levels": ["low", "normal", "high"],
        "default_priority": "normal"
    }
    
    # Worker function URLs
    @classmethod
    def is_emulator(cls) -> bool:
        emulator = os.getenv('RUNNING_ON_EMULATOR', 'false').lower()
        if emulator == 'true':
            return True
        if emulator == 'false':
            return False
        return False
    
    @classmethod
    def get_worker_function_url(cls, function_name: str = "processImageGeneration") -> str:
        """Get worker function URL based on environment."""
        if cls.is_emulator():  # Emulator
            return f"http://127.0.0.1:5551/feraset-imagen/us-central1/{function_name}"
        else:  # Production
            return f"https://{cls.REGION}-{cls.PROJECT_ID}.cloudfunctions.net/{function_name}"
    
    
    # Anomaly detection thresholds
    ANOMALY_DETECTION = {
        "user_request_spike_threshold": 10,  # Requests per user per day above average
        "total_request_spike_multiplier": 2.5,  # Total requests multiplier vs historical
        "credit_consumption_spike_multiplier": 3.0,  # Credit usage multiplier vs historical
        "failure_rate_threshold": 0.15,  # 15% failure rate threshold
        "new_user_spike_threshold": 5,  # New users per day threshold
        "single_user_credit_threshold": 50,  # Credits consumed by single user per day
        "historical_days": 14  # Days to look back for historical averages
    }
    
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