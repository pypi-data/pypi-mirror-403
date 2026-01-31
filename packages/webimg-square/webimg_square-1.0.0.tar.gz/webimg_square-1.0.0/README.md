# webimg-square

CLI tool to square images for web with smart padding.

## Features

- **Smart squaring**: Adds padding to make images square using the larger dimension
- **Auto background detection**: Analyzes image corners to determine padding color
- **Intelligent resizing**: Only shrinks images larger than 2500px (configurable)
- **Transparency support**: Preserves PNG transparency with transparent padding
- **AVIF conversion**: Automatically converts AVIF files to PNG
- **Batch processing**: Process entire directories recursively
- **Dry-run mode**: Preview changes before applying

## Installation

```bash
pip install webimg-square
```

## Usage

### Basic usage

```bash
# Process a single image
webimg-square image.jpg

# Process a directory recursively
webimg-square ./photos/

# Process multiple paths
webimg-square image1.jpg image2.png ./more-photos/
```

### Options

```bash
# Custom maximum size (default: 2500)
webimg-square --max-size 1500 ./photos/

# Preview changes without modifying files
webimg-square --dry-run ./photos/

# Non-recursive directory processing
webimg-square --no-recursive ./photos/

# Verbose output
webimg-square -v ./photos/
```

## Processing Rules

1. **Already square images**: Skipped (no changes)
2. **Non-square images**: Padded to square using the larger dimension
3. **Large images (>2500px)**: Resized to 2500px max, then squared
4. **Small images (<2500px)**: Only squared, never upscaled
5. **Transparent PNGs**: Use transparent padding
6. **AVIF files**: Converted to PNG

## Supported Formats

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| JPEG | ✅ | ✅ | Quality 95 |
| PNG | ✅ | ✅ | Transparency preserved |
| WebP | ✅ | ✅ | Quality 95 |
| AVIF | ✅ | → PNG | Converted to PNG |
| GIF | ✅ | ✅ | First frame only |
| BMP | ✅ | ✅ | |
| TIFF | ✅ | ✅ | |

## Examples

### Landscape image (1000x500)
- Result: 1000x1000 with 250px padding top and bottom

### Portrait image (500x1000)
- Result: 1000x1000 with 250px padding left and right

### Large image (3000x4000)
- Resized to 1875x2500 (maintaining aspect ratio)
- Result: 2500x2500 with padding

### Small image (100x200)
- Result: 200x200 (not upscaled to 2500)

## Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=webimg_square
```

## License

MIT
