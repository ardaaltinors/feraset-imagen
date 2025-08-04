"""Repository for style data operations."""

from typing import Set
from .base_repository import BaseRepository
from core.config import Config


class StyleRepository(BaseRepository):
    """Repository for managing style data."""
    
    def __init__(self):
        super().__init__(Config.get_collection_name("styles"))
    
    def get_valid_styles(self) -> Set[str]:
        """Get all valid style names from database."""
        styles = self.list_all()
        return {style["id"] for style in styles}