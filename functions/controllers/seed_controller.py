"""Controller for seed-related endpoints."""

from firebase_functions import https_fn
from services import SeedService
from schemas import ApiResponse, ErrorResponse
import logging
import json


class SeedController:
    """Controller for handling seed-related HTTP requests."""
    
    def __init__(self):
        """Initialize seed controller with service."""
        self.seed_service = SeedService()
        self.logger = logging.getLogger(__name__)
    
    def seed_database(self, req: https_fn.Request) -> https_fn.Response:
        """
        HTTP endpoint to seed the database with initial data.
        """
        try:
            # Log request info
            self.logger.info(
                "Seed database request from %s", 
                req.headers.get('X-Forwarded-For', 'unknown')
            )
            
            # Call service layer
            result = self.seed_service.seed_database()
            
            if result.get("success"):
                env = ApiResponse(success=True, data=result, message=result.get("message"))
                return https_fn.Response(
                    env.model_dump_json(),
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
            else:
                # Determine appropriate HTTP status code
                error_type = result.get("error_type", "system")
                status_code = 400 if error_type == "validation" else 500
                
                err = ErrorResponse(message=result.get("message", "Seeding failed"), error=result.get("error"), error_type=error_type)
                return https_fn.Response(
                    err.model_dump_json(),
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            # Catch any unexpected controller-level errors
            self.logger.error("Controller error in seed_database: %s", str(e))
            err = ErrorResponse(message=f"Controller error: {str(e)}", error=str(e), error_type="system")
            return https_fn.Response(
                err.model_dump_json(),
                status=500,
                headers={"Content-Type": "application/json"}
            )
            