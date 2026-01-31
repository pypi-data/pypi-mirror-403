"""Comprehensive exception hierarchy for imageops."""


class ImageOpsError(Exception):
    """Base exception for all imageops errors."""
    pass


class ImageDownloadError(ImageOpsError):
    """Failed to download image from URL."""
    pass


class ImageValidationError(ImageOpsError):
    """Image validation failed (format, size, etc.)."""
    pass


class ImageProcessingError(ImageOpsError):
    """Error during image processing operations."""
    pass


class ImageCorruptedError(ImageOpsError):
    """Image file is corrupted or unreadable."""
    pass


class ImageTooLargeError(ImageOpsError):
    """Image exceeds size or dimension limits."""
    pass


class UnsupportedFormatError(ImageOpsError):
    """Image format is not supported."""
    pass


class CompressionFailedError(ImageProcessingError):
    """Cannot compress image to required size."""
    pass


class ProviderNotFoundError(ImageOpsError):
    """Unknown or unsupported provider."""
    pass


class TimeoutError(ImageOpsError):
    """Operation timed out."""
    pass


class ResourceLimitError(ImageOpsError):
    """Resource limit exceeded (memory, file handles, etc.)."""
    pass

