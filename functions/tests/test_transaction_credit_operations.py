"""Unit tests for transaction-based credit operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Import the modules we're testing
from repositories.generation_repository import GenerationRepository
from schemas import TransactionType


class TestTransactionCreditOperations:
    """Test transaction-based credit operations."""
    
    def test_atomic_credit_deduction_with_transaction_success(self, mock_firestore_db, sample_user_data, sample_generation_data, sample_transaction_data):
        """Test successful atomic credit deduction using Firestore transaction."""
        # Setup mock user document
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = sample_user_data
        
        # Setup mock references
        mock_user_ref = Mock()
        mock_generation_ref = Mock()
        mock_transaction_ref = Mock()
        
        # Setup mock transaction
        mock_transaction_obj = Mock()
        
        # Configure mock database
        mock_firestore_db.collection.return_value.document.side_effect = lambda doc_id: (
            mock_user_ref if doc_id == "test_user_123" else mock_generation_ref
        )
        mock_user_ref.collection.return_value.document.return_value = mock_transaction_ref
        mock_user_ref.get.return_value = mock_user_doc
        mock_firestore_db.transaction.return_value = mock_transaction_obj
        
        # Mock the transactional decorator to execute the function directly
        def mock_transactional(func):
            def wrapper(transaction):
                # Execute the actual transaction logic
                return func(transaction)
            return wrapper
        
        with patch('repositories.generation_repository.firestore.transactional', mock_transactional):
            with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
                repo = GenerationRepository()
                repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="test_user_123",
                current_credits=100,
                credit_cost=3,
                generation_data=sample_generation_data.copy(),
                transaction_data=sample_transaction_data.copy()
            )
        
        # Assertions
        assert result["success"] is True
        assert "generation_id" in result
        assert result["new_credits"] == 97
        
        # Verify transaction was created and methods were called
        mock_firestore_db.transaction.assert_called_once()
        mock_transaction_obj.update.assert_called()
        assert mock_transaction_obj.set.call_count == 2  # generation request and transaction record
    
    def test_atomic_credit_deduction_insufficient_credits_transaction(self, mock_firestore_db, sample_user_data, sample_generation_data, sample_transaction_data):
        """Test credit deduction fails with insufficient credits in transaction."""
        # Setup user with insufficient credits
        insufficient_user = sample_user_data.copy()
        insufficient_user["current_credits"] = 2
        
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = insufficient_user
        
        # Setup mock references
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        # Setup mock transaction
        mock_transaction_obj = Mock()
        
        # Configure mock database
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        mock_firestore_db.transaction.return_value = mock_transaction_obj
        
        # Mock transactional to raise ValueError for insufficient credits
        def mock_transactional(func):
            def wrapper(transaction):
                # Simulate reading user doc and finding insufficient credits
                user_doc = mock_user_ref.get(transaction=transaction)
                if user_doc.to_dict()["current_credits"] < 3:
                    raise ValueError("Insufficient credits")
                return func(transaction)
            return wrapper
        
        with patch('repositories.generation_repository.firestore.transactional', mock_transactional):
            with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
                repo = GenerationRepository()
                repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="test_user_123",
                current_credits=2,
                credit_cost=3,
                generation_data=sample_generation_data.copy(),
                transaction_data=sample_transaction_data.copy()
            )
        
        # Assertions
        assert result["success"] is False
        assert result["error"] == "Insufficient credits"
        assert result["error_type"] == "validation"
        
        # Verify transaction was created but no updates were made
        mock_firestore_db.transaction.assert_called_once()
        mock_transaction_obj.update.assert_not_called()
        mock_transaction_obj.set.assert_not_called()
    
    def test_atomic_credit_refund_with_transaction_success(self, mock_firestore_db, sample_user_data):
        """Test successful atomic credit refund using Firestore transaction."""
        # Setup mock user document
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = sample_user_data
        
        # Setup mock references
        mock_user_ref = Mock()
        mock_generation_ref = Mock()
        mock_transaction_ref = Mock()
        
        # Setup mock transaction
        mock_transaction_obj = Mock()
        
        # Configure mock database
        def mock_document(doc_id):
            if doc_id == "test_user_123":
                return mock_user_ref
            else:
                return mock_generation_ref
        
        mock_firestore_db.collection.return_value.document.side_effect = mock_document
        mock_user_ref.collection.return_value.document.return_value = mock_transaction_ref
        mock_user_ref.get.return_value = mock_user_doc
        mock_firestore_db.transaction.return_value = mock_transaction_obj
        
        # Mock the transactional decorator
        def mock_transactional(func):
            def wrapper(transaction):
                return func(transaction)
            return wrapper
        
        with patch('repositories.generation_repository.firestore.transactional', mock_transactional):
            with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
                repo = GenerationRepository()
                repo._db = mock_firestore_db
            
            result = repo.atomic_credit_refund(
                user_id="test_user_123",
                generation_id="test_generation_456",
                credit_amount=3,
                error_message="Generation failed due to model error"
            )
        
        # Assertions
        assert result["success"] is True
        assert result["refunded_credits"] == 3
        assert result["new_credits"] == 103  # 100 + 3
        
        # Verify transaction was created and methods were called
        mock_firestore_db.transaction.assert_called_once()
        assert mock_transaction_obj.update.call_count == 2  # user credits and generation status
        mock_transaction_obj.set.assert_called_once()  # refund transaction record
    
    def test_transaction_rollback_on_error(self, mock_firestore_db, sample_user_data, sample_generation_data, sample_transaction_data):
        """Test that transaction rolls back on error."""
        # Setup mock user document
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = sample_user_data
        
        # Setup mock references
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_user_doc
        
        # Setup mock transaction that fails
        mock_transaction_obj = Mock()
        mock_transaction_obj.update.side_effect = Exception("Database connection error")
        
        # Configure mock database
        mock_firestore_db.collection.return_value.document.return_value = mock_user_ref
        mock_firestore_db.transaction.return_value = mock_transaction_obj
        
        # Mock transactional to simulate transaction execution
        def mock_transactional(func):
            def wrapper(transaction):
                try:
                    return func(transaction)
                except Exception as e:
                    raise e
            return wrapper
        
        with patch('repositories.generation_repository.firestore.transactional', mock_transactional):
            with patch('repositories.generation_repository.firestore.client', return_value=mock_firestore_db):
                repo = GenerationRepository()
                repo._db = mock_firestore_db
            
            result = repo.atomic_credit_deduction_and_request_creation(
                user_id="test_user_123",
                current_credits=100,
                credit_cost=3,
                generation_data=sample_generation_data.copy(),
                transaction_data=sample_transaction_data.copy()
            )
        
        # Assertions
        assert result["success"] is False
        assert "Database connection error" in result["error"]
        assert result["error_type"] == "system"
        
        # Verify transaction was attempted
        mock_firestore_db.transaction.assert_called_once()