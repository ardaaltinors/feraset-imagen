"""Repository for user-related database operations."""

from typing import Dict, List, Optional, Any
from .base_repository import BaseRepository
from schemas import TransactionModel, UserCreditsResponse
from core import Config


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
    def __init__(self):
        """Initialize user repository."""
        super().__init__(Config.get_collection_name("users"))
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            User data or None if not found
        """
        return self.get(user_id)
    
    def get_user_transactions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all transactions for a user.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            List of transaction dictionaries
        """
        transactions_collection = self.db.collection(
            Config.get_collection_name("users")
        ).document(user_id).collection("transactions")
        
        # Order by timestamp descending (newest first)
        docs = transactions_collection.order_by("timestamp", direction="DESCENDING").stream()
        
        transactions = []
        for doc in docs:
            transaction_data = doc.to_dict()
            transaction_data["id"] = doc.id
            transactions.append(transaction_data)
        
        return transactions
    
    def get_user_credits_with_transactions(self, user_id: str) -> Optional[UserCreditsResponse]:
        """
        Get user's current credits along with transaction history.
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            UserCreditsResponse object or None if user not found
        """
        # Get user data
        user_data = self.get_user_by_id(user_id)
        if not user_data:
            return None
        
        # Get transactions
        transactions_data = self.get_user_transactions(user_id)
        
        # Convert to TransactionModel objects for validation
        validated_transactions = []
        for transaction_data in transactions_data:
            try:
                # Ensure user_id is included for validation
                transaction_data["user_id"] = user_id
                transaction_model = TransactionModel(**transaction_data)
                validated_transactions.append(transaction_model)
            except Exception as e:
                # Log invalid transaction but continue
                print(f"Invalid transaction data for user {user_id}: {e}")
                continue
        
        return UserCreditsResponse(
            current_credits=user_data.get("current_credits", 0),
            transactions=validated_transactions
        )
    
    def create_transaction(
        self, 
        user_id: str, 
        transaction_data: Dict[str, Any]
    ) -> bool:
        """
        Create a new transaction for a user.
        
        Args:
            user_id: The user's unique identifier
            transaction_data: Transaction data to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction_id = transaction_data.get("id")
            if not transaction_id:
                return False
            
            transactions_collection = self.db.collection(
                Config.get_collection_name("users")
            ).document(user_id).collection("transactions")
            
            transactions_collection.document(transaction_id).set(transaction_data)
            return True
        except Exception:
            return False
    
    def update_user_credits(self, user_id: str, new_credits: int) -> bool:
        """
        Update user's current credits.
        
        Args:
            user_id: The user's unique identifier
            new_credits: New credit amount
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.update(user_id, {
                "current_credits": new_credits,
                "updated_at": self.db.SERVER_TIMESTAMP
            })
            return True
        except Exception:
            return False