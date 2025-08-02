"""Service layer for generation request business logic."""

import logging
from typing import Dict, Any
from repositories import GenerationRepository, UserRepository
from services.ai_model_service import AIModelService
from schemas import (
    CreateGenerationRequestModel, 
    GenerationRequestModel,
    CreateGenerationResponseModel,
    TransactionType,
    GenerationStatus,
    AIModel
)


class GenerationService:
    """Service for handling generation request business logic."""
    
    def __init__(self):
        """Initialize generation service with repositories and AI service."""
        self.generation_repository = GenerationRepository()
        self.user_repository = UserRepository()
        self.ai_model_service = AIModelService(failure_rate=0.05)  # 5% failure rate
        self.logger = logging.getLogger(__name__)
    
    def create_generation_request(
        self, 
        request_data: CreateGenerationRequestModel
    ) -> Dict[str, Any]:
        """
        Process a new generation request with credit deduction and AI generation.
        
        Args:
            request_data: Validated generation request data
            
        Returns:
            Dict containing success status, generation ID, and image URL
        """
        try:
            self.logger.info(
                "Processing generation request for user %s with model %s",
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
            credit_deduction_result = self._deduct_credits_and_create_request(
                request_data, credit_cost, user_data
            )
            if not credit_deduction_result["success"]:
                return credit_deduction_result
            
            generation_id = credit_deduction_result["generation_id"]
            
            # Step 4: Attempt AI generation
            generation_result = self.ai_model_service.generate_image(
                model=request_data.model,
                style=request_data.style,
                color=request_data.color,
                size=request_data.size,
                prompt=request_data.prompt,
                generation_request_id=generation_id
            )
            
            # Step 5: Handle generation result
            if generation_result["success"]:
                # Success: Update generation request with image URL
                image_url = generation_result["image_url"]
                self.generation_repository.complete_generation_request(
                    generation_id, image_url
                )
                
                self.logger.info(
                    "Generation successful for request %s: %s",
                    generation_id, image_url
                )
                
                return {
                    "success": True,
                    "data": {
                        "generationRequestId": generation_id,
                        "deductedCredits": credit_cost,
                        "imageUrl": image_url
                    },
                    "message": "Image generated successfully"
                }
            else:
                # Failure: Refund credits and update status
                error_message = generation_result.get("error", "Generation failed")
                refund_result = self.generation_repository.atomic_credit_refund(
                    user_id=request_data.userId,
                    generation_id=generation_id,
                    credit_amount=credit_cost,
                    error_message=error_message
                )
                
                if refund_result["success"]:
                    self.logger.warning(
                        "Generation failed for request %s, credits refunded: %s",
                        generation_id, error_message
                    )
                    
                    return {
                        "success": False,
                        "message": f"Generation failed: {error_message}. Credits have been refunded.",
                        "error": error_message,
                        "error_type": "generation_failure",
                        "refunded": True,
                        "generation_request_id": generation_id
                    }
                else:
                    # Critical error: generation failed AND refund failed
                    self.logger.error(
                        "CRITICAL: Generation failed AND refund failed for request %s",
                        generation_id
                    )
                    
                    return {
                        "success": False,
                        "message": "Generation failed and refund failed. Please contact support.",
                        "error": f"Generation error: {error_message}. Refund error: {refund_result.get('error')}",
                        "error_type": "critical_system_error",
                        "generation_request_id": generation_id
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
        
        Args:
            request_data: Generation request data
            
        Returns:
            Dict with validation results
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
    
    def _deduct_credits_and_create_request(
        self,
        request_data: CreateGenerationRequestModel,
        credit_cost: int,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atomically deduct credits and create generation request.
        
        Args:
            request_data: Generation request data
            credit_cost: Credits to deduct
            user_data: Current user data
            
        Returns:
            Dict with operation results
        """
        # Prepare generation request data
        generation_data = {
            "user_id": request_data.userId,
            "model": request_data.model.value,
            "style": request_data.style,
            "color": request_data.color,
            "size": request_data.size,
            "prompt": request_data.prompt,
            "status": GenerationStatus.PROCESSING.value,
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
                "Credits deducted and generation request created: %s (Cost: %d)",
                result["generation_id"], credit_cost
            )
        else:
            self.logger.error(
                "Failed to deduct credits for user %s: %s",
                request_data.userId, result.get("error")
            )
        
        return result
    
    def get_generation_request(self, generation_id: str) -> Dict[str, Any]:
        """
        Get generation request by ID.
        
        Args:
            generation_id: Generation request ID
            
        Returns:
            Dict with generation request data or error
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