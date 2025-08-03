"""Service layer for user-related business logic."""

import logging
from typing import Dict, Any, Optional
from repositories import UserRepository
from schemas import UserCreditsResponse


class UserService:
    """Service for handling user-related business logic."""
    
    def __init__(self):
        """Initialize user service with repository."""
        self.user_repository = UserRepository()
        self.logger = logging.getLogger(__name__)
    
    def get_user_credits(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current credits and transaction history.
        """
        try:
            # Validate input
            if not user_id or not user_id.strip():
                return {
                    "success": False,
                    "message": "User ID is required",
                    "error": "Invalid user_id parameter",
                    "error_type": "validation"
                }
            
            user_id = user_id.strip()
            self.logger.info("Getting credits for user: %s", user_id)
            
            # Get user credits and transactions
            user_credits_data = self.user_repository.get_user_credits_with_transactions(user_id)
            
            if user_credits_data is None:
                self.logger.warning("User not found: %s", user_id)
                return {
                    "success": False,
                    "message": f"User not found: {user_id}",
                    "error": "User does not exist",
                    "error_type": "not_found"
                }
            
            # Convert to dict for JSON response
            response_data = user_credits_data.dict()
            
            self.logger.info(
                "Retrieved credits for user %s: %d credits, %d transactions",
                user_id,
                response_data.get("current_credits", 0),
                len(response_data.get("transactions", []))
            )
            
            return {
                "success": True,
                "data": response_data,
                "message": "User credits retrieved successfully"
            }
            
        except Exception as e:
            self.logger.error("Error getting user credits for %s: %s", user_id, str(e))
            return {
                "success": False,
                "message": f"Failed to retrieve user credits: {str(e)}",
                "error": str(e),
                "error_type": "system"
            }
    
    def validate_user_exists(self, user_id: str) -> Dict[str, Any]:
        """
        Validate that a user exists in the system.
        """
        try:
            if not user_id or not user_id.strip():
                return {
                    "success": False,
                    "message": "User ID is required",
                    "error": "Invalid user_id parameter"
                }
            
            user_data = self.user_repository.get_user_by_id(user_id.strip())
            
            if user_data is None:
                return {
                    "success": False,
                    "message": f"User not found: {user_id}",
                    "exists": False
                }
            
            return {
                "success": True,
                "message": "User exists",
                "exists": True,
                "user_data": {
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "current_credits": user_data.get("current_credits", 0)
                }
            }
            
        except Exception as e:
            self.logger.error("Error validating user %s: %s", user_id, str(e))
            return {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "error": str(e)
            }