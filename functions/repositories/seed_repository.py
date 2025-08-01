"""Repository for seeding database with initial data."""

from datetime import datetime
from typing import List, Tuple
from .base_repository import BaseRepository
from schemas import StyleModel, ColorModel, SizeModel, UserModel
from core import Config


class SeedRepository(BaseRepository):
    """Repository for database seeding operations."""
    
    def __init__(self):
        """Initialize seed repository."""
        super().__init__("seed")  # Not used, but required by base class
    
    def get_validated_styles(self) -> List[Tuple[str, StyleModel]]:
        """Get predefined image styles with validation."""
        styles_data = [
            ("realistic", {
                "display_name": "Realistic",
                "description": "Photorealistic images with natural lighting",
                "sort_order": 1
            }),
            ("anime", {
                "display_name": "Anime", 
                "description": "Japanese animation style artwork",
                "sort_order": 2
            }),
            ("oil_painting", {
                "display_name": "Oil Painting",
                "description": "Traditional oil painting technique", 
                "sort_order": 3
            }),
            ("sketch", {
                "display_name": "Sketch",
                "description": "Hand-drawn pencil sketch style",
                "sort_order": 4
            }),
            ("cyberpunk", {
                "display_name": "Cyberpunk",
                "description": "Futuristic neon-lit cyberpunk aesthetic",
                "sort_order": 5
            }),
            ("watercolor", {
                "display_name": "Watercolor",
                "description": "Soft watercolor painting technique",
                "sort_order": 6
            })
        ]
        
        return [(style_id, StyleModel(**data)) for style_id, data in styles_data]
    
    def get_validated_colors(self) -> List[Tuple[str, ColorModel]]:
        """Get predefined color palettes with validation."""
        colors_data = [
            ("vibrant", {
                "display_name": "Vibrant",
                "description": "Bold and saturated colors",
                "hex_examples": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
                "sort_order": 1
            }),
            ("monochrome", {
                "display_name": "Monochrome",
                "description": "Black and white tones", 
                "hex_examples": ["#000000", "#808080", "#FFFFFF"],
                "sort_order": 2
            }),
            ("pastel", {
                "display_name": "Pastel",
                "description": "Soft and muted colors",
                "hex_examples": ["#FFB3BA", "#BAFFC9", "#BAE1FF"],
                "sort_order": 3
            }),
            ("neon", {
                "display_name": "Neon", 
                "description": "Electric glowing colors",
                "hex_examples": ["#39FF14", "#FF073A", "#00FFFF"],
                "sort_order": 4
            }),
            ("vintage", {
                "display_name": "Vintage",
                "description": "Warm retro color palette",
                "hex_examples": ["#D2B48C", "#CD853F", "#8B4513"],
                "sort_order": 5
            })
        ]
        
        return [(color_id, ColorModel(**data)) for color_id, data in colors_data]
    
    def get_validated_sizes(self) -> List[Tuple[str, SizeModel]]:
        """Get predefined image sizes with validation."""
        sizes_data = [
            ("512x512", {
                "width": 512,
                "height": 512,
                "aspect_ratio": "1:1",
                "display_name": "Square (512×512)",
                "description": "Perfect for avatars and social media",
                "credit_cost": 1,
                "sort_order": 1
            }),
            ("1024x1024", {
                "width": 1024,
                "height": 1024,
                "aspect_ratio": "1:1", 
                "display_name": "Large Square (1024×1024)",
                "description": "High resolution square images",
                "credit_cost": 3,
                "sort_order": 2
            }),
            ("1024x1792", {
                "width": 1024,
                "height": 1792,
                "aspect_ratio": "9:16",
                "display_name": "Portrait (1024×1792)",
                "description": "Vertical format for portraits",
                "credit_cost": 4,
                "sort_order": 3
            })
        ]
        
        return [(size_id, SizeModel(**data)) for size_id, data in sizes_data]
    
    def get_validated_users(self) -> List[Tuple[str, UserModel]]:
        """Get test user data with validation."""
        current_time = datetime.now()
        users_data = [
            ("arda", {
                "name": "Arda",
                "email": "arda@altinors.com", 
                "current_credits": 20,
                "total_credits": 20,
                "total_images_generated": 0,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": current_time
            }),
            ("havanur", {
                "name": "Havanur",
                "email": "havanur@example.com",
                "current_credits": 10,
                "total_credits": 10,
                "total_images_generated": 0,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": current_time
            })
        ]
        
        return [(user_id, UserModel(**data)) for user_id, data in users_data]
    
    def seed_all_collections(self) -> dict:
        """Seed all collections with validated data."""
        try:
            batch = self.db.batch()
            
            # Seed styles collection
            validated_styles = self.get_validated_styles()
            styles_collection = self.db.collection(Config.get_collection_name("styles"))
            for style_id, style_model in validated_styles:
                doc_ref = styles_collection.document(style_id)
                batch.set(doc_ref, style_model.dict())
            
            # Seed colors collection
            validated_colors = self.get_validated_colors()
            colors_collection = self.db.collection(Config.get_collection_name("colors"))
            for color_id, color_model in validated_colors:
                doc_ref = colors_collection.document(color_id)
                batch.set(doc_ref, color_model.dict())
                
            # Seed sizes collection
            validated_sizes = self.get_validated_sizes()
            sizes_collection = self.db.collection(Config.get_collection_name("sizes"))
            for size_id, size_model in validated_sizes:
                doc_ref = sizes_collection.document(size_id)
                batch.set(doc_ref, size_model.dict())
                
            # Seed test users
            validated_users = self.get_validated_users()
            users_collection = self.db.collection(Config.get_collection_name("users"))
            for user_id, user_model in validated_users:
                doc_ref = users_collection.document(user_id)
                batch.set(doc_ref, user_model.dict())
            
            # Commit all changes atomically
            batch.commit()
            
            return {
                "success": True,
                "counts": {
                    "styles": len(validated_styles),
                    "colors": len(validated_colors),
                    "sizes": len(validated_sizes),  
                    "users": len(validated_users)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }