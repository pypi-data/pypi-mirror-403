"""Base64 encoding operations."""

import asyncio
import base64
import logging
import os

logger = logging.getLogger("imageops")


async def encode_to_base64(file_path: str, include_prefix: bool = False) -> str:
    """
    Encode image to base64 string.
    
    Args:
        file_path: Path to image file
        include_prefix: If True, returns data URI format (data:image/jpeg;base64,...)
                       If False, returns just the base64 string
        
    Returns:
        Base64 encoded string (with or without data URI prefix)
    """
    def _encode():
        with open(file_path, "rb") as f:
            image_data = f.read()
            encoded = base64.b64encode(image_data).decode("utf-8")
            
            if include_prefix:
                # Determine media type from file extension
                ext = os.path.splitext(file_path)[1].lower()
                media_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp"
                }
                media_type = media_type_map.get(ext, "image/jpeg")
                return f"data:{media_type};base64,{encoded}"
            
            return encoded
    
    return await asyncio.to_thread(_encode)


async def get_image_with_media_type(file_path: str) -> tuple[str, str]:
    """
    Encode image and return both base64 and media type.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (base64_string, media_type)
    """
    def _encode():
        with open(file_path, "rb") as f:
            image_data = f.read()
            encoded = base64.b64encode(image_data).decode("utf-8")
            
            # Determine media type
            ext = os.path.splitext(file_path)[1].lower()
            media_type_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            media_type = media_type_map.get(ext, "image/jpeg")
            
            return encoded, media_type
    
    return await asyncio.to_thread(_encode)


