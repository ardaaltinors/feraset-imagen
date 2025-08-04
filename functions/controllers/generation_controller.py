"""Controller for generation-related endpoints."""

from firebase_functions import https_fn
from services import GenerationService
from schemas import CreateGenerationRequestModel
import logging
import json
from datetime import datetime


class GenerationController:
    """Controller for handling generation-related HTTP requests."""
    
    def __init__(self):
        """Initialize generation controller with service."""
        self.generation_service = GenerationService()
        self.logger = logging.getLogger(__name__)
    
    def create_generation_request(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to create a new image generation request.
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
                # Success response - now async with queue information
                response_data = result["data"]
                return https_fn.Response(
                    json.dumps({
                        "generationRequestId": response_data["generationRequestId"],
                        "status": response_data["status"],
                        "deductedCredits": response_data["deductedCredits"],
                        "queuePosition": response_data.get("queuePosition")
                    }, default=str),
                    status=202,  # Accepted - request queued for processing
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
                elif error_type == "queue_failure":
                    status_code = 503  # Service Unavailable (temporary)
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
    
    def get_generation_status(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to get generation request status.
        """
        try:
            self.logger.info(
                "Get generation status from %s",
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
            result = self.generation_service.get_generation_status(generation_id)
            
            if result.get("success"):
                return https_fn.Response(
                    json.dumps(result["data"], default=str),
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                error_type = result.get("error_type", "system")
                status_code = 404 if error_type == "not_found" else 500
                
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": result.get("message", "Failed to get generation status"),
                        "error": result.get("error")
                    }),
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Controller error in get_generation_status: %s", str(e))
            return https_fn.Response(
                json.dumps({
                    "success": False,
                    "message": f"Controller error: {str(e)}",
                    "error": str(e)
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    def process_background_generation(self, req: https_fn.Request) -> https_fn.Response:
        """
        Background worker endpoint for processing generation tasks from Cloud Tasks.
        
        This endpoint is called by Cloud Tasks to process queued generation requests.
        
        Args:
            req: HTTP request object containing task payload
            
        Returns:
            https_fn.Response: JSON response with processing results
        """
        try:
            # Validate that this is a POST request
            if req.method != "POST":
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "error": "Only POST method allowed for task processing"
                    }),
                    status=405,
                    headers={"Content-Type": "application/json"}
                )
            
            # Parse task payload
            try:
                task_payload = req.get_json(silent=True)
                if not task_payload:
                    raise ValueError("Empty or invalid JSON payload")
            except Exception as e:
                self.logger.error(f"Invalid task payload: {str(e)}")
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "error": f"Invalid JSON in task payload: {str(e)}"
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            generation_id = task_payload.get("generation_request_id")
            self.logger.info(f"Processing background generation task: {generation_id}")
            
            # Process the generation task
            result = self.generation_service.process_generation_task(task_payload)
            
            # Return appropriate status for Cloud Tasks
            # 200 = success, 500 = retry, 400 = permanent failure
            if result.get("success"):
                status_code = 200
            elif result.get("error_type") == "validation":
                status_code = 400  # Don't retry validation errors
            else:
                status_code = 500  # Retry other errors
            
            response_data = {
                "success": result.get("success", False),
                "generation_id": result.get("generation_id"),
                "message": result.get("message", "Task processed"),
                "processed_at": datetime.now().isoformat()
            }
            
            if not result.get("success"):
                response_data["error"] = result.get("error")
                response_data["error_type"] = result.get("error_type", "processing_error")
            else:
                response_data["image_url"] = result.get("image_url")
            
            return https_fn.Response(
                response=json.dumps(response_data, default=str),
                status=status_code,
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            self.logger.error(f"Background generation controller error: {str(e)}")
            # Return 500 to trigger Cloud Tasks retry
            return https_fn.Response(
                response=json.dumps({
                    "success": False,
                    "error": f"Controller error: {str(e)}",
                    "error_type": "controller_error",
                    "processed_at": datetime.now().isoformat()
                }, default=str),
                status=500,
                headers={"Content-Type": "application/json"}
            )