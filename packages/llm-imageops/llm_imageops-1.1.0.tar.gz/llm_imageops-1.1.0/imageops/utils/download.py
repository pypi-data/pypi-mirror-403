"""URL download with retry logic."""

import asyncio
import os
import tempfile
from typing import Tuple
import logging
import httpx
import aiofiles

from .validation import InputValidator
from ..exceptions import ImageDownloadError

logger = logging.getLogger("imageops")


async def download_if_url(
    source: str,
    timeout: float = 10.0,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Tuple[str, bool]:
    """
    Download image from URL with retry logic and exponential backoff.
    
    Args:
        source: File path or URL
        timeout: Download timeout in seconds
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor
        
    Returns:
        Tuple of (file_path, is_temp_file)
        
    Raises:
        ImageDownloadError: If download fails after all retries
        FileNotFoundError: If local file doesn't exist
    """
    # Check if it's a local file
    if not source.startswith(("http://", "https://")):
        if not os.path.exists(source):
            raise FileNotFoundError(f"File not found: {source}")
        return source, False
    
    # Validate URL
    validated_url = InputValidator.validate_url(source)
    
    # Retry loop
    last_exception = None
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout),
                follow_redirects=True,
                limits=httpx.Limits(max_connections=5)
            ) as client:
                response = await client.get(validated_url)
                response.raise_for_status()
                
                # Validate content type - check both header and file extension
                content_type = response.headers.get("content-type", "")
                file_ext = os.path.splitext(validated_url.split("?")[0])[1].lower()
                valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
                
                # Accept if either content-type is image/* OR file extension is valid
                is_valid_content_type = content_type.startswith("image/")
                is_valid_extension = file_ext in valid_extensions
                
                if not is_valid_content_type and not is_valid_extension:
                    raise ValueError(
                        f"URL does not appear to be an image. "
                        f"Content-Type: {content_type}, Extension: {file_ext}"
                    )
                
                # Check size
                # content_length = response.headers.get("content-length")
                # if content_length:
                #     size_mb = int(content_length) / (1024 * 1024)
                #     if size_mb > 100:
                #         raise ValueError(f"Image too large: {size_mb:.1f}MB (max: 100MB)")
                
                # Save to temp file
                suffix = os.path.splitext(validated_url.split("?")[0])[1] or ".jpg"
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                    prefix="imageops_download_"
                )
                temp_path = temp_file.name
                temp_file.close()
                
                # Write content
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(response.content)
                
                return temp_path, True
                
        except httpx.TimeoutException as e:
            last_exception = e
            logger.warning(f"Download timeout (attempt {attempt + 1}): {e}")
            
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                raise ImageDownloadError(
                    f"HTTP {e.response.status_code}: {validated_url}"
                ) from e
            last_exception = e
            logger.warning(f"HTTP error (attempt {attempt + 1}): {e}")
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Download error (attempt {attempt + 1}): {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            wait_time = backoff_factor ** attempt
            await asyncio.sleep(wait_time)
    
    raise ImageDownloadError(
        f"Failed to download after {max_retries} attempts: {validated_url}"
    ) from last_exception

