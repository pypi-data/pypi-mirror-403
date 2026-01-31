"""Result types and data classes."""

from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ImageOutput(BaseModel):
    """Single processed image output."""
    
    # Based on output_format parameter
    data: str = Field(..., description="base64 string OR file path")
    format: Literal["base64", "file"] = Field(..., description="Output format")
    
    # Metadata
    media_type: str = Field(..., description="image/jpeg, image/png, etc.")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    size_bytes: int = Field(..., ge=0, description="Image size in bytes")
    
    # Processing info
    was_resized: bool = Field(False, description="Whether image was resized")
    was_compressed: bool = Field(False, description="Whether image was compressed")
    was_sliced: bool = Field(False, description="Whether image was sliced")
    compression_quality: Optional[int] = Field(None, ge=1, le=100, description="Compression quality used")
    
    def to_data_uri(self) -> str:
        """
        Convert to data URI format with media type prefix.
        
        Returns:
            Data URI string like: data:image/jpeg;base64,<base64_data>
            
        Example:
            >>> img = ImageOutput(data="abc123...", format="base64", media_type="image/jpeg", ...)
            >>> img.to_data_uri()
            'data:image/jpeg;base64,abc123...'
        """
        if self.format != "base64":
            raise ValueError("to_data_uri() only works with base64 format")
        
        return f"data:{self.media_type};base64,{self.data}"
    
    class Config:
        frozen = True  # Immutable


class ProcessingResult(BaseModel):
    """Complete processing result."""
    
    success: bool = Field(..., description="Processing success status")
    
    # Outputs
    images: List[ImageOutput] = Field(..., description="Single image OR multiple if sliced")
    output_format: Literal["base64", "file"] = Field(..., description="Output format")
    
    # Original info
    original_path: str = Field(..., description="Original input path")
    original_metadata: Dict = Field(..., description="Original image metadata")
    
    # Processing stats
    provider: str = Field(..., description="Provider name")
    strategy_used: str = Field(..., description="Processing strategy used")
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    was_sliced: bool = Field(..., description="Whether image was sliced")
    slice_count: int = Field(..., ge=1, description="Number of slices")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Result creation timestamp")
    
    def to_anthropic_format(self) -> List[Dict]:
        """
        Convert to Anthropic message content format.
        
        Returns:
            List of formatted image content dicts
        """
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64" if img.format == "base64" else "url",
                    "media_type": img.media_type,
                    "data": img.data if img.format == "base64" else None
                }
            }
            for img in self.images
        ]
    
    async def cleanup(self):
        """Clean up temp files if output_format='file'."""
        if self.output_format == "file":
            from ..utils.cleanup import cleanup_files
            await cleanup_files([img.data for img in self.images])

