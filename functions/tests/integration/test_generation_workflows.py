"""Integration tests for generation workflows (non-credit related)."""

from unittest.mock import Mock, patch
from datetime import datetime

from services.generation_service import GenerationService
from schemas import GenerationStatus


class TestGenerationProcessing:
    """Test generation processing workflows."""
    
    @patch('services.generation_service.GenerationRepository')
    def test_process_generation_task_success(self, mock_gen_repo_class):
        mock_gen_repo = Mock()
        mock_gen_repo.update_generation_request.return_value = True
        mock_gen_repo.complete_generation_request.return_value = True
        mock_gen_repo_class.return_value = mock_gen_repo
        
        with patch('services.generation_service.AIModelService') as mock_ai_service_class:
            mock_ai_service = Mock()
            mock_ai_service.generate_image.return_value = {
                "success": True,
                "image_url": "https://example.com/image.jpg"
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
            
            # Assertions
            assert result["success"] is True
            assert result["generation_id"] == "gen_123"
            assert result["image_url"] == "https://example.com/image.jpg"
            
            # Verify operations
            mock_gen_repo.update_generation_request.assert_called()
            mock_gen_repo.complete_generation_request.assert_called_once_with(
                "gen_123", "https://example.com/image.jpg"
            )
    
    @patch('services.generation_service.GenerationRepository')
    def test_get_generation_status_success(self, mock_gen_repo_class):
        mock_gen_repo = Mock()
        mock_gen_repo.get_generation_request.return_value = {
            "id": "gen_123",
            "status": GenerationStatus.COMPLETED.value,
            "image_url": "https://example.com/image.jpg",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "completed_at": datetime.now()
        }
        mock_gen_repo_class.return_value = mock_gen_repo
        
        with patch('services.generation_service.TaskQueueService') as mock_task_queue_class:
            mock_task_queue = Mock()
            mock_task_queue_class.return_value = mock_task_queue
            
            service = GenerationService()
            
            # Execute
            result = service.get_generation_status("gen_123")
            
            # Assertions
            assert result["success"] is True
            assert result["data"]["generationRequestId"] == "gen_123"
            assert result["data"]["status"] == GenerationStatus.COMPLETED.value
            assert result["data"]["imageUrl"] == "https://example.com/image.jpg"
            assert result["data"]["progress"] == 100.0
    
    @patch('services.generation_service.GenerationRepository')
    def test_get_generation_status_not_found(self, mock_gen_repo_class):
        mock_gen_repo = Mock()
        mock_gen_repo.get_generation_request.return_value = None
        mock_gen_repo_class.return_value = mock_gen_repo
        
        service = GenerationService()
        
        # Execute
        result = service.get_generation_status("nonexistent_gen")
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "not_found"
        assert "Generation request not found" in result["message"]
    


class TestGenerationStatusCalculation:
    """Test generation progress calculation."""
    
    def test_calculate_progress_pending(self):
        service = GenerationService()
        progress = service._calculate_progress(GenerationStatus.PENDING.value)
        assert progress == 0.0
    
    def test_calculate_progress_queued(self):
        service = GenerationService()
        progress = service._calculate_progress(GenerationStatus.QUEUED.value)
        assert progress == 10.0
    
    def test_calculate_progress_processing(self):
        service = GenerationService()
        progress = service._calculate_progress(GenerationStatus.PROCESSING.value)
        assert progress == 50.0
    
    def test_calculate_progress_completed(self):
        service = GenerationService()
        progress = service._calculate_progress(GenerationStatus.COMPLETED.value)
        assert progress == 100.0
    
    def test_calculate_progress_failed(self):
        service = GenerationService()
        progress = service._calculate_progress(GenerationStatus.FAILED.value)
        assert progress == 100.0


class TestTaskPayloadValidation:
    """Test task payload validation."""
    
    def test_invalid_task_payload_validation(self):
        service = GenerationService()
        
        invalid_payload = {
            "generation_request_id": "gen_123",
            "user_id": "test_user",
            "model": "invalid_model",
            "style": "realistic",
            "color": "vibrant",
            "size": "1024x1024",
            "prompt": "Test image",
            "priority": "normal"
        }
        
        # Execute
        result = service.process_generation_task(invalid_payload)
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "validation"
        assert "Invalid task payload" in result["error"]
    
    def test_missing_required_fields_validation(self):
        service = GenerationService()
        
        incomplete_payload = {
            "generation_request_id": "gen_123",
            # Missing required fields
        }
        
        # Execute
        result = service.process_generation_task(incomplete_payload)
        
        # Assertions
        assert result["success"] is False
        assert result["error_type"] == "validation"
        assert "Invalid task payload" in result["error"]