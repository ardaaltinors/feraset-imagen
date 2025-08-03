"""Integration tests for credit-related workflows."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from services.generation_service import GenerationService
from repositories.user_repository import UserRepository
from schemas import CreateGenerationRequestModel, AIModel, GenerationStatus


class TestCreditWorkflowIntegration:
    """Test complete credit workflows end-to-end."""
    
    @patch('services.generation_service.TaskQueueService')
    @patch('services.generation_service.AIModelService')
    @patch('services.generation_service.GenerationRepository')
    @patch('services.generation_service.UserRepository')
    def test_complete_generation_request_workflow_success(
        self, 
        mock_user_repo_class,
        mock_gen_repo_class,
        mock_ai_service_class,
        mock_task_queue_class
    ):
        # Setup mocks
        mock_user_repo = Mock()
        mock_user_repo.get_user_by_id.return_value = {
            "id": "test_user",
            "current_credits": 100,
            "name": "Test User"
        }
        mock_user_repo_class.return_value = mock_user_repo
        
        mock_gen_repo = Mock()
        mock_gen_repo.atomic_credit_deduction_and_request_creation.return_value = {
            "success": True,
            "generation_id": "gen_123",
            "new_credits": 97
        }
        mock_gen_repo.update_generation_request.return_value = True
        mock_gen_repo_class.return_value = mock_gen_repo
        
        mock_ai_service = Mock()
        mock_ai_service.get_credit_cost.return_value = 3
        mock_ai_service.validate_generation_parameters.return_value = {"valid": True}
        mock_ai_service_class.return_value = mock_ai_service
        
        mock_task_queue = Mock()
        mock_task_queue.enqueue_generation_task.return_value = True
        mock_task_queue_class.return_value = mock_task_queue
        
        # Create service and request
        service = GenerationService()
        request_data = CreateGenerationRequestModel(
            userId="test_user",
            model=AIModel.MODEL_A,
            style="realistic",
            color="vibrant",
            size="1024x1024",
            prompt="Test image"
        )
        
        # Execute
        result = service.create_generation_request(request_data)
        
        # Assertions
        assert result["success"] is True
        assert result["data"]["generationRequestId"] == "gen_123"
        assert result["data"]["status"] == GenerationStatus.QUEUED.value
        assert result["data"]["deductedCredits"] == 3
        
        # Verify all operations were called
        mock_user_repo.get_user_by_id.assert_called_once_with("test_user")
        mock_ai_service.get_credit_cost.assert_called_once_with("1024x1024")
        mock_gen_repo.atomic_credit_deduction_and_request_creation.assert_called_once()
        mock_task_queue.enqueue_generation_task.assert_called_once()
    
    @patch('services.generation_service.TaskQueueService')
    @patch('services.generation_service.AIModelService')
    @patch('services.generation_service.GenerationRepository')
    @patch('services.generation_service.UserRepository')
    def test_generation_request_failure_with_refund(
        self, 
        mock_user_repo_class,
        mock_gen_repo_class,
        mock_ai_service_class,
        mock_task_queue_class
    ):
        # Setup mocks
        mock_user_repo = Mock()
        mock_user_repo.get_user_by_id.return_value = {
            "id": "test_user",
            "current_credits": 100,
            "name": "Test User"
        }
        mock_user_repo_class.return_value = mock_user_repo
        
        mock_gen_repo = Mock()
        mock_gen_repo.atomic_credit_deduction_and_request_creation.return_value = {
            "success": True,
            "generation_id": "gen_123",
            "new_credits": 97
        }
        mock_gen_repo.atomic_credit_refund.return_value = {
            "success": True,
            "refunded_credits": 3,
            "new_credits": 100
        }
        mock_gen_repo_class.return_value = mock_gen_repo
        
        mock_ai_service = Mock()
        mock_ai_service.get_credit_cost.return_value = 3
        mock_ai_service.validate_generation_parameters.return_value = {"valid": True}
        mock_ai_service_class.return_value = mock_ai_service
        
        # Task queue fails
        mock_task_queue = Mock()
        mock_task_queue.enqueue_generation_task.return_value = False
        mock_task_queue_class.return_value = mock_task_queue
        
        # Create service and request
        service = GenerationService()
        request_data = CreateGenerationRequestModel(
            userId="test_user",
            model=AIModel.MODEL_A,
            style="realistic",
            color="vibrant",
            size="1024x1024",
            prompt="Test image"
        )
        
        # Execute
        result = service.create_generation_request(request_data)
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "queue_failure"
        assert result["refunded"] is True
        assert "Credits have been refunded" in result["message"]
        
        # Verify refund was called
        mock_gen_repo.atomic_credit_refund.assert_called_once_with(
            user_id="test_user",
            generation_id="gen_123",
            credit_amount=3,
            error_message="Failed to queue generation task"
        )
    
    
    @patch('services.generation_service.GenerationRepository')
    def test_process_generation_task_failure_with_refund(self, mock_gen_repo_class):
        mock_gen_repo = Mock()
        mock_gen_repo.update_generation_request.return_value = True
        mock_gen_repo.get_generation_request.return_value = {
            "id": "gen_123",
            "credits_deducted": 3
        }
        mock_gen_repo.atomic_credit_refund.return_value = {
            "success": True,
            "refunded_credits": 3
        }
        mock_gen_repo_class.return_value = mock_gen_repo
        
        with patch('services.generation_service.AIModelService') as mock_ai_service_class:
            mock_ai_service = Mock()
            mock_ai_service.generate_image.return_value = {
                "success": False,
                "error": "AI model failed"
            }
            mock_ai_service_class.return_value = mock_ai_service
            
            service = GenerationService()
            
            task_payload = {
                "generation_request_id": "gen_123",
                "user_id": "test_user",
                "model": "Model A",
                "style": "realistic",
                "color": "vibrant",
                "size": "1024x1024",
                "prompt": "Test image",
                "priority": "normal"
            }
            
            # Execute
            result = service.process_generation_task(task_payload)
            
            assert result["success"] is False
            assert result["generation_id"] == "gen_123"
            assert result["error"] == "AI model failed"
            assert result["refunded"] is True
            
            mock_gen_repo.atomic_credit_refund.assert_called_once_with(
                user_id="test_user",
                generation_id="gen_123",
                credit_amount=3,
                error_message="AI model failed"
            )


class TestUserCreditOperations:
    """Test user credit operations integration."""
    
    @patch('firebase_admin.firestore.client')
    def test_get_user_credits_with_transactions(self, mock_firestore_client):
        """Test retrieving user credits with transaction history."""
        # Setup mock database responses
        mock_db = Mock()
        mock_firestore_client.return_value = mock_db
        
        # Mock user document
        mock_user_doc = Mock()
        mock_user_doc.to_dict.return_value = {
            "id": "test_user",
            "current_credits": 75,
            "name": "Test User"
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        
        # Mock transactions
        mock_transaction_docs = [
            Mock(id="txn_1", to_dict=lambda: {
                "type": "deduction",
                "credits": 3,
                "description": "Image generation",
                "timestamp": datetime.now(),
                "generation_request_id": "gen_123"
            }),
            Mock(id="txn_2", to_dict=lambda: {
                "type": "refund",
                "credits": 3,
                "description": "Failed generation refund",
                "timestamp": datetime.now(),
                "generation_request_id": "gen_124"
            })
        ]
        
        mock_transactions_collection = Mock()
        mock_transactions_collection.order_by.return_value.stream.return_value = mock_transaction_docs
        mock_db.collection.return_value.document.return_value.collection.return_value = mock_transactions_collection
        
        # Execute
        repo = UserRepository()
        result = repo.get_user_credits_with_transactions("test_user")
        
        # Assertions
        assert result is not None
        assert result.current_credits == 75
        assert len(result.transactions) == 2
        assert result.transactions[0].type == "deduction"
        assert result.transactions[1].type == "refund"