# ImageOps: Production-Grade Image Preprocessing for LLMs

**Simple, fast, and production-ready async image preprocessing for LLM APIs.**

> **PyPI Package**: `llm-imageops` (import as `imageops`)

ImageOps handles all the complexity of preparing images for LLM providers like Anthropic Claude, automatically handling resizing, compression, slicing, and encoding based on each provider's limits.

## 🚀 Features

- **Zero Configuration** - Works out of the box with sensible defaults
- **100% Async** - Built for modern async Python applications
- **Production Ready** - Comprehensive error handling, security, resource limits
- **Provider Agnostic** - Easy to add support for new LLM providers
- **Type Safe** - Full type hints with Pydantic validation
- **Edge Case Handling** - Animated GIFs, panoramas, EXIF orientation, alpha channels
- **Smart Optimization** - Only processes when necessary based on provider limits
- **Resource Safe** - Automatic cleanup with async context managers

## 📦 Installation

```bash
pip install llm-imageops
```

Import as:
```python
import imageops  # Module name stays 'imageops'
```

Or install from source:

```bash
git clone https://github.com/yourusername/imageops.git
cd imageops
pip install -e .
```

## 🎯 Quick Start

### Simple One-Liner

```python
import imageops
import asyncio

async def main():
    # Process image for Anthropic Claude
    result = await imageops.process("image.jpg", provider="anthropic")
    
    # Use in your LLM API call
    messages = [
        {
            "role": "user",
            "content": result.to_anthropic_format() + [
                {"type": "text", "text": "What's in this image?"}
            ]
        }
    ]

asyncio.run(main())
```

### Process from URL

```python
result = await imageops.process(
    "https://example.com/image.jpg",
    provider="anthropic"
)
```

### Get File Paths Instead of Base64

```python
result = await imageops.process(
    "large_image.jpg",
    provider="anthropic",
    output_format="file"  # Returns processed file paths
)
```

### With Progress Callback

```python
async def progress_callback(step: str, progress: float):
    print(f"{step}: {progress:.1%}")

result = await imageops.process(
    "huge_image.jpg",
    provider="anthropic",
    progress_callback=progress_callback
)
```

### Batch Processing

```python
results = await imageops.process_batch(
    ["img1.jpg", "img2.jpg", "img3.jpg"],
    provider="anthropic"
)

for result in results:
    print(f"Processed {result.slice_count} image(s)")
```

## 🔧 Advanced Usage

### Custom Configuration

```python
import imageops

config = imageops.ImageOpsConfig(
    max_image_size_mb=50,      # Reject images > 50MB
    max_batch_size=20,          # Limit batch processing
    enable_logging=True,
    log_level="DEBUG",
    default_quality=85          # JPEG quality
)

async with imageops.ImageProcessor(provider="anthropic", config=config) as processor:
    result1 = await processor.process("img1.jpg")
    result2 = await processor.process("img2.jpg", timeout=60.0)
# Automatic cleanup
```

### Custom Provider

```python
from imageops.providers import BaseProvider, ProviderConfig, register_provider

class MyCustomProvider(BaseProvider):
    name = "my_llm"
    
    config = ProviderConfig(
        max_width=4096,
        max_height=4096,
        max_size_mb=5.0,
        max_base64_size_mb=10.0,
        max_images_per_call=10,
        supported_formats=["jpeg", "png"]
    )
    
    def needs_processing(self, metadata) -> bool:
        return metadata.width > 4096 or metadata.size_mb > 5.0
    
    def format_for_api(self, images):
        # Return your provider's format
        pass

# Register it
register_provider("my_llm", MyCustomProvider())

# Use it
result = await imageops.process("image.jpg", provider="my_llm")
```

## 📊 What It Does

ImageOps automatically handles:

### Resizing
- Reduces width/height to fit provider limits
- Maintains aspect ratio
- Uses high-quality INTER_AREA interpolation

### Slicing
- Splits very tall images into vertical segments
- Splits very wide panoramas into horizontal slices
- Processes each segment independently

### Compression
- Iterative quality reduction (95 → 10)
- Falls back to dimension reduction if needed
- Ensures file size stays under limits

### Edge Cases
- **Animated GIFs** - Extracts first frame
- **EXIF Orientation** - Auto-rotates images
- **Alpha Channels** - Converts RGBA → RGB on white background
- **Wide Panoramas** - Horizontal slicing for 50000x1000 images
- **Corrupted Images** - Clear error messages

## 🔒 Security

- **Path Traversal Protection** - Validates file paths
- **File Size Limits** - Rejects images > 100MB by default
- **Dimension Limits** - Maximum 100,000px per side
- **Format Whitelist** - Only allows safe formats
- **URL Validation** - Proper URL format checking

## 📈 Result Format

```python
result = await imageops.process("image.jpg")

# Result attributes
result.success              # bool
result.images               # List[ImageOutput]
result.output_format        # "base64" or "file"
result.was_sliced           # bool
result.slice_count          # int
result.processing_time_ms   # float
result.provider             # str
result.original_metadata    # Dict

# Each image has THREE ways to access base64 + media type:

# 1. Separate fields (most flexible)
for img in result.images:
    base64_data = img.data          # Just the base64 string
    media_type = img.media_type     # e.g., "image/jpeg"
    # Combine as needed: f"data:{media_type};base64,{base64_data}"

# 2. Data URI with prefix (convenience method)
for img in result.images:
    data_uri = img.to_data_uri()    # "data:image/jpeg;base64,<data>"

# 3. Anthropic API format (ready-to-use)
content = result.to_anthropic_format()
# Returns Anthropic-formatted content blocks with media_type included

# Other attributes
for img in result.images:
    img.format              # "base64" or "file"
    img.width               # int
    img.height              # int
    img.size_bytes          # int
    img.was_compressed      # bool
    img.compression_quality # Optional[int]

# Convenience methods
result.to_anthropic_format()  # Ready for Anthropic API
await result.cleanup()         # Manual cleanup if needed
```

## ⚙️ Configuration Options

```python
ImageOpsConfig(
    # Resource Limits
    max_image_size_mb=100.0,        # Max input image size
    max_dimension=100000,            # Max width/height
    max_batch_size=50,               # Max images per batch
    
    # Performance
    max_concurrent_ops=5,            # Concurrent operations
    download_timeout=10.0,           # Download timeout (seconds)
    processing_timeout=300.0,        # Processing timeout (seconds)
    
    # Retry Logic
    max_download_retries=3,          # Download retry attempts
    retry_backoff_factor=2.0,        # Exponential backoff
    
    # Compression
    default_quality=90,              # JPEG quality (1-100)
    quality_step=5,                  # Quality reduction step
    min_quality=10,                  # Minimum quality
    
    # Logging
    enable_logging=True,
    log_level="INFO",                # DEBUG, INFO, WARNING, ERROR
    log_file=None,                   # Optional log file
    
    # Security
    validate_paths=True,             # Path traversal protection
    allowed_formats=[".jpg", ".jpeg", ".png", ".gif", ".webp"]
)
```

## 🧪 Testing

The package includes comprehensive tests:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=imageops --cov-report=html

# Run specific test categories
pytest tests/test_operations.py
pytest tests/test_edge_cases.py
```

## 🐛 Troubleshooting

### Image Download Fails

```python
from imageops.exceptions import ImageDownloadError

try:
    result = await imageops.process("https://example.com/image.jpg")
except ImageDownloadError as e:
    print(f"Download failed: {e}")
    # Handle fallback
```

### Image Too Large

```python
from imageops.exceptions import ImageTooLargeError

try:
    result = await imageops.process("huge.jpg")
except ImageTooLargeError as e:
    print(f"Image exceeds limit: {e}")
```

### Processing Timeout

```python
from imageops.exceptions import TimeoutError

try:
    result = await imageops.process("image.jpg", timeout=30.0)
except TimeoutError as e:
    print(f"Processing took too long: {e}")
```

### Enable Debug Logging

```python
config = imageops.ImageOpsConfig(
    enable_logging=True,
    log_level="DEBUG",
    log_file="imageops.log"
)

processor = imageops.ImageProcessor(config=config)
```

## 🏗️ Architecture

```
imageops/
├── core/           # Main processor and result types
├── providers/      # Provider implementations
├── operations/     # Image operations (resize, slice, compress, encode)
├── strategies/     # Processing strategies
├── utils/          # Utilities (validation, cleanup, logging, metadata)
├── config.py       # Configuration
└── exceptions.py   # Exception hierarchy
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built with best practices from:
- [httpx](https://www.python-httpx.org/) - Async HTTP patterns
- [aiofiles](https://github.com/Tinche/aiofiles) - Async file I/O
- [pydantic](https://pydantic-docs.helpmanual.io/) - Type validation
- [opencv-python](https://github.com/opencv/opencv-python) - Image processing

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/imageops/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/imageops/discussions)

---

Made with ❤️ for the LLM community
