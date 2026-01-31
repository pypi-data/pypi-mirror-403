"""Image metadata extraction with format detection."""

import asyncio
import os
import logging
from pydantic import BaseModel, Field
from PIL import Image
import cv2

from ..exceptions import ImageProcessingError

logger = logging.getLogger("imageops")


class ImageMetadata(BaseModel):
    """Image metadata model."""
    
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    size_bytes: int = Field(..., ge=0)
    size_mb: float = Field(..., ge=0)
    format: str = Field(..., description="JPEG, PNG, etc.")
    media_type: str = Field(..., description="image/jpeg, etc.")
    is_animated: bool = Field(False)
    has_alpha: bool = Field(False)
    mode: str = Field("RGB")


async def extract_metadata(file_path: str) -> ImageMetadata:
    """
    Extract metadata with comprehensive error handling.
    Detects actual format (not just extension).
    Handles corrupted images, unusual formats, empty files.
    
    Args:
        file_path: Path to image file
        
    Returns:
        ImageMetadata object
        
    Raises:
        ValueError: If image is invalid, corrupted, or has invalid dimensions
    """
    def _extract() -> ImageMetadata:
        # Validate file exists and is not empty
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        size_bytes = os.path.getsize(file_path)
        if size_bytes == 0:
            raise ValueError(f"Empty image file: {file_path}")
        
        # Use PIL for format detection (imghdr deprecated in Python 3.13+)
        actual_format = None
        try:
            with Image.open(file_path) as img:
                actual_format = img.format
        except Exception:
            pass
        
        if actual_format is None:
            raise ValueError(f"Invalid or corrupted image: {file_path}")
        
        # Try PIL first (more robust)
        width = height = 0
        mode = "RGB"
        has_alpha = False
        is_animated = False
        img_format = actual_format.upper()
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                img_format = img.format or actual_format.upper()
                mode = img.mode
                has_alpha = mode in ("RGBA", "LA", "PA")
                
                # Check for animated GIF
                if img_format == "GIF":
                    try:
                        img.seek(1)
                        is_animated = True
                    except EOFError:
                        is_animated = False
                    finally:
                        img.seek(0)
        
        except Exception as pil_error:
            logger.warning(f"PIL failed to read {file_path}, trying cv2: {pil_error}")
            
            # Fallback to cv2
            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(
                    f"Cannot read image file (corrupted or unsupported): {file_path}"
                )
            
            height, width = img.shape[:2]
            has_alpha = len(img.shape) == 3 and img.shape[2] == 4
            mode = "RGBA" if has_alpha else "RGB"
            img_format = actual_format.upper()
            is_animated = False
        
        # Validate dimensions
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        
        if width > 100000 or height > 100000:
            raise ValueError(
                f"Image dimensions too large: {width}x{height} "
                "(max 100000px per side)"
            )
        
        # Map format to media type
        media_type_map = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "WEBP": "image/webp"
        }
        media_type = media_type_map.get(img_format, "image/jpeg")
        
        return ImageMetadata(
            width=width,
            height=height,
            size_bytes=size_bytes,
            size_mb=size_bytes / (1024 * 1024),
            format=img_format,
            media_type=media_type,
            is_animated=is_animated,
            has_alpha=has_alpha,
            mode=mode
        )
    
    try:
        return await asyncio.to_thread(_extract)
    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        raise ImageProcessingError(f"Metadata extraction failed: {e}") from e

