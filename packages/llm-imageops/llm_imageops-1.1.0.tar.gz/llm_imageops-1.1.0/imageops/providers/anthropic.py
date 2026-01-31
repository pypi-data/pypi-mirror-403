"""Anthropic provider implementation."""

from typing import List, Dict
from .base import BaseProvider, ProviderConfig


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider with specific limits."""
    
    name = "anthropic"
    
    config = ProviderConfig(
        max_width=8000,
        max_height=8000,
        max_size_mb=3.35,  # Accounts for 33% base64 overhead
        max_base64_size_mb=5.0,
        max_images_per_call=20,
        supported_formats=["jpeg", "png", "gif", "webp"]
    )
    
    def needs_processing(self, metadata) -> bool:
        """Check if image needs processing."""
        return (
            metadata.width > self.config.max_width
            or metadata.height > self.config.max_height
            or metadata.size_mb > self.config.max_size_mb
        )
    
    def format_for_api(self, images: List) -> List[Dict]:
        """Format images for Anthropic API."""
        content = []
        for img in images:
            if img.format == "base64":
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img.media_type,
                        "data": img.data
                    }
                })
            else:  # file format
                # For file format, we'd typically need to read and encode
                # For now, just include the path info
                content.append({
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": f"file://{img.data}"
                    }
                })
        return content

