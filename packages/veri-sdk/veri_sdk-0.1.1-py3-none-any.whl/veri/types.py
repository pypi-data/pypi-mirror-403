"""
Type definitions for Veri SDK
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DetectionModel(str, Enum):
    """Available detection models"""

    VERI_FACE = "veri_face"


class ModelResult(BaseModel):
    """Individual model result from the detection pipeline"""

    score: float | None = Field(default=None, description="Model score (0-1)")
    status: str = Field(description="Model status (success/error)")
    latency_ms: int | None = Field(default=None, description="Inference latency in ms")
    error: str | None = Field(default=None, description="Error message if failed")


class DetectionResult(BaseModel):
    """Complete detection result"""

    # Original fields from the API
    prediction: str = Field(description="Prediction: 'ai', 'real', or 'uncertain'")
    confidence: float = Field(description="Overall confidence score (0-1)")
    ensemble_score: float | None = Field(default=None, description="Weighted ensemble score")
    verdict: str = Field(description="Verdict: 'ai_generated', 'uncertain', or 'likely_real'")
    models_succeeded: int = Field(description="Number of models that succeeded")
    models_total: int = Field(description="Total models invoked")
    model_results: dict[str, ModelResult] = Field(description="Per-model results")
    detection_latency_ms: int = Field(description="Total detection latency in ms")

    # SDK-friendly fields
    is_fake: bool | None = Field(
        alias="isFake", default=None, description="Whether image is AI-generated"
    )
    processing_time_ms: int = Field(
        alias="processingTimeMs", description="Total processing time in ms"
    )
    image_hash: str = Field(alias="imageHash", description="SHA-256 hash of image")
    cached: bool = Field(description="Whether result was from cache")
    timestamp: str = Field(description="Detection timestamp (ISO 8601)")

    model_config = ConfigDict(populate_by_name=True)


class DetectionOptions(BaseModel):
    """Options for detection request"""

    models: list[str] | None = Field(default=None, description="Specific models to use")
    threshold: float = Field(default=0.5, ge=0, le=1, description="Classification threshold")

    model_config = ConfigDict(populate_by_name=True)
