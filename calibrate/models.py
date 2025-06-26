"""
Typed data structures shared across the calibration service.

Keeping them in their own module makes the rest of the codebase cleaner and
allows IDEs / type-checkers to import them without pulling in heavy runtime
dependencies such as `boto3` or `opencv`.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Metadata(BaseModel):
    """
    Context information that accompanies each calibration job.

    Attributes
    ----------
    run_id:
        Folder (S3 key-prefix) where output artefacts should be written.
    dataset:
        Folder (S3 key-prefix) that contains the source images.
    """

    run_id: str = Field(
        ..., description="Destination folder for result artefacts"
    )
    dataset: str = Field(
        ..., description="Source folder holding calibration images"
    )
    checkerboard_size: tuple[int, int] = Field(
        ..., description="Size of the checkerboard pattern in squares"
    )
    calibration_accuracy: float = Field(
        default=0.001, description="Accuracy of the calibration"
    )
    iterations: int = Field(
        default=30, description="Number of iterations for the calibration"
    )

    class Config:
        # Allow forward compatibility in case the producer adds new keys.
        extra = "allow"


class CalibrationRequest(BaseModel):
    """
    JSON payload for calibration requests from Cloudflare Queue.

    Example
    -------
    {
        "metadata": {
            "run_id": "runs/2024-04-21T10-15-00Z",
            "dataset": "datasets/board-shots"
        },
        "images": ["img_0001.jpg", "img_0002.jpg", "..."]
    }
    """

    metadata: Metadata
    images: list[str] = Field(
        ...,
        min_length=1,
        description="Relative filenames of images inside `metadata.dataset`",
    )

    class Config:
        # Fail fast if unexpected keys appear at the top level.
        extra = "forbid"


class Settings(BaseSettings):
    """
    Environment variables configuration for the calibration service.
    """

    r2_endpoint_url: str = Field(
        default="", description="Cloudflare R2 endpoint URL"
    )
    r2_access_key: str = Field(
        default="", description="Cloudflare R2 access key"
    )
    r2_secret_access_key: str = Field(
        default="", description="Cloudflare R2 secret access key"
    )
    r2_bucket: str = Field(default="", description="Cloudflare R2 bucket name")

    model_config = {
        "env_prefix": "",  # No prefix, use exact environment variable names
        "case_sensitive": False,  # Allow case-insensitive matching
    }


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str = Field(description="Health status")
    message: Optional[str] = Field(default=None, description="Optional message")


class CalibrationResult(BaseModel):
    """Model for calibration computation results."""

    camera_matrix: list[list[float]] = Field(description="3x3 camera matrix")
    dist: list[float] = Field(description="Distortion coefficients")
    processed_images: int = Field(
        description="Number of images successfully processed"
    )
    total_images: int = Field(description="Total number of images provided")


class CalibrationResponse(BaseModel):
    """Response model for calibration endpoint."""

    status: str = Field(description="Response status")
    message: str = Field(description="Response message")
    run_id: str = Field(description="Calibration run identifier")
    result: CalibrationResult = Field(
        description="Calibration computation results"
    )


class CalibrationResultResponse(BaseModel):
    """Response model for retrieving calibration results."""

    status: str = Field(description="Response status")
    run_id: str = Field(description="Calibration run identifier")
    result: CalibrationResult = Field(
        description="Calibration computation results"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Original calibration metadata"
    )


__all__ = [
    "Metadata",
    "CalibrationRequest",
    "Settings",
    "HealthResponse",
    "CalibrationResult",
    "CalibrationResponse",
    "CalibrationResultResponse",
]
