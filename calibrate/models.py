"""
Typed data structures shared across the calibration Lambda.

Keeping them in their own module makes the rest of the codebase cleaner and
allows IDEs / type-checkers to import them without pulling in heavy runtime
dependencies such as `boto3` or `opencv`.
"""

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

    class Config:
        # Allow forward compatibility in case the producer adds new keys.
        extra = "allow"


class SQSMessageBody(BaseModel):
    """
    Exact JSON payload placed on the SQS queue.

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
    Environment variables configuration for the calibration Lambda.
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


__all__ = ["Metadata", "SQSMessageBody", "Settings"]
