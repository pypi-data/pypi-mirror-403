"""Compression operations with adaptive quality and smart scaling."""

import asyncio
import logging
import os
import tempfile
from typing import Optional, Tuple, List
import cv2
import math

from ..exceptions import ImageProcessingError

logger = logging.getLogger("imageops")


def _profile_compression(img, temp_path: str, sample_qualities: List[int]) -> List[Tuple[int, float]]:
    """
    Profile image compression at different quality levels.
    
    Returns:
        List of (quality, size_mb) tuples
    """
    profile = []
    for quality in sample_qualities:
        cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        profile.append((quality, size_mb))
    return profile


def _interpolate_quality(profile: List[Tuple[int, float]], target_mb: float) -> int:
    """
    Interpolate to find the quality level that achieves target size.
    
    Returns:
        Predicted quality level (10-95)
    """
    # Sort by size descending
    profile = sorted(profile, key=lambda x: x[1], reverse=True)
    
    # If target is larger than largest sample, use highest quality
    if target_mb >= profile[0][1]:
        return profile[0][0]
    
    # If target is smaller than smallest sample, extrapolate
    if target_mb < profile[-1][1]:
        # Linear extrapolation from last two points
        q1, s1 = profile[-2]
        q2, s2 = profile[-1]
        if s1 != s2:
            slope = (q2 - q1) / (s2 - s1)
            predicted = q2 + slope * (target_mb - s2)
            return max(10, min(95, int(predicted)))
        return 10
    
    # Interpolate between two points
    for i in range(len(profile) - 1):
        q1, s1 = profile[i]
        q2, s2 = profile[i + 1]
        
        if s2 <= target_mb <= s1:
            # Linear interpolation
            if s1 != s2:
                ratio = (target_mb - s2) / (s1 - s2)
                predicted = q2 + ratio * (q1 - q2)
                return max(10, min(95, int(predicted)))
    
    return 50  # Default fallback


async def compress_to_size(
    image_path: str,
    max_size_mb: float,
    output_folder: Optional[str] = None,
    quality_start: int = 95,
    quality_step: int = 5,
    min_quality: int = 10
) -> str:
    """
    Compress image to target size using adaptive quality and smart scaling.
    
    Strategies:
    1. Quick profiling (2-3 samples) to understand compression curve
    2. Interpolate to predict exact quality needed
    3. If quality alone insufficient, calculate proportional downscaling
    4. Fallback to quality 60 if target impossible
    
    Args:
        image_path: Path to image
        max_size_mb: Maximum size in MB
        output_folder: Optional custom folder name for temp files
        quality_start: Starting quality (unused, kept for API compatibility)
        quality_step: Quality reduction step (unused, kept for API compatibility)
        min_quality: Minimum quality
        
    Returns:
        Path to compressed image
    """
    def _compress():
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        height, width = img.shape[:2]
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create temp path
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            temp_path = os.path.join(output_folder, f"compressed_{os.path.basename(image_path)}")
        else:
            temp_path = tempfile.mktemp(suffix=".jpg")
        
        # Get original size
        cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        original_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        
        # Step 1: Quick profiling (2-3 samples)
        sample_qualities = [95, 75, 50]
        profile = _profile_compression(img, temp_path, sample_qualities)
        
        # Step 2: Calculate compression ratio needed
        ratio = max_size_mb / original_size_mb
        
        # Step 3: Decision tree
        if ratio >= 0.5:
            # Quality reduction alone should work
            # Predict exact quality needed
            predicted_quality = _interpolate_quality(profile, max_size_mb)
            
            # Try predicted quality
            cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, predicted_quality])
            current_size = os.path.getsize(temp_path)
            
            if current_size <= max_size_bytes:
                return temp_path
            
            # If prediction was slightly off, try a bit lower
            for quality_adjust in [5, 10, 15, 20]:
                adjusted_quality = max(min_quality, predicted_quality - quality_adjust)
                cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, adjusted_quality])
                current_size = os.path.getsize(temp_path)
                
                if current_size <= max_size_bytes:
                    return temp_path
        
        # Quality alone won't work - need to resize
        # Step 4: Calculate proportional downscaling
        # Use sqrt for dimension scaling (since area = width × height)
        scale_factor = math.sqrt(ratio * 1.3)  # 1.3 safety margin
        scale_factor = max(0.01, min(1.0, scale_factor))  # Clamp between 1% and 100%
        
        new_width = max(10, int(width * scale_factor))
        new_height = max(10, int(height * scale_factor))
        
        # Resize image
        resized_img = cv2.resize(
            img,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )
        
        # Compress at moderate quality (90-92%)
        for quality in [92, 90, 85, 80, 70, 60, 50, 40, 30, 20, 10]:
            cv2.imwrite(temp_path, resized_img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            current_size = os.path.getsize(temp_path)
            
            if current_size <= max_size_bytes:
                return temp_path
        
        # Fallback: If still too large, try more aggressive resize
        if current_size > max_size_bytes:
            # Try 80% of calculated scale
            scale_factor *= 0.8
            new_width = max(10, int(width * scale_factor))
            new_height = max(10, int(height * scale_factor))
            
            resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            cv2.imwrite(temp_path, resized_img, [cv2.IMWRITE_JPEG_QUALITY, 60])
            current_size = os.path.getsize(temp_path)
            
            if current_size <= max_size_bytes:
                return temp_path
        
        # Final fallback: Return best effort at quality 60
        logger.warning(
            f"Could not compress to {max_size_mb}MB. "
            f"Returning best effort: {current_size / 1024 / 1024:.2f}MB at quality 60"
        )
        return temp_path
    
    try:
        return await asyncio.to_thread(_compress)
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise ImageProcessingError(f"Compression failed: {e}") from e

