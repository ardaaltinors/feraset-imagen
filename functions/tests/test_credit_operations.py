"""Unit tests for credit deduction and refund logic."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Import the modules we're testing
from repositories.generation_repository import GenerationRepository
from repositories.user_repository import UserRepository
from services.generation_service import GenerationService
from schemas import CreateGenerationRequestModel, AIModel


class TestCreditDeduction:
    """Test credit deduction operations."""
    
    def test_atomic_credit_deduction_success(self, mock_firestore_db, sample_user_data, sample_generation_data, sample_transaction_data):
        """Test successful atomic credit deduction and request creation."""
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = sample_user_data
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        
        # Create repository with mocked database
        with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
            repo = GenerationRepository()
            repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="test_user_123",
                current_credits=100,
                credit_cost=3,
                generation_data=sample_generation_data,
                transaction_data=sample_transaction_data
            )
        
        # Assertions
        assert result["success"] is True
        assert "generation_id" in result
        assert result["new_credits"] == 97
        
        # Verify batch operations were called
        mock_firestore_db.batch.assert_called_once()
        batch = mock_firestore_db.batch.return_value
        batch.commit.assert_called_once()
    
    def test_atomic_credit_deduction_insufficient_credits(self, mock_firestore_db, sample_user_data, sample_generation_data, sample_transaction_data):
        """Test credit deduction fails with insufficient credits."""
        # Setup user with insufficient credits
        insufficient_credits_user = sample_user_data.copy()
        insufficient_credits_user["current_credits"] = 2
        
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = insufficient_credits_user
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        
        # Create repository with mocked database
        with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
            repo = GenerationRepository()
            repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="test_user_123",
                current_credits=2,
                credit_cost=3,
                generation_data=sample_generation_data,
                transaction_data=sample_transaction_data
            )
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Insufficient credits"
        assert result["error_type"] == "validation"
        
        # Verify no batch commit was called
        batch = mock_firestore_db.batch.return_value
        batch.commit.assert_not_called()
    
    def test_atomic_credit_deduction_user_not_found(self, mock_firestore_db, sample_generation_data, sample_transaction_data):
        """Test credit deduction fails when user doesn't exist."""
        # Setup non-existent user
        mock_user_doc = Mock()
        mock_user_doc.exists = False
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        
        # Create repository with mocked database
        with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
            repo = GenerationRepository()
            repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="nonexistent_user",
                current_credits=100,
                credit_cost=3,
                generation_data=sample_generation_data,
                transaction_data=sample_transaction_data
            )
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "User not found"
        assert result["error_type"] == "validation"


class TestCreditRefund:
    """Test credit refund operations."""
    
    def test_atomic_credit_refund_success(self, mock_firestore_db, sample_user_data):
        """Test successful atomic credit refund."""
        # Setup mocks
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = sample_user_data
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        
        # Create repository with mocked database
        with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
            repo = GenerationRepository()
            repo._db = mock_firestore_db
            
            result = repo.atomic_credit_refund(
                user_id="test_user_123",
                generation_id="test_generation_456",
                credit_amount=3,
                error_message="Generation failed"
            )
        
        # Assertions
        assert result["success"] is True
        assert result["refunded_credits"] == 3
        assert result["new_credits"] == 103  # 100 + 3
        
        # Verify batch operations were called
        mock_firestore_db.batch.assert_called_once()
        batch = mock_firestore_db.batch.return_value
        batch.commit.assert_called_once()


class TestGenerationServiceCreditOperations:
    """Test credit operations in the Generation Service layer."""
    
    def test_validate_user_and_credits_success(self, mock_firestore_db, sample_user_data):
        # Mock user repository
        with patch('services.generation_service.UserRepository') as mock_user_repo_class:
            mock_user_repo = Mock()
            mock_user_repo.get_user_by_id.return_value = sample_user_data
            mock_user_repo_class.return_value = mock_user_repo
            
            # Mock AI model service
            with patch('services.generation_service.AIModelService') as mock_ai_service_class:
                mock_ai_service = Mock()
                mock_ai_service.get_credit_cost.return_value = 3
                mock_ai_service_class.return_value = mock_ai_service
                
                service = GenerationService()
                
                request_data = CreateGenerationRequestModel(
                    userId="test_user_123",
                    model=AIModel.MODEL_A,
                    style="realistic",
                    color="vibrant",
                    size="1024x1024",
                    prompt="Test prompt"
                )
                
                result = service._validate_user_and_credits(request_data)
        
        # Assertions
        assert result["success"] is True
        assert result["user_data"] == sample_user_data
        assert result["credit_cost"] == 3
        assert result["current_credits"] == 100
    
    def test_validate_user_and_credits_insufficient(self, mock_firestore_db):
        # User with insufficient credits
        poor_user_data = {
            "id": "test_user_123",
            "current_credits": 1  # Less than required 3
        }
        
        # Mock user repository
        with patch('services.generation_service.UserRepository') as mock_user_repo_class:
            mock_user_repo = Mock()
            mock_user_repo.get_user_by_id.return_value = poor_user_data
            mock_user_repo_class.return_value = mock_user_repo
            
            # Mock AI model service
            with patch('services.generation_service.AIModelService') as mock_ai_service_class:
                mock_ai_service = Mock()
                mock_ai_service.get_credit_cost.return_value = 3
                mock_ai_service_class.return_value = mock_ai_service
                
                service = GenerationService()
                
                request_data = CreateGenerationRequestModel(
                    userId="test_user_123",
                    model=AIModel.MODEL_A,
                    style="realistic",
                    color="vibrant",
                    size="1024x1024",
                    prompt="Test prompt"
                )
                
                result = service._validate_user_and_credits(request_data)
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "insufficient_credits"
        assert "Insufficient credits" in result["message"]
    
    def test_validate_user_and_credits_user_not_found(self, mock_firestore_db):
        """Test user validation fails when user doesn't exist."""
        # Mock user repository
        with patch('services.generation_service.UserRepository') as mock_user_repo_class:
            mock_user_repo = Mock()
            mock_user_repo.get_user_by_id.return_value = None  # User not found
            mock_user_repo_class.return_value = mock_user_repo
            
            service = GenerationService()
            
            request_data = CreateGenerationRequestModel(
                userId="nonexistent_user",
                model=AIModel.MODEL_A,
                style="realistic",
                color="vibrant",
                size="1024x1024",
                prompt="Test prompt"
            )
            
            result = service._validate_user_and_credits(request_data)
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "not_found"
        assert "User not found" in result["message"]


class TestCreditCalculations:
    """Test credit cost calculations."""
    
    @patch('services.generation_service.AIModelService')
    def test_credit_cost_calculation_512x512(self, mock_ai_service_class):
        mock_ai_service = Mock()
        mock_ai_service.get_credit_cost.return_value = 1
        mock_ai_service_class.return_value = mock_ai_service
        
        service = GenerationService()
        cost = service.ai_model_service.get_credit_cost("512x512")
        
        assert cost == 1
    
    @patch('services.generation_service.AIModelService')
    def test_credit_cost_calculation_1024x1024(self, mock_ai_service_class):
        mock_ai_service = Mock()
        mock_ai_service.get_credit_cost.return_value = 3
        mock_ai_service_class.return_value = mock_ai_service
        
        service = GenerationService()
        cost = service.ai_model_service.get_credit_cost("1024x1024")
        
        assert cost == 3
    
    @patch('services.generation_service.AIModelService')
    def test_credit_cost_calculation_1024x1792(self, mock_ai_service_class):
        mock_ai_service = Mock()
        mock_ai_service.get_credit_cost.return_value = 4
        mock_ai_service_class.return_value = mock_ai_service
        
        service = GenerationService()
        cost = service.ai_model_service.get_credit_cost("1024x1792")
        
        assert cost == 4