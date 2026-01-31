"""Input validation and security checks."""

import os
import re
from pathlib import Path
from typing import Optional
from ..exceptions import ImageValidationError, ImageTooLargeError, UnsupportedFormatError


class InputValidator:
    """Validate and sanitize user inputs against security attacks."""
    
    # Maximum file size to process (100MB default)
    MAX_FILE_SIZE_MB = 100.0
    
    # Allowed image formats
    ALLOWED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    # Dangerous path patterns
    DANGEROUS_PATTERNS = ["..", "~", "/etc", "/sys", "/proc"]
    
    @staticmethod
    def validate_file_path(path: str, max_size_mb: Optional[float] = None) -> str:
        """
        Validate and sanitize file path against path traversal attacks.
        
        Args:
            path: File path to validate
            max_size_mb: Maximum file size in MB (uses default if None)
            
        Returns:
            Absolute validated path
            
        Raises:
            ImageValidationError: If path is invalid or dangerous
            ImageTooLargeError: If file exceeds size limit
            UnsupportedFormatError: If format is not allowed
        """
        if not path:
            raise ImageValidationError("Path cannot be empty")
        
        # Check for dangerous patterns
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            if pattern in path:
                raise ImageValidationError(f"Potentially dangerous path pattern detected: {pattern}")
        
        try:
            # Resolve to absolute path
            abs_path = os.path.abspath(path)
            
            # Check if file exists
            if not os.path.exists(abs_path):
                raise ImageValidationError(f"File not found: {path}")
            
            # Check if it's a file (not a directory)
            if not os.path.isfile(abs_path):
                raise ImageValidationError(f"Path is not a file: {path}")
            
            # Check file size
            size_bytes = os.path.getsize(abs_path)
            size_mb = size_bytes / (1024 * 1024)
            
            max_size = max_size_mb if max_size_mb is not None else InputValidator.MAX_FILE_SIZE_MB
            if size_mb > max_size:
                raise ImageTooLargeError(
                    f"File too large: {size_mb:.1f}MB (max: {max_size}MB)"
                )
            
            # Check file extension
            ext = os.path.splitext(abs_path)[1].lower()
            if ext not in InputValidator.ALLOWED_FORMATS:
                raise UnsupportedFormatError(
                    f"Unsupported format: {ext}. "
                    f"Allowed: {', '.join(sorted(InputValidator.ALLOWED_FORMATS))}"
                )
            
            return abs_path
            
        except (ImageValidationError, ImageTooLargeError, UnsupportedFormatError):
            # Re-raise our exceptions
            raise
        except Exception as e:
            raise ImageValidationError(f"Invalid file path: {path} - {str(e)}") from e
    
    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            ImageValidationError: If URL is invalid
        """
        if not url:
            raise ImageValidationError("URL cannot be empty")
        
        if not url.startswith(("http://", "https://")):
            raise ImageValidationError("URL must start with http:// or https://")
        
        # Basic URL validation pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            raise ImageValidationError(f"Invalid URL format: {url}")
        
        return url

