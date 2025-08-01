"""Service layer for database seeding operations."""

import logging
from typing import Dict, Any
from repositories import SeedRepository


class SeedService:
    """Service for handling database seeding business logic."""
    
    def __init__(self):
        """Initialize seed service with repository."""
        self.seed_repository = SeedRepository()
        self.logger = logging.getLogger(__name__)
    
    def seed_database(self) -> Dict[str, Any]:
        """
        Seed the database with initial configuration data and test users.
        
        Returns:
            Dict containing success status, counts, or error details
        """
        try:
            self.logger.info("Starting database seeding process")
            
            # Perform seeding operation
            result = self.seed_repository.seed_all_collections()
            
            if result.get("success"):
                counts = result.get("counts", {})
                self.logger.info(
                    "Database seeded successfully with validated data: "
                    "%d styles, %d colors, %d sizes, %d users",
                    counts.get("styles", 0),
                    counts.get("colors", 0), 
                    counts.get("sizes", 0),
                    counts.get("users", 0)
                )
                
                return {
                    "success": True,
                    "message": (
                        f"Database seeded successfully with validated data! "
                        f"Added {counts.get('styles', 0)} styles, "
                        f"{counts.get('colors', 0)} colors, "
                        f"{counts.get('sizes', 0)} sizes, and "
                        f"{counts.get('users', 0)} test users."
                    ),
                    "counts": counts
                }
            else:
                error_msg = result.get("error", "Unknown error occurred")
                self.logger.error("Failed to seed database: %s", error_msg)
                return {
                    "success": False,
                    "message": f"Database error: {error_msg}",
                    "error": error_msg
                }
                
        except ValueError as e:
            # Pydantic validation errors
            error_msg = f"Data validation error: {str(e)}"
            self.logger.error("Data validation failed: %s", str(e))
            return {
                "success": False,
                "message": error_msg,
                "error": str(e),
                "error_type": "validation"
            }
        except Exception as e:
            # Other unexpected errors
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error("Unexpected error during seeding: %s", str(e))
            return {
                "success": False,
                "message": error_msg,
                "error": str(e),
                "error_type": "system"
            }
    
    def validate_seed_data(self) -> Dict[str, Any]:
        """
        Validate seed data without actually inserting to database.
        
        Returns:
            Dict containing validation results
        """
        try:
            self.logger.info("Validating seed data")
            
            # Get validated data (this will raise exceptions if invalid)
            styles = self.seed_repository.get_validated_styles()
            colors = self.seed_repository.get_validated_colors()
            sizes = self.seed_repository.get_validated_sizes()
            users = self.seed_repository.get_validated_users()
            
            return {
                "success": True,
                "message": "All seed data validation passed",
                "counts": {
                    "styles": len(styles),
                    "colors": len(colors),
                    "sizes": len(sizes),
                    "users": len(users)
                }
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": f"Validation failed: {str(e)}",
                "error": str(e),
                "error_type": "validation"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "error": str(e),
                "error_type": "system"
            }