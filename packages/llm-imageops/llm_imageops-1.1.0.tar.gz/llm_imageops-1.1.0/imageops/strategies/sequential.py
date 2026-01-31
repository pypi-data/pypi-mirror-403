"""Sequential processing strategy."""

import asyncio
import logging
import time
from typing import Callable, Awaitable, Optional, Literal

from ..utils.metadata import extract_metadata
from ..operations import (
    resize_width,
    resize_height,
    fix_exif_orientation,
    handle_alpha_channel,
    slice_by_height,
    handle_animated_gif,
    handle_wide_panorama,
    compress_to_size,
    encode_to_base64
)
from ..core.result import ProcessingResult, ImageOutput

logger = logging.getLogger("imageops")

# Type for progress callback
ProgressCallback = Callable[[str, float], Awaitable[None]]


async def process_sequential(
    file_path: str,
    provider,
    output_format: Literal["base64", "file"],
    output_folder: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    quality: int = 90
    ):
    """
    Sequential processing strategy: Width → Height → Compress → Encode.
    
    Args:
        file_path: Path to image file
        provider: Provider instance
        output_format: "base64" or "file"
        output_folder: Optional custom folder name for temp files
        progress_callback: Optional progress callback function
        quality: JPEG quality
        
    Returns:
        ProcessingResult object
    """
    start_time = time.time()
    
    async def update_progress(step: str, progress: float):
        """Helper to update progress if callback provided."""
        if progress_callback:
            try:
                await progress_callback(step, progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    await update_progress("Starting", 0.0)
    
    # Extract metadata
    await update_progress("Analyzing", 0.1)
    metadata = await extract_metadata(file_path)
    
    # Check if processing needed
    if not provider.needs_processing(metadata):
        # Handle output format
        if output_format == "base64":
            data = await encode_to_base64(file_path)
        else:
            data = file_path
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            success=True,
            images=[ImageOutput(
                data=data,
                format=output_format,
                media_type=metadata.media_type,
                width=metadata.width,
                height=metadata.height,
                size_bytes=metadata.size_bytes
            )],
            output_format=output_format,
            original_path=file_path,
            original_metadata=metadata.dict(),
            provider=provider.name,
            strategy_used="sequential",
            processing_time_ms=processing_time_ms,
            was_sliced=False,
            slice_count=1
        )
    
    # Processing needed
    await update_progress("Pre-processing", 0.2)
    processed_path = file_path
    temp_files = []
    
    # Handle animated GIFs
    processed_path = await handle_animated_gif(processed_path, metadata)
    if processed_path != file_path:
        temp_files.append(processed_path)
        metadata = await extract_metadata(processed_path)
    
    # Fix EXIF orientation
    processed_path = await fix_exif_orientation(processed_path)
    if processed_path != file_path and processed_path not in temp_files:
        temp_files.append(processed_path)
        metadata = await extract_metadata(processed_path)
    
    # Handle alpha channel
    processed_path = await handle_alpha_channel(processed_path, metadata)
    if processed_path not in [file_path] + temp_files:
        temp_files.append(processed_path)
        metadata = await extract_metadata(processed_path)
    
    # Check for wide panorama
    panorama_slices = await handle_wide_panorama(processed_path, metadata, thread_id=output_folder)
    if len(panorama_slices) > 1:
        # Process each panorama slice
        await update_progress("Processing panorama", 0.4)
        final_slices = []
        
        for i, slice_path in enumerate(panorama_slices):
            slice_meta = await extract_metadata(slice_path)
            
            # Compress if needed
            if slice_meta.size_mb > provider.config.max_size_mb:
                compressed = await compress_to_size(
                    slice_path,
                    provider.config.max_size_mb,
                    output_folder
                )
                final_slices.append(compressed)
            else:
                final_slices.append(slice_path)
        
        # Convert to output format
        images = []
        for slice_path in final_slices:
            slice_meta = await extract_metadata(slice_path)
            if output_format == "base64":
                data = await encode_to_base64(slice_path)
            else:
                data = slice_path
            
            images.append(ImageOutput(
                data=data,
                format=output_format,
                media_type=slice_meta.media_type,
                width=slice_meta.width,
                height=slice_meta.height,
                size_bytes=slice_meta.size_bytes,
                was_sliced=True
            ))
        
        await update_progress("Complete", 1.0)
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            success=True,
            images=images,
            output_format=output_format,
            original_path=file_path,
            original_metadata=metadata.dict(),
            provider=provider.name,
            strategy_used="sequential",
            processing_time_ms=processing_time_ms,
            was_sliced=True,
            slice_count=len(images)
        )
    
    # Step 1: Resize width if needed
    await update_progress("Resizing width", 0.3)
    if metadata.width > provider.config.max_width:
        processed_path = await resize_width(
            processed_path,
            provider.config.max_width,
            output_folder,
            quality
        )
        temp_files.append(processed_path)
        metadata = await extract_metadata(processed_path)
    
    # Step 2: Handle height - smart resize or slice
    await update_progress("Processing height", 0.5)
    if metadata.height > provider.config.max_height:
        # Smart decision: Only slice if height is significantly over limit
        # If height is < 1.5x limit, just resize instead of slicing
        height_ratio = metadata.height / provider.config.max_height
        
        if height_ratio < 1.5:
            # Close to limit - resize instead of slicing
            # This avoids unnecessary slicing for images just slightly over limit
            processed_path = await resize_height(
                processed_path,
                provider.config.max_height,
                output_folder,
                quality
            )
            temp_files.append(processed_path)
            metadata = await extract_metadata(processed_path)
            # Continue to Step 3 (compression check)
        else:
            # Way over limit - slice makes more sense
            segment_paths = await slice_by_height(
                processed_path,
                provider.config.max_height,
                output_folder,
                quality
            )
            temp_files.extend(segment_paths)
            
            # Compress each segment if needed
            await update_progress("Compressing segments", 0.7)
            final_segments = []
            for seg_path in segment_paths:
                seg_meta = await extract_metadata(seg_path)
                if seg_meta.size_mb > provider.config.max_size_mb:
                    compressed = await compress_to_size(
                        seg_path,
                        provider.config.max_size_mb,
                        output_folder
                    )
                    final_segments.append(compressed)
                    temp_files.append(compressed)
                else:
                    final_segments.append(seg_path)
            
            # Convert to output format
            await update_progress("Encoding", 0.9)
            images = []
            for seg_path in final_segments:
                seg_meta = await extract_metadata(seg_path)
                if output_format == "base64":
                    data = await encode_to_base64(seg_path)
                else:
                    data = seg_path
                
                images.append(ImageOutput(
                    data=data,
                    format=output_format,
                    media_type=seg_meta.media_type,
                    width=seg_meta.width,
                    height=seg_meta.height,
                    size_bytes=seg_meta.size_bytes,
                    was_sliced=True
                ))
            
            await update_progress("Complete", 1.0)
            processing_time_ms = (time.time() - start_time) * 1000
            
            return ProcessingResult(
                success=True,
                images=images,
                output_format=output_format,
                original_path=file_path,
                original_metadata=metadata.dict(),
                provider=provider.name,
                strategy_used="sequential",
                processing_time_ms=processing_time_ms,
                was_sliced=True,
                slice_count=len(images)
            )
    
    # Step 3: Compress if needed
    await update_progress("Compressing", 0.7)
    if metadata.size_mb > provider.config.max_size_mb:
        processed_path = await compress_to_size(
            processed_path,
            provider.config.max_size_mb,
            output_folder
        )
        temp_files.append(processed_path)
        metadata = await extract_metadata(processed_path)
    
    # Convert to output format
    await update_progress("Encoding", 0.9)
    if output_format == "base64":
        data = await encode_to_base64(processed_path)
    else:
        data = processed_path
    
    await update_progress("Complete", 1.0)
    processing_time_ms = (time.time() - start_time) * 1000
    
    return ProcessingResult(
        success=True,
        images=[ImageOutput(
            data=data,
            format=output_format,
            media_type=metadata.media_type,
            width=metadata.width,
            height=metadata.height,
            size_bytes=metadata.size_bytes,
            was_resized=True,
            was_compressed=True
        )],
        output_format=output_format,
        original_path=file_path,
        original_metadata=metadata.dict(),
        provider=provider.name,
        strategy_used="sequential",
        processing_time_ms=processing_time_ms,
        was_sliced=False,
        slice_count=1
    )

