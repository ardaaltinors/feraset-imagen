"""Pytest configuration"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_firestore_db():
    """Mock Firestore database for testing."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    mock_batch = Mock()
    
    # Setup basic mock structure
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_db.batch.return_value = mock_batch
    
    return mock_db

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test_user_123",
        "name": "Test User",
        "email": "test@example.com",
        "current_credits": 100,
        "total_credits": 500,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_generation_data():
    """Sample generation request data for testing."""
    return {
        "user_id": "test_user_123",
        "model": "model_a",
        "style": "realistic",
        "color": "vibrant",
        "size": "1024x1024",
        "prompt": "A beautiful landscape",
        "status": "pending",
        "credits_deducted": 3
    }

@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        "type": "deduction",
        "credits": 3,
        "description": "Image generation - model_a - 1024x1024",
        "user_id": "test_user_123"
    }

@pytest.fixture(autouse=True)
def mock_firebase_admin():
    """Auto-used fixture to mock Firebase Admin SDK initialization."""
    with patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.firestore.client'):
        yield

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "FIREBASE_PROJECT_ID": "test-project",
        "COLLECTIONS": {
            "users": "test_users",
            "generation_requests": "test_generation_requests",
            "styles": "test_styles",
            "colors": "test_colors",
            "sizes": "test_sizes"
        }
    }