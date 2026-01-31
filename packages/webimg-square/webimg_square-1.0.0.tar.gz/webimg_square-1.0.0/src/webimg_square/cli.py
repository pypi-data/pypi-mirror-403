#!/usr/bin/env python3
"""CLI tool to square images for web with smart padding."""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image

# Supported image extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif', '.bmp', '.tiff', '.tif'}
# Extensions that need conversion to PNG (due to write limitations)
CONVERT_TO_PNG = {'.avif'}

DEFAULT_MAX_SIZE = 2500


def detect_background_color(img: Image.Image) -> Tuple[int, ...]:
    """Detect background color by analyzing image corners.

    Samples pixels from all four corners and returns the most common color.
    For images with transparency, returns transparent color.
    """
    width, height = img.size

    # Handle transparency
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        # Convert to RGBA to handle transparency properly
        img_rgba = img.convert('RGBA')
        # Check if corners are transparent
        corners = [
            img_rgba.getpixel((0, 0)),
            img_rgba.getpixel((width - 1, 0)),
            img_rgba.getpixel((0, height - 1)),
            img_rgba.getpixel((width - 1, height - 1)),
        ]
        # If any corner has significant transparency, use transparent
        if any(c[3] < 128 for c in corners):
            return (0, 0, 0, 0)

    # Sample size from each corner (adaptive based on image size)
    sample_size = max(1, min(10, width // 20, height // 20))

    # Convert to numpy array for efficient processing
    img_array = np.array(img.convert('RGB'))

    # Collect corner pixels
    corner_pixels = []
    # Top-left
    corner_pixels.extend(img_array[:sample_size, :sample_size].reshape(-1, 3).tolist())
    # Top-right
    corner_pixels.extend(img_array[:sample_size, -sample_size:].reshape(-1, 3).tolist())
    # Bottom-left
    corner_pixels.extend(img_array[-sample_size:, :sample_size].reshape(-1, 3).tolist())
    # Bottom-right
    corner_pixels.extend(img_array[-sample_size:, -sample_size:].reshape(-1, 3).tolist())

    # Find most common color (simple approach: average with rounding)
    corner_array = np.array(corner_pixels)
    avg_color = np.mean(corner_array, axis=0).astype(int)

    return tuple(avg_color)


def process_image(
    input_path: Path,
    max_size: int = DEFAULT_MAX_SIZE,
    dry_run: bool = False
) -> str:
    """Process a single image: square it and optionally resize.

    Args:
        input_path: Path to the image file
        max_size: Maximum dimension (default 2500)
        dry_run: If True, don't actually modify files

    Returns:
        Status string: 'skipped', 'processed', or 'converted'
    """
    try:
        img = Image.open(input_path)
    except Exception as e:
        return f"error: {e}"

    width, height = img.size

    # Already square - skip
    if width == height:
        return "skipped (already square)"

    # Determine target size (larger dimension, but not exceeding max_size)
    target = max(width, height)
    needs_resize = target > max_size
    if needs_resize:
        target = max_size

    # Determine output format
    output_path = input_path
    suffix = input_path.suffix.lower()
    if suffix in CONVERT_TO_PNG:
        output_path = input_path.with_suffix('.png')

    if dry_run:
        action = "resize + square" if needs_resize else "square"
        if suffix in CONVERT_TO_PNG:
            action += f" + convert to PNG"
        return f"would {action}: {width}x{height} -> {target}x{target}"

    # Detect background color before any transformations
    bg_color = detect_background_color(img)

    # Preserve mode for transparency
    has_transparency = img.mode in ('RGBA', 'LA', 'PA') or (
        img.mode == 'P' and 'transparency' in img.info
    )

    if has_transparency:
        # Convert to RGBA for processing
        img = img.convert('RGBA')
        bg_color = (0, 0, 0, 0)  # Transparent background
    else:
        # Convert to RGB for non-transparent images
        img = img.convert('RGB')
        # Ensure bg_color is RGB tuple
        if len(bg_color) == 4:
            bg_color = bg_color[:3]

    # Resize if needed (maintaining aspect ratio)
    if needs_resize:
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = target
            new_height = int(height * (target / width))
        else:
            new_height = target
            new_width = int(width * (target / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = new_width, new_height

    # Create square canvas
    if has_transparency:
        canvas = Image.new('RGBA', (target, target), bg_color)
    else:
        canvas = Image.new('RGB', (target, target), bg_color)

    # Center the image on canvas
    paste_x = (target - width) // 2
    paste_y = (target - height) // 2

    if has_transparency:
        canvas.paste(img, (paste_x, paste_y), img)  # Use alpha as mask
    else:
        canvas.paste(img, (paste_x, paste_y))

    # Save with appropriate format and quality
    save_kwargs = {}
    output_suffix = output_path.suffix.lower()

    if output_suffix in ('.jpg', '.jpeg'):
        save_kwargs['quality'] = 95
        save_kwargs['optimize'] = True
    elif output_suffix == '.png':
        save_kwargs['optimize'] = True
    elif output_suffix == '.webp':
        save_kwargs['quality'] = 95
        save_kwargs['method'] = 6

    canvas.save(output_path, **save_kwargs)

    # Remove original if converted to different format
    if output_path != input_path:
        input_path.unlink()
        return f"converted: {input_path.name} -> {output_path.name} ({target}x{target})"

    action = "resized + squared" if needs_resize else "squared"
    return f"{action}: {img.size[0]}x{img.size[1]} -> {target}x{target}"


def find_images(path: Path, recursive: bool = True) -> list:
    """Find all supported image files in a path.

    Args:
        path: File or directory path
        recursive: Whether to search recursively in directories

    Returns:
        List of Path objects to image files
    """
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        return []

    if path.is_dir():
        images = []
        pattern = '**/*' if recursive else '*'
        for ext in SUPPORTED_EXTENSIONS:
            images.extend(path.glob(f'{pattern}{ext}'))
            images.extend(path.glob(f'{pattern}{ext.upper()}'))
        return sorted(set(images))

    return []


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='webimg-square',
        description='Square images for web with smart padding. '
                    'Adds padding to make images square, optionally resizes large images.'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        type=Path,
        help='Image files or directories to process'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=DEFAULT_MAX_SIZE,
        help=f'Maximum dimension in pixels (default: {DEFAULT_MAX_SIZE})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually processing'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not process directories recursively'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output for each file'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    parsed = parser.parse_args(args)

    # Collect all images to process
    all_images = []
    for path in parsed.paths:
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            continue
        all_images.extend(find_images(path, recursive=not parsed.no_recursive))

    if not all_images:
        print("No supported images found.", file=sys.stderr)
        return 1

    # Process images
    stats = {'processed': 0, 'skipped': 0, 'errors': 0, 'converted': 0}

    for img_path in all_images:
        result = process_image(img_path, max_size=parsed.max_size, dry_run=parsed.dry_run)

        if parsed.verbose or parsed.dry_run:
            print(f"{img_path}: {result}")

        if result.startswith('skipped'):
            stats['skipped'] += 1
        elif result.startswith('error'):
            stats['errors'] += 1
            if not parsed.verbose:
                print(f"{img_path}: {result}", file=sys.stderr)
        elif result.startswith('converted'):
            stats['converted'] += 1
            stats['processed'] += 1
        elif result.startswith('would'):
            stats['processed'] += 1
        else:
            stats['processed'] += 1

    # Summary
    total = len(all_images)
    action = "Would process" if parsed.dry_run else "Processed"
    print(f"\n{action} {stats['processed']}/{total} images "
          f"({stats['skipped']} skipped, {stats['converted']} converted, {stats['errors']} errors)")

    return 0 if stats['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
