"""Main ImageProcessor orchestrator."""

import asyncio
import logging
from typing import List, Literal, Optional
from ..config import ImageOpsConfig
from ..providers import get_provider
from ..utils import setup_logging, InputValidator, download_if_url, CleanupManager
from ..strategies import process_sequential, ProgressCallback
from ..exceptions import TimeoutError as ImageOpsTimeoutError


class ImageProcessor:
    """Main image processor with context manager support."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        config: Optional[ImageOpsConfig] = None
    ):
        """
        Initialize ImageProcessor.
        
        Args:
            provider: Provider name (e.g., "anthropic")
            config: Optional configuration
        """
        self.provider_name = provider
        self.config = config or ImageOpsConfig()
        self.provider = get_provider(provider)
        self.cleanup_manager = CleanupManager()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging based on config."""
        if self.config.enable_logging:
            setup_logging(
                level=self.config.log_level,
                log_file=self.config.log_file
            )
    
    async def __aenter__(self):
        """Enter async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - cleanup all temp files."""
        await self.cleanup_manager.cleanup_all(ignore_errors=True)
        return False
    
    async def process(
        self,
        image_source: str,
        output_format: Literal["base64", "file"] = "base64",
        progress_callback: Optional[ProgressCallback] = None,
        timeout: Optional[float] = None,
        thread_id: Optional[str] = None,
        output_folder: Optional[str] = None,
        quality: int = 90,
        **kwargs
    ):
        """
        Process single image with timeout.
        
        Args:
            image_source: File path or URL
            output_format: "base64" or "file"
            progress_callback: Optional progress callback
            timeout: Processing timeout in seconds
            thread_id: Optional thread ID for temp directories (deprecated, use output_folder)
            output_folder: Custom folder name for temp files (e.g., "my_thread_123")
            quality: JPEG quality (1-100)
            
        Returns:
            ProcessingResult object
            
        Raises:
            TimeoutError: If processing exceeds timeout
        """
        timeout = timeout or self.config.processing_timeout
        
        try:
            # Use output_folder if provided, otherwise fall back to thread_id pattern
            folder_name = output_folder
            if not folder_name and thread_id:
                folder_name = thread_id  # Just use thread_id as-is, no prefix
            
            result = await asyncio.wait_for(
                self._process_internal(
                    image_source,
                    output_format,
                    progress_callback,
                    folder_name,
                    quality
                ),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            raise ImageOpsTimeoutError(
                f"Processing timeout after {timeout}s: {image_source}"
            )
    
    async def _process_internal(
        self,
        image_source: str,
        output_format: Literal["base64", "file"],
        progress_callback: Optional[ProgressCallback],
        folder_name: Optional[str],
        quality: int
    ):
        """Internal processing logic."""
        # Download if URL
        local_path, is_temp = await download_if_url(
            image_source,
            timeout=self.config.download_timeout,
            max_retries=self.config.max_download_retries,
            backoff_factor=self.config.retry_backoff_factor
        )
        
        if is_temp:
            self.cleanup_manager.track_file(local_path)
        
        # Validate file path
        validated_path = InputValidator.validate_file_path(
            local_path,
            max_size_mb=self.config.max_image_size_mb
        )
        
        # Process using sequential strategy
        result = await process_sequential(
            validated_path,
            self.provider,
            output_format,
            folder_name,
            progress_callback,
            quality
        )
        
        return result
    
    async def process_batch(
        self,
        image_sources: List[str],
        output_format: Literal["base64", "file"] = "base64",
        max_concurrent: Optional[int] = None,
        **kwargs
    ):
        """
        Process multiple images concurrently.
        
        Args:
            image_sources: List of file paths or URLs
            output_format: "base64" or "file"
            max_concurrent: Max concurrent operations
            
        Returns:
            List of ProcessingResult objects
        """
        # Validate batch size
        if len(image_sources) > self.config.max_batch_size:
            raise ValueError(
                f"Batch size {len(image_sources)} exceeds limit "
                f"of {self.config.max_batch_size}"
            )
        
        max_concurrent = max_concurrent or self.config.max_concurrent_ops
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(source: str):
            async with semaphore:
                return await self.process(source, output_format, **kwargs)
        
        results = await asyncio.gather(
            *[process_one(source) for source in image_sources],
            return_exceptions=True
        )
        
        return results

