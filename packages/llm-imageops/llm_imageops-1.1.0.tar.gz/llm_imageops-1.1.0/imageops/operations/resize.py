"""Resize operations with EXIF and alpha channel handling."""

import asyncio
import logging
import os
import tempfile
from typing import Optional
import cv2
from PIL import Image, ExifTags

logger = logging.getLogger("imageops")


async def resize_width(
    image_path: str,
    max_width: int,
    output_folder: Optional[str] = None,
    quality: int = 90
) -> str:
    """
    Resize image width while maintaining aspect ratio.
    
    Args:
        image_path: Path to image
        max_width: Maximum width in pixels
        output_folder: Optional custom folder name for temp files
        quality: JPEG quality
        
    Returns:
        Path to resized image
    """
    def _resize():
        try:
            import cv2
        except ImportError:
            raise ImportError("opencv-python is required. Install with: pip install opencv-python-headless")
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        height, width = img.shape[:2]
        if width <= max_width:
            return image_path
        
        # Calculate new dimensions
        scale = max_width / width
        new_size = (max_width, int(height * scale))
        
        # Resize
        resized_img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        
        # Save to temp file
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            temp_path = os.path.join(output_folder, f"resized_w_{os.path.basename(image_path)}")
        else:
            temp_path = tempfile.mktemp(suffix=".jpg")
        
        cv2.imwrite(temp_path, resized_img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return temp_path
    
    return await asyncio.to_thread(_resize)


async def resize_height(
    image_path: str,
    max_height: int,
    output_folder: Optional[str] = None,
    quality: int = 90
) -> str:
    """
    Resize image height while maintaining aspect ratio.
    
    Args:
        image_path: Path to image
        max_height: Maximum height in pixels
        output_folder: Optional custom folder name for temp files
        quality: JPEG quality
        
    Returns:
        Path to resized image
    """
    def _resize():
        try:
            import cv2
        except ImportError:
            raise ImportError("opencv-python is required. Install with: pip install opencv-python-headless")
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        height, width = img.shape[:2]
        if height <= max_height:
            return image_path
        
        # Calculate new dimensions
        scale = max_height / height
        new_size = (int(width * scale), max_height)
        
        # Resize
        resized_img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        
        # Save to temp file
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            temp_path = os.path.join(output_folder, f"resized_h_{os.path.basename(image_path)}")
        else:
            temp_path = tempfile.mktemp(suffix=".jpg")
        
        cv2.imwrite(temp_path, resized_img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return temp_path
    
    return await asyncio.to_thread(_resize)


async def fix_exif_orientation(image_path: str) -> str:
    """
    Fix EXIF orientation (auto-rotate images).
    
    Args:
        image_path: Path to image
        
    Returns:
        Path to corrected image (or original if no correction needed)
    """
    def _fix():
        try:
            from PIL import Image, ExifTags
        except ImportError:
            logger.warning("PIL not available, skipping EXIF orientation fix")
            return image_path
        
        try:
            img = Image.open(image_path)
            
            # Check for EXIF data
            if not hasattr(img, '_getexif') or img._getexif() is None:
                return image_path
            
            exif = dict(img._getexif().items())
            
            # Find orientation tag
            orientation_key = None
            for key in ExifTags.TAGS.keys():
                if ExifTags.TAGS[key] == 'Orientation':
                    orientation_key = key
                    break
            
            if orientation_key and orientation_key in exif:
                orientation = exif[orientation_key]
                
                # Rotate based on orientation
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
                else:
                    return image_path
                
                # Save corrected image
                temp_path = tempfile.mktemp(suffix=".jpg")
                img.save(temp_path, quality=95)
                return temp_path
            
            return image_path
            
        except Exception as e:
            logger.warning(f"Could not fix EXIF orientation: {e}")
            return image_path
    
    return await asyncio.to_thread(_fix)


async def handle_alpha_channel(image_path: str, metadata) -> str:
    """
    Convert RGBA to RGB (remove alpha channel).
    
    Args:
        image_path: Path to image
        metadata: Image metadata
        
    Returns:
        Path to converted image (or original if no alpha)
    """
    if not metadata.has_alpha:
        return image_path
    
    def _remove_alpha():
        try:
            from PIL import Image
        except ImportError:
            logger.warning("PIL not available, skipping alpha channel handling")
            return image_path
        
        try:
            img = Image.open(image_path)
            
            # Convert RGBA → RGB on white background
            if img.mode in ('RGBA', 'LA', 'PA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                
                temp_path = tempfile.mktemp(suffix=".jpg")
                background.save(temp_path, "JPEG", quality=95)
                return temp_path
            
            return image_path
            
        except Exception as e:
            logger.warning(f"Could not remove alpha channel: {e}")
            return image_path
    
    return await asyncio.to_thread(_remove_alpha)

