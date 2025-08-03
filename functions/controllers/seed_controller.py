"""Controller for seed-related endpoints."""

from firebase_functions import https_fn
from services import SeedService
import logging


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
                return https_fn.Response(
                    result.get("message", "Database seeded successfully"),
                    status=200
                )
            else:
                # Determine appropriate HTTP status code
                error_type = result.get("error_type", "system")
                status_code = 400 if error_type == "validation" else 500
                
                return https_fn.Response(
                    result.get("message", "Seeding failed"),
                    status=status_code
                )
                
        except Exception as e:
            # Catch any unexpected controller-level errors
            self.logger.error("Controller error in seed_database: %s", str(e))
            return https_fn.Response(
                f"Controller error: {str(e)}",
                status=500
            )
            