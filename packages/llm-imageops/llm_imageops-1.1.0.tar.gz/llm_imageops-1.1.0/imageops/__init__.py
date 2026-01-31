"""ImageOps: Production-grade image preprocessing for LLMs."""

from .config import ImageOpsConfig
from .core import ImageProcessor, ProcessingResult, ImageOutput
from .exceptions import *
from .providers import get_provider, register_provider

__version__ = "1.1.0"

# Simple API
async def process(
    image_source: str,
    provider: str = "anthropic",
    output_format: str = "base64",
    progress_callback=None,
    **kwargs
):
    """
    Simple one-line API to process images.
    
    Args:
        image_source: File path or URL
        provider: Provider name (default: "anthropic")
        output_format: "base64" or "file" (default: "base64")
        progress_callback: Optional async progress callback
        **kwargs: Additional arguments
        
    Returns:
        ProcessingResult object
        
    Example:
        >>> result = await imageops.process("image.jpg", provider="anthropic")
        >>> print(result.images[0].data[:50])  # First 50 chars of base64
    """
    async with ImageProcessor(provider=provider) as processor:
        return await processor.process(
            image_source,
            output_format=output_format,
            progress_callback=progress_callback,
            **kwargs
        )


async def process_batch(
    image_sources: list,
    provider: str = "anthropic",
    output_format: str = "base64",
    **kwargs
):
    """
    Process multiple images concurrently.
    
    Args:
        image_sources: List of file paths or URLs
        provider: Provider name (default: "anthropic")
        output_format: "base64" or "file" (default: "base64")
        **kwargs: Additional arguments
        
    Returns:
        List of ProcessingResult objects
        
    Example:
        >>> results = await imageops.process_batch(
        ...     ["img1.jpg", "img2.jpg"],
        ...     provider="anthropic"
        ... )
    """
    async with ImageProcessor(provider=provider) as processor:
        return await processor.process_batch(
            image_sources,
            output_format=output_format,
            **kwargs
        )


__all__ = [
    "ImageOpsConfig",
    "ImageProcessor",
    "ProcessingResult",
    "ImageOutput",
    "process",
    "process_batch",
    "get_provider",
    "register_provider",
    # Exceptions
    "ImageOpsError",
    "ImageDownloadError",
    "ImageValidationError",
    "ImageProcessingError",
    "ImageCorruptedError",
    "ImageTooLargeError",
    "UnsupportedFormatError",
    "CompressionFailedError",
    "ProviderNotFoundError",
    "TimeoutError",
    "ResourceLimitError",
]

