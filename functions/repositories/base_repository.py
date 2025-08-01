"""Base repository class for database operations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from firebase_admin import firestore
from pydantic import BaseModel


class BaseRepository(ABC):
    """Base repository for common database operations."""
    
    def __init__(self, collection_name: str):
        """Initialize repository with collection name."""
        self.collection_name = collection_name
        self._db = None
    
    @property
    def db(self) -> firestore.firestore.Client:
        """Get Firestore client instance."""
        if self._db is None:
            self._db = firestore.client()
        return self._db
    
    @property
    def collection(self) -> firestore.firestore.CollectionReference:
        """Get collection reference."""
        return self.db.collection(self.collection_name)
    
    def create(self, document_id: str, data: Dict[str, Any]) -> None:
        """Create a new document."""
        self.collection.document(document_id).set(data)
    
    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        doc = self.collection.document(document_id).get()
        return doc.to_dict() if doc.exists else None
    
    def update(self, document_id: str, data: Dict[str, Any]) -> None:
        """Update a document."""
        self.collection.document(document_id).update(data)
    
    def delete(self, document_id: str) -> None:
        """Delete a document."""
        self.collection.document(document_id).delete()
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all documents in collection."""
        docs = self.collection.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    def batch_create(self, items: List[Tuple[str, Dict[str, Any]]]) -> None:
        """Create multiple documents in a batch."""
        batch = self.db.batch()
        for doc_id, data in items:
            doc_ref = self.collection.document(doc_id)
            batch.set(doc_ref, data)
        batch.commit()
    
    def query_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Query documents by field value."""
        docs = self.collection.where(field, "==", value).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]