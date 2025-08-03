"""Service layer for generation request business logic."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from repositories import GenerationRepository, UserRepository
from services.ai_model_service import AIModelService
from services.task_queue_service import TaskQueueService
from schemas import (
    CreateGenerationRequestModel, 
    GenerationRequestModel,
    CreateGenerationResponseModel,
    GenerationStatusResponseModel,
    TaskPayloadModel,
    TransactionType,
    GenerationStatus,
    AIModel
)
from core import Config


class GenerationService:
    """Service for handling generation request business logic."""
    
    def __init__(self):
        """Initialize generation service with repositories and services."""
        self.generation_repository = GenerationRepository()
        self.user_repository = UserRepository()
        self.ai_model_service = AIModelService(failure_rate=0.05)  # 5% failure rate
        self.task_queue_service = TaskQueueService()
        self.logger = logging.getLogger(__name__)
    
    def create_generation_request(
        self, 
        request_data: CreateGenerationRequestModel
    ) -> Dict[str, Any]:
        """
        Create a new generation request and queue it for asynchronous processing.
        """
        try:
            self.logger.info(
                "Creating async generation request for user %s with model %s",
                request_data.userId, request_data.model.value
            )
            
            # Step 1: Validate user exists and has sufficient credits
            user_validation = self._validate_user_and_credits(request_data)
            if not user_validation["success"]:
                return user_validation
            
            user_data = user_validation["user_data"]
            credit_cost = user_validation["credit_cost"]
            
            # Step 2: Validate generation parameters
            param_validation = self.ai_model_service.validate_generation_parameters(
                request_data.style, request_data.color, request_data.size
            )
            if not param_validation["valid"]:
                return {
                    "success": False,
                    "message": "Invalid generation parameters",
                    "errors": param_validation["errors"],
                    "error_type": "validation"
                }
            
            # Step 3: Atomically deduct credits and create generation request
            credit_deduction_result = self._deduct_credits_and_create_request_async(
                request_data, credit_cost, user_data
            )
            if not credit_deduction_result["success"]:
                return credit_deduction_result
            
            generation_id = credit_deduction_result["generation_id"]
            
            # Step 4: Create task payload for background processing
            task_payload = TaskPayloadModel(
                generation_request_id=generation_id,
                user_id=request_data.userId,
                model=request_data.model,
                style=request_data.style,
                color=request_data.color,
                size=request_data.size,
                prompt=request_data.prompt,
                priority=Config.GENERATION_CONFIG["default_priority"]
            )
            
            # Step 5: Enqueue task for background processing
            queue_success = self.task_queue_service.enqueue_generation_task(
                generation_request_id=generation_id,
                task_payload=task_payload.dict(),
                priority=task_payload.priority
            )
            
            if not queue_success:
                # Revert the credit deduction if queueing fails
                refund_result = self.generation_repository.atomic_credit_refund(
                    user_id=request_data.userId,
                    generation_id=generation_id,
                    credit_amount=credit_cost,
                    error_message="Failed to queue generation task"
                )
                
                return {
                    "success": False,
                    "message": "Failed to queue generation request. Credits have been refunded.",
                    "error": "Queue service unavailable",
                    "error_type": "queue_failure",
                    "refunded": refund_result["success"]
                }
            
            # Step 6: Update status to queued
            self.generation_repository.update_generation_request(
                generation_id, 
                {"status": GenerationStatus.QUEUED.value}
            )
            
            # Step 7: Calculate estimated completion time
            estimated_completion = self.task_queue_service.estimate_completion_time()
            
            self.logger.info(
                "Generation request %s queued successfully for user %s",
                generation_id, request_data.userId
            )
            
            return {
                "success": True,
                "data": {
                    "generationRequestId": generation_id,
                    "status": GenerationStatus.QUEUED.value,
                    "deductedCredits": credit_cost,
                    "estimatedCompletionTime": estimated_completion.isoformat() if estimated_completion else None,
                    "queuePosition": None  # Could be implemented with more complex queue tracking
                },
                "message": "Generation request queued successfully"
            }
                    
        except Exception as e:
            self.logger.error(
                "Unexpected error in create_generation_request: %s", str(e)
            )
            return {
                "success": False,
                "message": f"System error: {str(e)}",
                "error": str(e),
                "error_type": "system"
            }
    
    def _validate_user_and_credits(
        self, 
        request_data: CreateGenerationRequestModel
    ) -> Dict[str, Any]:
        """
        Validate user exists and has sufficient credits.
        """
        # Check if user exists
        user_data = self.user_repository.get_user_by_id(request_data.userId)
        if not user_data:
            return {
                "success": False,
                "message": f"User not found: {request_data.userId}",
                "error": "User does not exist",
                "error_type": "not_found"
            }
        
        # Calculate credit cost
        credit_cost = self.ai_model_service.get_credit_cost(request_data.size)
        if credit_cost == 0:
            return {
                "success": False,
                "message": f"Invalid image size: {request_data.size}",
                "error": "Unknown image size",
                "error_type": "validation"
            }
        
        # Check sufficient credits
        current_credits = user_data.get("current_credits", 0)
        if current_credits < credit_cost:
            return {
                "success": False,
                "message": f"Insufficient credits. Required: {credit_cost}, Available: {current_credits}",
                "error": "Insufficient credits",
                "error_type": "insufficient_credits"
            }
        
        return {
            "success": True,
            "user_data": user_data,
            "credit_cost": credit_cost,
            "current_credits": current_credits
        }
    
    def _deduct_credits_and_create_request_async(
        self,
        request_data: CreateGenerationRequestModel,
        credit_cost: int,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deduct credits and create generation request for task processing.
        """
        # Prepare generation request data with pending status
        generation_data = {
            "user_id": request_data.userId,
            "model": request_data.model.value,
            "style": request_data.style,
            "color": request_data.color,
            "size": request_data.size,
            "prompt": request_data.prompt,
            "status": GenerationStatus.PENDING.value,
            "credits_deducted": credit_cost
        }
        
        # Prepare transaction data
        transaction_data = {
            "type": TransactionType.DEDUCTION.value,
            "credits": credit_cost,
            "description": f"Image generation - {request_data.model.value} - {request_data.size}"
        }
        
        # Perform atomic operation
        result = self.generation_repository.atomic_credit_deduction_and_request_creation(
            user_id=request_data.userId,
            current_credits=user_data.get("current_credits", 0),
            credit_cost=credit_cost,
            generation_data=generation_data,
            transaction_data=transaction_data
        )
        
        if result["success"]:
            self.logger.info(
                "Credits deducted and async generation request created: %s (Cost: %d)",
                result["generation_id"], credit_cost
            )
        else:
            self.logger.error(
                "Failed to deduct credits for user %s: %s",
                request_data.userId, result.get("error")
            )
        
        return result
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Get current status of a generation request.
        """
        try:
            request_data = self.generation_repository.get_generation_request(generation_id)
            
            if not request_data:
                return {
                    "success": False,
                    "message": f"Generation request not found: {generation_id}",
                    "error": "Request does not exist",
                    "error_type": "not_found"
                }
            
            # Calculate progress based on status
            progress = self._calculate_progress(request_data.get("status"))
            
            # Get estimated completion time if still processing
            estimated_completion = None
            if request_data.get("status") in [GenerationStatus.QUEUED.value, GenerationStatus.PROCESSING.value]:
                estimated_completion = self.task_queue_service.estimate_completion_time()
            
            status_response = GenerationStatusResponseModel(
                generationRequestId=generation_id,
                status=request_data.get("status", GenerationStatus.PENDING.value),
                imageUrl=request_data.get("image_url"),
                error_message=request_data.get("error_message"),
                progress=progress,
                created_at=request_data.get("created_at"),
                updated_at=request_data.get("updated_at"),
                completed_at=request_data.get("completed_at"),
                estimated_completion_time=estimated_completion
            )
            
            return {
                "success": True,
                "data": status_response.dict(),
                "message": "Generation status retrieved successfully"
            }
            
        except Exception as e:
            self.logger.error(
                "Error retrieving generation status %s: %s", generation_id, str(e)
            )
            return {
                "success": False,
                "message": f"Failed to retrieve generation status: {str(e)}",
                "error": str(e),
                "error_type": "system"
            }
    
    def process_generation_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a generation task from the queue (called by background worker).
        """
        try:
            # Validate and parse task payload
            try:
                payload = TaskPayloadModel(**task_payload)
            except Exception as e:
                self.logger.error(f"Invalid task payload: {str(e)}")
                return {
                    "success": False,
                    "error": f"Invalid task payload: {str(e)}",
                    "error_type": "validation"
                }
            
            generation_id = payload.generation_request_id
            
            self.logger.info(f"Processing generation task: {generation_id}")
            
            # Update status to processing
            self.generation_repository.update_generation_request(
                generation_id,
                {
                    "status": GenerationStatus.PROCESSING.value,
                    "updated_at": datetime.now()
                }
            )
            
            # Perform AI generation
            generation_result = self.ai_model_service.generate_image(
                model=payload.model,
                style=payload.style,
                color=payload.color,
                size=payload.size,
                prompt=payload.prompt,
                generation_request_id=generation_id
            )
            
            # Handle generation result
            if generation_result["success"]:
                # Success: Update generation request with image URL
                image_url = generation_result["image_url"]
                self.generation_repository.complete_generation_request(
                    generation_id, image_url
                )
                
                self.logger.info(
                    "Background generation successful for request %s: %s",
                    generation_id, image_url
                )
                
                return {
                    "success": True,
                    "generation_id": generation_id,
                    "image_url": image_url,
                    "message": "Image generated successfully"
                }
            else:
                # Failure: Refund credits and update status
                error_message = generation_result.get("error", "Generation failed")
                credit_cost = self._get_credit_cost_from_request(generation_id)
                
                refund_result = self.generation_repository.atomic_credit_refund(
                    user_id=payload.user_id,
                    generation_id=generation_id,
                    credit_amount=credit_cost,
                    error_message=error_message
                )
                
                self.logger.warning(
                    "Background generation failed for request %s: %s. Refund success: %s",
                    generation_id, error_message, refund_result["success"]
                )
                
                return {
                    "success": False,
                    "generation_id": generation_id,
                    "error": error_message,
                    "refunded": refund_result["success"],
                    "message": f"Generation failed: {error_message}"
                }
                
        except Exception as e:
            self.logger.error(f"Unexpected error in process_generation_task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "system"
            }
    
    def _calculate_progress(self, status: str) -> float:
        """Calculate progress percentage based on status."""
        status_progress = {
            GenerationStatus.PENDING.value: 0.0,
            GenerationStatus.QUEUED.value: 10.0,
            GenerationStatus.PROCESSING.value: 50.0,
            GenerationStatus.COMPLETED.value: 100.0,
            GenerationStatus.FAILED.value: 100.0,
            GenerationStatus.CANCELLED.value: 100.0
        }
        return status_progress.get(status, 0.0)
    
    def _get_credit_cost_from_request(self, generation_id: str) -> int:
        """Get credit cost from existing generation request."""
        try:
            request_data = self.generation_repository.get_generation_request(generation_id)
            return request_data.get("credits_deducted", 0) if request_data else 0
        except Exception:
            return 0
    
    def get_generation_request(self, generation_id: str) -> Dict[str, Any]:
        """
        Get generation request by ID.
        """
        try:
            request_data = self.generation_repository.get_generation_request(generation_id)
            
            if not request_data:
                return {
                    "success": False,
                    "message": f"Generation request not found: {generation_id}",
                    "error": "Request does not exist",
                    "error_type": "not_found"
                }
            
            return {
                "success": True,
                "data": request_data,
                "message": "Generation request retrieved successfully"
            }
            
        except Exception as e:
            self.logger.error(
                "Error retrieving generation request %s: %s", generation_id, str(e)
            )
            return {
                "success": False,
                "message": f"Failed to retrieve generation request: {str(e)}",
                "error": str(e),
                "error_type": "system"
            }