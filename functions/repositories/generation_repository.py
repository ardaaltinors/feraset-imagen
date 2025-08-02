"""Repository for generation request database operations."""

from typing import Dict, List, Optional, Any
from firebase_admin import firestore
from .base_repository import BaseRepository
from schemas import TransactionType
from core import Config
import uuid
from datetime import datetime


class GenerationRepository(BaseRepository):
    """Repository for generation request operations."""
    
    def __init__(self):
        """Initialize generation repository."""
        super().__init__(Config.get_collection_name("generation_requests"))
    
    def create_generation_request(
        self, 
        generation_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new generation request.
        
        Args:
            generation_data: Generation request data
            
        Returns:
            Generation request ID if successful, None otherwise
        """
        try:
            generation_id = str(uuid.uuid4())
            generation_data["id"] = generation_id
            generation_data["created_at"] = datetime.now()
            generation_data["updated_at"] = datetime.now()
            
            self.create(generation_id, generation_data)
            return generation_id
        except Exception:
            return None
    
    def update_generation_request(
        self, 
        generation_id: str, 
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a generation request.
        
        Args:
            generation_id: Generation request ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data["updated_at"] = datetime.now()
            self.update(generation_id, update_data)
            return True
        except Exception:
            return False
    
    def get_generation_request(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get generation request by ID.
        
        Args:
            generation_id: Generation request ID
            
        Returns:
            Generation request data or None if not found
        """
        return self.get(generation_id)
    
    def atomic_credit_deduction_and_request_creation(
        self,
        user_id: str,
        current_credits: int,
        credit_cost: int,
        generation_data: Dict[str, Any],
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atomically deduct credits and create generation request.
        
        Args:
            user_id: User ID
            current_credits: Current user credits
            credit_cost: Credits to deduct
            generation_data: Generation request data
            transaction_data: Transaction data
            
        Returns:
            Dict with success status and generation request ID
        """
        try:
            generation_id = str(uuid.uuid4())
            transaction_id = str(uuid.uuid4())
            
            # References
            user_ref = self.db.collection(Config.get_collection_name("users")).document(user_id)
            generation_ref = self.db.collection(
                Config.get_collection_name("generation_requests")
            ).document(generation_id)
            transaction_ref = user_ref.collection("transactions").document(transaction_id)
            
            # Use Firestore batch for atomic operations
            batch = self.db.batch()
            
            # First verify user exists and has sufficient credits
            user_doc = user_ref.get()
            if not user_doc.exists:
                raise ValueError("User not found")
            
            user_data = user_doc.to_dict()
            current_user_credits = user_data.get("current_credits", 0)
            
            if current_user_credits < credit_cost:
                raise ValueError("Insufficient credits")
            
            # Calculate new credit balance
            new_credits = current_user_credits - credit_cost
            
            # Prepare data
            generation_data["id"] = generation_id
            generation_data["created_at"] = datetime.now()
            generation_data["updated_at"] = datetime.now()
            
            transaction_data["id"] = transaction_id
            transaction_data["user_id"] = user_id
            transaction_data["generation_request_id"] = generation_id
            transaction_data["timestamp"] = datetime.now()
            
            # Update user credits
            batch.update(user_ref, {
                "current_credits": new_credits,
                "updated_at": datetime.now()
            })
            
            # Create generation request
            batch.set(generation_ref, generation_data)
            
            # Create transaction record
            batch.set(transaction_ref, transaction_data)
            
            # Commit all operations atomically
            batch.commit()
            
            return {
                "success": True,
                "generation_id": generation_id,
                "new_credits": new_credits
            }
            
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Transaction failed: {str(e)}",
                "error_type": "system"
            }
    
    def atomic_credit_refund(
        self,
        user_id: str,
        generation_id: str,
        credit_amount: int,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Atomically refund credits and update generation request status.
        
        Args:
            user_id: User ID
            generation_id: Generation request ID
            credit_amount: Credits to refund
            error_message: Error message for the generation failure
            
        Returns:
            Dict with success status
        """
        try:
            refund_transaction_id = str(uuid.uuid4())
            
            # References
            user_ref = self.db.collection(Config.get_collection_name("users")).document(user_id)
            generation_ref = self.db.collection(
                Config.get_collection_name("generation_requests")
            ).document(generation_id)
            transaction_ref = user_ref.collection("transactions").document(refund_transaction_id)
            
            # Use Firestore batch for atomic operations
            batch = self.db.batch()
            
            # Get current user credits
            user_doc = user_ref.get()
            if not user_doc.exists:
                raise ValueError("User not found")
            
            user_data = user_doc.to_dict()
            current_credits = user_data.get("current_credits", 0)
            new_credits = current_credits + credit_amount
            
            # Prepare refund transaction
            refund_transaction_data = {
                "id": refund_transaction_id,
                "type": TransactionType.REFUND.value,
                "credits": credit_amount,
                "generation_request_id": generation_id,
                "timestamp": datetime.now(),
                "user_id": user_id,
                "description": f"Refund for failed generation: {error_message}"
            }
            
            # Update user credits
            batch.update(user_ref, {
                "current_credits": new_credits,
                "updated_at": datetime.now()
            })
            
            # Update generation request status
            batch.update(generation_ref, {
                "status": "failed",
                "error_message": error_message,
                "updated_at": datetime.now(),
                "completed_at": datetime.now()
            })
            
            # Create refund transaction record
            batch.set(transaction_ref, refund_transaction_data)
            
            # Commit all operations atomically
            batch.commit()
            
            return {
                "success": True,
                "refunded_credits": credit_amount,
                "new_credits": new_credits
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Refund transaction failed: {str(e)}",
                "error_type": "system"
            }
    
    def complete_generation_request(
        self,
        generation_id: str,
        image_url: str
    ) -> bool:
        """
        Mark generation request as completed with image URL.
        
        Args:
            generation_id: Generation request ID
            image_url: Generated image URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "status": "completed",
                "image_url": image_url,
                "completed_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return self.update_generation_request(generation_id, update_data)
        except Exception:
            return False
    
    def get_user_generation_requests(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get generation requests for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of requests to return
            
        Returns:
            List of generation request dictionaries
        """
        try:
            docs = (
                self.collection
                .where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            
            requests = []
            for doc in docs:
                request_data = doc.to_dict()
                request_data["id"] = doc.id
                requests.append(request_data)
            
            return requests
        except Exception:
            return []