# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum
import logging

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

initialize_app()


# Pydantic Models for strict schema validation
class StyleModel(BaseModel):
    """Schema for image generation styles."""
    display_name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    sort_order: int = Field(..., ge=1, le=100)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ColorModel(BaseModel):
    """Schema for color palettes."""
    display_name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)
    hex_examples: List[str] = Field(..., min_items=1, max_items=5)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    sort_order: int = Field(..., ge=1, le=100)

    @validator('hex_examples')
    def validate_hex_colors(cls, v):
        """Validate hex color format."""
        for color in v:
            if not color.startswith('#') or len(color) != 7:
                raise ValueError(f'Invalid hex color: {color}')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SizeModel(BaseModel):
    """Schema for image sizes and pricing."""
    width: int = Field(..., ge=128, le=2048)
    height: int = Field(..., ge=128, le=2048)
    aspect_ratio: str = Field(..., pattern=r'^\d+:\d+$')
    display_name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)
    credit_cost: int = Field(..., ge=1, le=100)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    sort_order: int = Field(..., ge=1, le=100)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserModel(BaseModel):
    """Schema for user accounts."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    current_credits: int = Field(..., ge=0)
    total_credits: int = Field(..., ge=0)
    total_images_generated: int = Field(default=0, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    @validator('total_credits')
    def validate_total_credits(cls, v, values):
        """Ensure total_credits >= current_credits."""
        if 'current_credits' in values and v < values['current_credits']:
            raise ValueError('total_credits must be >= current_credits')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@https_fn.on_request()
def on_request_example(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello world!")


def _get_validated_styles() -> List[tuple[str, StyleModel]]:
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


def _get_validated_colors() -> List[tuple[str, ColorModel]]:
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


def _get_validated_sizes() -> List[tuple[str, SizeModel]]:
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


def _get_validated_users() -> List[tuple[str, UserModel]]:
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


@https_fn.on_request()
def seed_database(req: https_fn.Request) -> https_fn.Response:
    """
    Seed the database with validated initial data.
    
    This endpoint populates Firestore collections with strictly validated:
    - Image generation styles (realistic, anime, etc.)
    - Color palettes (vibrant, monochrome, etc.) 
    - Available image sizes and pricing
    - Test user accounts
    
    All data is validated using Pydantic models before insertion.
    
    Returns:
        https_fn.Response: Success message or detailed validation errors
    """
    try:
        db = firestore.client()
        batch = db.batch()
        
        # Seed styles collection with validation
        validated_styles = _get_validated_styles()
        for style_id, style_model in validated_styles:
            batch.set(
                db.collection("styles").document(style_id), 
                style_model.dict()
            )
        
        # Seed colors collection with validation
        validated_colors = _get_validated_colors()
        for color_id, color_model in validated_colors:
            batch.set(
                db.collection("colors").document(color_id),
                color_model.dict()
            )
            
        # Seed sizes collection with validation
        validated_sizes = _get_validated_sizes()
        for size_id, size_model in validated_sizes:
            batch.set(
                db.collection("sizes").document(size_id),
                size_model.dict()
            )
            
        # Seed test users with validation
        validated_users = _get_validated_users()
        for user_id, user_model in validated_users:
            batch.set(
                db.collection("users").document(user_id),
                user_model.dict()
            )
        
        # Commit all changes atomically
        batch.commit()
        
        logging.info(
            "Database seeded successfully with validated data: "
            "%d styles, %d colors, %d sizes, %d users",
            len(validated_styles), len(validated_colors), 
            len(validated_sizes), len(validated_users)
        )
        
        return https_fn.Response(
            "Database seeded successfully with validated data! "
            f"Added {len(validated_styles)} styles, "
            f"{len(validated_colors)} colors, "
            f"{len(validated_sizes)} sizes, and "
            f"{len(validated_users)} test users."
        )
        
    except ValueError as e:
        # Pydantic validation errors
        logging.error("Data validation failed: %s", str(e))
        return https_fn.Response(
            f"Data validation error: {str(e)}", 
            status=400
        )
    except Exception as e:
        # Other errors (database, network, etc.)
        logging.error("Failed to seed database: %s", str(e))
        return https_fn.Response(
            f"Database error: {str(e)}", 
            status=500
        )