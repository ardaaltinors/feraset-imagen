"""Pydantic models for strict schema validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum


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


class TransactionType(str, Enum):
    """Transaction types for credit operations."""
    DEDUCTION = "deduction"
    REFUND = "refund"


class TransactionModel(BaseModel):
    """Schema for credit transactions."""
    id: str = Field(..., min_length=1, max_length=100)
    type: TransactionType
    credits: int = Field(..., ge=1)
    generation_request_id: Optional[str] = Field(None, max_length=100)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserCreditsResponse(BaseModel):
    """Response schema for getUserCredits endpoint."""
    current_credits: int = Field(..., ge=0)
    transactions: List[TransactionModel] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }