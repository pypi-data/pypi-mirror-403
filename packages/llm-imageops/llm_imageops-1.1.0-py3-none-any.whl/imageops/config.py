"""Configuration module with resource limits and security settings."""

from typing import List, Optional
from pydantic import Field, validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        raise ImportError(
            "pydantic-settings is required. Install with: pip install pydantic-settings"
        )


class ImageOpsConfig(BaseSettings):
    """Global configuration with resource limits and security."""
    
    # Resource Limits
    max_image_size_mb: float = Field(
        100.0,
        gt=0,
        description="Maximum input image size in MB"
    )
    max_dimension: int = Field(
        100000,
        gt=0,
        description="Maximum width or height in pixels"
    )
    max_batch_size: int = Field(
        50,
        ge=1,
        le=1000,
        description="Maximum number of images in batch"
    )
    
    # Temp Management
    temp_dir_pattern: str = Field(
        "imageops_{thread_id}",
        description="Pattern for temp directory naming"
    )
    auto_cleanup: bool = Field(
        True,
        description="Auto-cleanup temp files"
    )
    
    # Performance
    max_concurrent_ops: int = Field(
        5,
        ge=1,
        le=20,
        description="Max concurrent operations"
    )
    download_timeout: float = Field(
        10.0,
        gt=0,
        description="Download timeout in seconds"
    )
    processing_timeout: float = Field(
        300.0,
        gt=0,
        description="Max processing time per image in seconds"
    )
    
    # Retry Logic
    max_download_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Max download retries"
    )
    retry_backoff_factor: float = Field(
        2.0,
        ge=1.0,
        description="Exponential backoff factor"
    )
    
    # Compression
    default_quality: int = Field(
        90,
        ge=1,
        le=100,
        description="Default JPEG quality"
    )
    quality_step: int = Field(
        5,
        ge=1,
        le=20,
        description="Quality reduction step"
    )
    min_quality: int = Field(
        10,
        ge=1,
        le=100,
        description="Minimum JPEG quality"
    )
    
    # Logging
    enable_logging: bool = Field(
        True,
        description="Enable logging"
    )
    log_level: str = Field(
        "INFO",
        description="Logging level"
    )
    log_file: Optional[str] = Field(
        None,
        description="Log file path"
    )
    
    # Security
    validate_paths: bool = Field(
        True,
        description="Validate file paths against traversal attacks"
    )
    allowed_formats: List[str] = Field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        description="Allowed image formats"
    )
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    class Config:
        env_prefix = "IMAGEOPS_"
        case_sensitive = False

