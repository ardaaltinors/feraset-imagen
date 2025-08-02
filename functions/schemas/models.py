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
    total_images_generated: int = Field(default=0, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

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


class AIModel(str, Enum):
    """AI models for image generation."""
    MODEL_A = "Model A"
    MODEL_B = "Model B"


class GenerationStatus(str, Enum):
    """Generation request status."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class CreateGenerationRequestModel(BaseModel):
    """Schema for createGenerationRequest input."""
    userId: str = Field(..., min_length=1, max_length=100)
    model: AIModel
    style: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., min_length=1, max_length=50)
    size: str = Field(..., pattern=r'^\d+x\d+$')
    prompt: str = Field(..., min_length=1, max_length=1000)


class GenerationRequestModel(BaseModel):
    """Schema for generation request records."""
    id: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    model: AIModel
    style: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., min_length=1, max_length=50)
    size: str = Field(..., pattern=r'^\d+x\d+$')
    prompt: str = Field(..., min_length=1, max_length=1000)
    status: GenerationStatus = GenerationStatus.PENDING
    credits_deducted: int = Field(..., ge=0)
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CreateGenerationResponseModel(BaseModel):
    """Schema for createGenerationRequest response."""
    generationRequestId: str = Field(..., min_length=1)
    status: GenerationStatus = GenerationStatus.QUEUED
    deductedCredits: int = Field(..., ge=0)
    estimatedCompletionTime: Optional[datetime] = None
    queuePosition: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenerationStatusResponseModel(BaseModel):
    """Schema for generation status response."""
    generationRequestId: str = Field(..., min_length=1)
    status: GenerationStatus
    imageUrl: Optional[str] = None
    error_message: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    queue_position: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskPayloadModel(BaseModel):
    """Schema for Cloud Tasks payload."""
    generation_request_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    model: AIModel
    style: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., min_length=1, max_length=50)
    size: str = Field(..., pattern=r'^\d+x\d+$')
    prompt: str = Field(..., min_length=1, max_length=1000)
    priority: str = Field(default="normal")
    retry_count: int = Field(default=0, ge=0)