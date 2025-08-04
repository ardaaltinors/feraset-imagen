"""Controller for user-related endpoints."""

from firebase_functions import https_fn
from services import UserService
from utils import convert_firestore_datetime
import logging
import json


class UserController:
    """Controller for handling user-related HTTP requests."""
    
    def __init__(self):
        """Initialize user controller with service."""
        self.user_service = UserService()
        self.logger = logging.getLogger(__name__)
    
    def get_user_credits(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to get user's current credits and transaction history.
        """
        try:
            # Log request info
            self.logger.info(
                "Get user credits request from %s", 
                req.headers.get('X-Forwarded-For', 'unknown')
            )
            
            # Extract user_id from request
            user_id = None
            
            # Try to get user_id from query parameters (GET request)
            if req.method == "GET":
                user_id = req.args.get('userId')
            
            # Try to get user_id from request body (POST request)
            elif req.method == "POST":
                try:
                    if req.content_type and 'application/json' in req.content_type:
                        request_data = req.get_json(silent=True)
                        if request_data:
                            user_id = request_data.get('userId')
                except Exception as e:
                    self.logger.warning("Failed to parse JSON body: %s", str(e))
            
            if not user_id:
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "userId parameter is required",
                        "error": "Missing userId in query parameters or request body"
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Call service layer
            result = self.user_service.get_user_credits(user_id)
            
            if result.get("success"):
                return https_fn.Response(
                    json.dumps({
                        "success": True,
                        "currentCredits": result["data"]["current_credits"],
                        "transactions": convert_firestore_datetime(result["data"]["transactions"])
                    }),
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                # Determine appropriate HTTP status code
                error_type = result.get("error_type", "system")
                if error_type == "validation":
                    status_code = 400
                elif error_type == "not_found":
                    status_code = 404
                else:
                    status_code = 500
                
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": result.get("message", "Failed to get user credits"),
                        "error": result.get("error")
                    }),
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            # Catch any unexpected controller-level errors
            self.logger.error("Controller error in get_user_credits: %s", str(e))
            return https_fn.Response(
                json.dumps({
                    "success": False,
                    "message": f"Controller error: {str(e)}",
                    "error": str(e)
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    def validate_user(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to validate if a user exists.
        """
        try:
            self.logger.info(
                "Validate user request from %s",
                req.headers.get('X-Forwarded-For', 'unknown')
            )
            
            # Extract user_id from request
            user_id = None
            
            if req.method == "GET":
                user_id = req.args.get('userId')
            elif req.method == "POST":
                try:
                    if req.content_type and 'application/json' in req.content_type:
                        request_data = req.get_json(silent=True)
                        if request_data:
                            user_id = request_data.get('userId')
                except Exception as e:
                    self.logger.warning("Failed to parse JSON body: %s", str(e))
            
            if not user_id:
                return https_fn.Response(
                    json.dumps({
                        "success": False,
                        "message": "userId parameter is required"
                    }),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Call service layer
            result = self.user_service.validate_user_exists(user_id)
            
            return https_fn.Response(
                json.dumps(result),
                status=200 if result.get("success") else 404,
                headers={"Content-Type": "application/json"}
            )
                
        except Exception as e:
            self.logger.error("Controller error in validate_user: %s", str(e))
            return https_fn.Response(
                json.dumps({
                    "success": False,
                    "message": f"Controller error: {str(e)}"
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )