"""Repository for color data operations."""

from typing import Set
from .base_repository import BaseRepository
from core.config import Config


class ColorRepository(BaseRepository):
    """Repository for managing color data."""
    
    def __init__(self):
        super().__init__(Config.get_collection_name("colors"))
    
    def get_valid_colors(self) -> Set[str]:
        """Get all valid color names from database."""
        colors = self.list_all()
        return {color["id"] for color in colors}