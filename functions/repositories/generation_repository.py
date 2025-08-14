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
        Create a new image generation request.
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
        Deduct credits and create generation request using Firestore transaction.
        """
        try:
            generation_id = str(uuid.uuid4())
            transaction_id = str(uuid.uuid4())
            
            # Prepare data outside transaction
            generation_data["id"] = generation_id
            generation_data["created_at"] = datetime.now()
            generation_data["updated_at"] = datetime.now()
            
            transaction_data["id"] = transaction_id
            transaction_data["user_id"] = user_id
            transaction_data["generation_request_id"] = generation_id
            transaction_data["timestamp"] = datetime.now()
            
            @firestore.transactional
            def deduct_credits_transaction(transaction):
                # References
                user_ref = self.db.collection(Config.get_collection_name("users")).document(user_id)
                generation_ref = self.db.collection(
                    Config.get_collection_name("generation_requests")
                ).document(generation_id)
                transaction_ref = user_ref.collection("transactions").document(transaction_id)
                
                # Read user document within transaction
                user_doc = user_ref.get(transaction=transaction)
                if not user_doc.exists:
                    raise ValueError("User not found")
                
                user_data = user_doc.to_dict()
                current_user_credits = user_data.get("current_credits", 0)
                
                if current_user_credits < credit_cost:
                    raise ValueError("Insufficient credits")
                
                # Calculate new credit balance
                new_credits = current_user_credits - credit_cost
                
                # Update user credits
                transaction.update(user_ref, {
                    "current_credits": new_credits,
                    "updated_at": datetime.now()
                })
                
                # Create generation request
                transaction.set(generation_ref, generation_data)
                
                # Create transaction record
                transaction.set(transaction_ref, transaction_data)
                
                return new_credits
            
            # Execute transaction
            transaction = self.db.transaction()
            new_credits = deduct_credits_transaction(transaction)
            
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
        Refund credits and update generation request status using Firestore transaction.
        """
        try:
            refund_transaction_id = str(uuid.uuid4())
            
            # Prepare refund transaction data outside transaction
            refund_transaction_data = {
                "id": refund_transaction_id,
                "type": TransactionType.REFUND.value,
                "credits": credit_amount,
                "generation_request_id": generation_id,
                "timestamp": datetime.now(),
                "user_id": user_id,
                "description": f"Refund for failed generation: {error_message}"
            }
            
            @firestore.transactional
            def refund_credits_transaction(transaction):
                # References
                user_ref = self.db.collection(Config.get_collection_name("users")).document(user_id)
                generation_ref = self.db.collection(
                    Config.get_collection_name("generation_requests")
                ).document(generation_id)
                transaction_ref = user_ref.collection("transactions").document(refund_transaction_id)
                
                # Read user document within transaction
                user_doc = user_ref.get(transaction=transaction)
                if not user_doc.exists:
                    raise ValueError("User not found")
                
                user_data = user_doc.to_dict()
                current_credits = user_data.get("current_credits", 0)
                new_credits = current_credits + credit_amount
                
                # Update user credits
                transaction.update(user_ref, {
                    "current_credits": new_credits,
                    "updated_at": datetime.now()
                })
                
                # Update generation request status
                transaction.update(generation_ref, {
                    "status": "failed",
                    "error_message": error_message,
                    "updated_at": datetime.now(),
                    "completed_at": datetime.now()
                })
                
                # Create refund transaction record
                transaction.set(transaction_ref, refund_transaction_data)
                
                return new_credits
            
            # Execute transaction
            transaction = self.db.transaction()
            new_credits = refund_credits_transaction(transaction)
            
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
        Mark generation request as completed with image URL and increment user's total images counter.
        """
        try:
            # Get the generation request to find the user_id
            generation_data = self.get_generation_request(generation_id)
            if not generation_data:
                return False
            
            user_id = generation_data.get("user_id")
            if not user_id:
                return False
            
            # Update generation request status
            update_data = {
                "status": "completed",
                "image_url": image_url,
                "completed_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Update generation request
            request_updated = self.update_generation_request(generation_id, update_data)
            
            if request_updated:
                # Increment user's total images generated counter
                from .user_repository import UserRepository
                user_repo = UserRepository()
                increment_success = user_repo.increment_total_images_generated(user_id)
                
                if not increment_success:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to increment total_images_generated counter for user {user_id}")
            
            return request_updated
        except Exception:
            return False
    
    def get_user_generation_requests(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get generation requests for a user.
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