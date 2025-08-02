"""Controller for generation-related endpoints."""

from firebase_functions import https_fn
from services import GenerationService
from schemas import CreateGenerationRequestModel
import logging
import json


class GenerationController:
    """Controller for handling generation-related HTTP requests."""
    
    def __init__(self):
        """Initialize generation controller with service."""
        self.generation_service = GenerationService()
        self.logger = logging.getLogger(__name__)
    
    def create_generation_request(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to create a new image generation request.
        
        Expected JSON payload:
        {
            "userId": "string",
            "model": "Model A" | "Model B",
            "style": "realistic" | "anime" | "oil painting" | "sketch" | "cyberpunk" | "watercolor",
            "color": "vibrant" | "monochrome" | "pastel" | "neon" | "vintage",
            "size": "512x512" | "1024x1024" | "1024x1792",
            "prompt": "string"
        }
        
        Args:
            req: Firebase Functions HTTP request object
            
        Returns:
            https_fn.Response: Generation result or error details
        """
        try:
            # Log request info
            self.logger.info(
                "Create generation request from %s", 
                req.headers.get('X-Forwarded-For', 'unknown')
            )
            
            # Validate request method
            if req.method != "POST":
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "Only POST method is allowed",
                        "error": "Method not allowed"
                    }),
                    status=405,
                    headers={"Content-Type": "application/json"}
                )
            
            # Parse request body
            try:
                if not req.content_type or 'application/json' not in req.content_type:
                    return https_fn.Response(
                        json.dumps({
                            "success": False,
                            "message": "Content-Type must be application/json",
                            "error": "Invalid content type"
                        }),
                        status=400,
                        headers={"Content-Type": "application/json"}
                    )
                
                request_data = req.get_json(silent=True)
                if not request_data:
                    return https_fn.Response(
                        json.dumps({
                            "success": False,
                            "message": "Invalid JSON in request body",
                            "error": "JSON parsing failed"
                        }),
                        status=400,
                        headers={"Content-Type": "application/json"}
                    )
                    
            except Exception as e:
                self.logger.warning("Failed to parse JSON body: %s", str(e))
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "Failed to parse request body",
                        "error": str(e)
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Validate request data with Pydantic
            try:
                validated_request = CreateGenerationRequestModel(**request_data)
            except Exception as e:
                self.logger.warning("Request validation failed: %s", str(e))
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "Request validation failed",
                        "error": str(e),
                        "error_type": "validation"
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Log validated request details
            self.logger.info(
                "Processing generation request - User: %s, Model: %s, Size: %s",
                validated_request.userId, 
                validated_request.model.value,
                validated_request.size
            )
            
            # Call service layer
            result = self.generation_service.create_generation_request(validated_request)
            
            if result.get("success"):
                # Success response
                response_data = result["data"]
                return https_fn.Response(
                    json.dumps({
                        "generationRequestId": response_data["generationRequestId"],
                        "deductedCredits": response_data["deductedCredits"],
                        "imageUrl": response_data["imageUrl"]
                    }),
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                # Error response with appropriate status code
                error_type = result.get("error_type", "system")
                
                if error_type == "validation":
                    status_code = 400
                elif error_type == "not_found":
                    status_code = 404
                elif error_type == "insufficient_credits":
                    status_code = 402  # Payment Required
                elif error_type == "generation_failure":
                    status_code = 503  # Service Unavailable (temporary)
                elif error_type == "critical_system_error":
                    status_code = 500
                else:
                    status_code = 500
                
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": result.get("message", "Generation failed"),
                        "error": result.get("error"),
                        "error_type": error_type,
                        "refunded": result.get("refunded", False),
                        "generation_request_id": result.get("generation_request_id")
                    }),
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            # Catch any unexpected controller-level errors
            self.logger.error("Controller error in create_generation_request: %s", str(e))
            return https_fn.Response(
                json.dumps({
                    "success": False,
                    "message": f"Controller error: {str(e)}",
                    "error": str(e),
                    "error_type": "system"
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    def get_generation_request(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to get generation request details.
        
        Args:
            req: Firebase Functions HTTP request object
            
        Returns:
            https_fn.Response: Generation request details or error
        """
        try:
            self.logger.info(
                "Get generation request from %s",
                req.headers.get('X-Forwarded-For', 'unknown')
            )
            
            # Extract generation request ID
            generation_id = None
            
            if req.method == "GET":
                generation_id = req.args.get('generationRequestId')
            elif req.method == "POST":
                try:
                    if req.content_type and 'application/json' in req.content_type:
                        request_data = req.get_json(silent=True)
                        if request_data:
                            generation_id = request_data.get('generationRequestId')
                except Exception as e:
                    self.logger.warning("Failed to parse JSON body: %s", str(e))
            
            if not generation_id:
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "generationRequestId parameter is required",
                        "error": "Missing generationRequestId"
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Call service layer
            result = self.generation_service.get_generation_request(generation_id)
            
            if result.get("success"):
                return https_fn.Response(
                    json.dumps({
                        "success": True,
                        "data": result["data"]
                    }),
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                error_type = result.get("error_type", "system")
                status_code = 404 if error_type == "not_found" else 500
                
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": result.get("message", "Failed to get generation request"),
                        "error": result.get("error")
                    }),
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Controller error in get_generation_request: %s", str(e))
            return https_fn.Response(
                json.dumps({
                    "success": False,
                    "message": f"Controller error: {str(e)}",
                    "error": str(e)
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )