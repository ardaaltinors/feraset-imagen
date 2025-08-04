"""Repository for size data operations."""

from typing import Set, Dict
from .base_repository import BaseRepository
from core.config import Config


class SizeRepository(BaseRepository):
    """Repository for managing size data."""
    
    def __init__(self):
        super().__init__(Config.get_collection_name("sizes"))
    
    def get_valid_sizes(self) -> Set[str]:
        """Get all valid size names from database."""
        sizes = self.list_all()
        return {size["id"] for size in sizes}
    
    def get_size_credit_costs(self) -> Dict[str, int]:
        """Get mapping of size to credit cost."""
        sizes = self.list_all()
        return {size["id"]: size.get("credit_cost", 0) for size in sizes}