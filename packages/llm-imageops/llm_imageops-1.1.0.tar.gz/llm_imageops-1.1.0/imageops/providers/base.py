"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel


class ProviderConfig(BaseModel):
    """Provider configuration model."""
    
    max_width: int
    max_height: int
    max_size_mb: float
    max_base64_size_mb: float
    max_images_per_call: int
    supported_formats: List[str]


class BaseProvider(ABC):
    """Base provider abstract class."""
    
    name: str
    config: ProviderConfig
    
    @abstractmethod
    def needs_processing(self, metadata: "ImageMetadata") -> bool:
        """Check if image needs processing based on provider limits."""
        pass
    
    @abstractmethod
    def format_for_api(self, images: List["ImageOutput"]) -> List[Dict]:
        """Format images for provider's API."""
        pass

