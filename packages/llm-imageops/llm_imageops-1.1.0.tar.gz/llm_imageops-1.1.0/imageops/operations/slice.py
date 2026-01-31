"""Slice operations for image segmentation."""

import asyncio
import logging
import os
import tempfile
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("imageops")


async def slice_by_height(
    image_path: str,
    segment_height: int,
    output_folder: Optional[str] = None,
    quality: int = 90
) -> List[str]:
    """
    Slice image into vertical segments.
    
    Args:
        image_path: Path to image
        segment_height: Maximum height per segment in pixels
        output_folder: Optional custom folder name for temp files
        quality: JPEG quality
        
    Returns:
        List of paths to sliced segments
    """
    def _slice():
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        height, width = img.shape[:2]
        
        # Create temp directory for segments
        if output_folder:
            segments_dir = f"{output_folder}/segments"
        else:
            segments_dir = tempfile.mkdtemp(prefix="imageops_segments_")
        
        os.makedirs(segments_dir, exist_ok=True)
        
        segments = []
        y_steps = list(range(0, height, segment_height))
        
        for i, y in enumerate(y_steps):
            y_end = min(y + segment_height, height)
            segment = img[y:y_end, :]
            
            segment_path = os.path.join(segments_dir, f"segment_{i:03d}.jpg")
            cv2.imwrite(segment_path, segment, [cv2.IMWRITE_JPEG_QUALITY, quality])
            segments.append(segment_path)
        
        return segments
    
    return await asyncio.to_thread(_slice)


async def handle_animated_gif(image_path: str, metadata) -> str:
    """
    Handle animated GIFs by extracting first frame.
    
    Args:
        image_path: Path to image
        metadata: Image metadata
        
    Returns:
        Path to static image (first frame)
    """
    if not metadata.is_animated or metadata.format != "GIF":
        return image_path
    
    def _extract_first_frame():
        try:
            logger.warning(f"Animated GIF detected: {image_path}. Processing first frame only.")
            
            with Image.open(image_path) as img:
                img.seek(0)  # First frame
                rgb_img = img.convert("RGB")
                
                temp_path = tempfile.mktemp(suffix=".jpg")
                rgb_img.save(temp_path, "JPEG", quality=95)
                return temp_path
                
        except Exception as e:
            logger.warning(f"Could not extract GIF frame: {e}")
            return image_path
    
    return await asyncio.to_thread(_extract_first_frame)


async def handle_wide_panorama(
    image_path: str,
    metadata,
    max_aspect_ratio: float = 10.0,
    thread_id: Optional[str] = None
) -> List[str]:
    """
    Handle very wide panoramas by slicing horizontally.
    
    Args:
        image_path: Path to image
        metadata: Image metadata
        max_aspect_ratio: Maximum aspect ratio before slicing
        thread_id: Optional custom folder name for temp files
        
    Returns:
        List of image paths (original if not panorama, slices if panorama)
    """
    aspect_ratio = metadata.width / metadata.height
    
    if aspect_ratio <= max_aspect_ratio:
        return [image_path]
    
    def _slice_horizontally():
        logger.warning(
            f"Very wide image detected: {metadata.width}x{metadata.height} "
            f"(ratio: {aspect_ratio:.1f}:1). Slicing horizontally."
        )
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Calculate slice width
        num_slices = int(np.ceil(aspect_ratio / max_aspect_ratio))
        slice_width = metadata.width // num_slices
        
        # Create temp directory
        if thread_id:
            slices_dir = f"{thread_id}/slices"
        else:
            slices_dir = tempfile.mkdtemp(prefix="imageops_slices_")
        
        os.makedirs(slices_dir, exist_ok=True)
        
        slices = []
        for i in range(num_slices):
            x_start = i * slice_width
            x_end = min((i + 1) * slice_width, metadata.width)
            
            slice_img = img[:, x_start:x_end]
            slice_path = os.path.join(slices_dir, f"slice_{i:03d}.jpg")
            cv2.imwrite(slice_path, slice_img, [cv2.IMWRITE_JPEG_QUALITY, 90])
            slices.append(slice_path)
        
        return slices
    
    return await asyncio.to_thread(_slice_horizontally)

