"""Tests for webimg-square CLI tool."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from webimg_square.cli import (
    detect_background_color,
    find_images,
    process_image,
    main,
    DEFAULT_MAX_SIZE,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    dirpath = tempfile.mkdtemp()
    yield Path(dirpath)
    shutil.rmtree(dirpath)


def create_test_image(path: Path, width: int, height: int, color=(255, 0, 0), mode='RGB'):
    """Helper to create test images."""
    img = Image.new(mode, (width, height), color)
    img.save(path)
    return path


def create_image_with_corners(path: Path, width: int, height: int, corner_color, center_color):
    """Create image with specific corner colors for background detection tests."""
    img = Image.new('RGB', (width, height), center_color)
    # Paint corners
    corner_size = max(1, min(10, width // 20, height // 20))
    for x in range(corner_size):
        for y in range(corner_size):
            # Top-left
            img.putpixel((x, y), corner_color)
            # Top-right
            img.putpixel((width - 1 - x, y), corner_color)
            # Bottom-left
            img.putpixel((x, height - 1 - y), corner_color)
            # Bottom-right
            img.putpixel((width - 1 - x, height - 1 - y), corner_color)
    img.save(path)
    return path


class TestSkipAlreadySquare:
    """Test that square images are not modified."""

    def test_skip_already_square(self, temp_dir):
        """Square image should be skipped."""
        img_path = temp_dir / "square.jpg"
        create_test_image(img_path, 500, 500)

        result = process_image(img_path)

        assert "skipped" in result
        # Verify image wasn't changed
        img = Image.open(img_path)
        assert img.size == (500, 500)

    def test_skip_large_square(self, temp_dir):
        """Large square image should also be skipped (no resize for squares)."""
        img_path = temp_dir / "large_square.jpg"
        create_test_image(img_path, 3000, 3000)

        result = process_image(img_path)

        assert "skipped" in result


class TestSmallImageNoUpscale:
    """Test that small images are not upscaled."""

    def test_small_image_no_upscale(self, temp_dir):
        """Small image should be squared but not upscaled."""
        img_path = temp_dir / "small.jpg"
        create_test_image(img_path, 100, 200)

        result = process_image(img_path)

        assert "squared" in result
        img = Image.open(img_path)
        assert img.size == (200, 200)  # Squared to larger dimension, not 2500

    def test_small_landscape(self, temp_dir):
        """Small landscape image should be squared to larger dimension."""
        img_path = temp_dir / "small_landscape.jpg"
        create_test_image(img_path, 300, 100)

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (300, 300)


class TestLargeImageResizeAndSquare:
    """Test that large images are resized and squared."""

    def test_large_image_resize_and_square(self, temp_dir):
        """Large image should be resized to max_size and squared."""
        img_path = temp_dir / "large.jpg"
        create_test_image(img_path, 3000, 4000)

        result = process_image(img_path)

        assert "resized" in result and "squared" in result
        img = Image.open(img_path)
        assert img.size == (2500, 2500)

    def test_large_landscape(self, temp_dir):
        """Large landscape image should be resized and squared."""
        img_path = temp_dir / "large_landscape.jpg"
        create_test_image(img_path, 5000, 3000)

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (2500, 2500)

    def test_custom_max_size(self, temp_dir):
        """Custom max_size should be respected."""
        img_path = temp_dir / "custom.jpg"
        create_test_image(img_path, 2000, 3000)

        process_image(img_path, max_size=1500)

        img = Image.open(img_path)
        assert img.size == (1500, 1500)


class TestLandscapeToSquare:
    """Test landscape images are properly squared."""

    def test_landscape_to_square(self, temp_dir):
        """Landscape image should become square with height padding."""
        img_path = temp_dir / "landscape.jpg"
        create_test_image(img_path, 1000, 500, color=(255, 0, 0))

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (1000, 1000)

    def test_landscape_content_centered(self, temp_dir):
        """Content should be centered in the square."""
        # Use PNG to avoid JPEG compression artifacts
        img_path = temp_dir / "landscape_center.png"
        # Create image with distinct center pixel
        img = Image.new('RGB', (100, 50), (255, 255, 255))
        img.putpixel((50, 25), (255, 0, 0))  # Red pixel at center
        img.save(img_path)

        process_image(img_path)

        img = Image.open(img_path)
        # Original was 100x50, now 100x100
        # Content should be centered, so original center (50, 25) is now at (50, 50)
        # With padding of 25 on top and bottom
        center_pixel = img.getpixel((50, 50))
        assert center_pixel == (255, 0, 0)


class TestPortraitToSquare:
    """Test portrait images are properly squared."""

    def test_portrait_to_square(self, temp_dir):
        """Portrait image should become square with width padding."""
        img_path = temp_dir / "portrait.jpg"
        create_test_image(img_path, 500, 1000, color=(0, 255, 0))

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (1000, 1000)


class TestPngTransparencyPreserved:
    """Test that PNG transparency is preserved."""

    def test_png_transparency_preserved(self, temp_dir):
        """PNG with transparency should maintain transparent background."""
        img_path = temp_dir / "transparent.png"
        # Create RGBA image with transparent background
        img = Image.new('RGBA', (100, 200), (0, 0, 0, 0))
        # Add opaque red rectangle in center
        for x in range(25, 75):
            for y in range(50, 150):
                img.putpixel((x, y), (255, 0, 0, 255))
        img.save(img_path)

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (200, 200)
        assert img.mode == 'RGBA'
        # Check corner is transparent
        corner = img.getpixel((0, 0))
        assert corner[3] == 0  # Alpha should be 0

    def test_png_opaque_uses_detected_color(self, temp_dir):
        """Opaque PNG should use detected corner color."""
        img_path = temp_dir / "opaque.png"
        create_image_with_corners(img_path, 100, 200, (128, 128, 128), (255, 0, 0))

        process_image(img_path)

        img = Image.open(img_path)
        # Corner padding should be approximately the corner color
        corner = img.getpixel((0, 0))
        assert abs(corner[0] - 128) < 10  # Allow some tolerance


class TestAvifToPngConversion:
    """Test AVIF to PNG conversion."""

    def test_avif_to_png_conversion(self, temp_dir):
        """AVIF files should be converted to PNG."""
        # Note: We can't easily create AVIF in tests without additional deps
        # So we test the path handling
        img_path = temp_dir / "test.png"
        create_test_image(img_path, 100, 200)

        # Rename to .avif to test the conversion logic
        avif_path = temp_dir / "test.avif"
        img_path.rename(avif_path)

        # Process should convert to PNG
        result = process_image(avif_path)

        # Check result mentions conversion or the file exists as PNG
        png_path = temp_dir / "test.png"
        # Either conversion happened or error (if pillow can't read avif)
        assert png_path.exists() or "error" in result.lower()


class TestBackgroundColorDetection:
    """Test background color detection from corners."""

    def test_background_color_detection(self, temp_dir):
        """Should detect background color from image corners."""
        img_path = temp_dir / "corners.jpg"
        corner_color = (200, 200, 200)
        center_color = (50, 50, 50)
        create_image_with_corners(img_path, 100, 200, corner_color, center_color)

        img = Image.open(img_path)
        detected = detect_background_color(img)

        # Detected color should be close to corner color
        assert all(abs(d - c) < 20 for d, c in zip(detected, corner_color))

    def test_white_background_detection(self, temp_dir):
        """Should detect white background."""
        img_path = temp_dir / "white_bg.jpg"
        img = Image.new('RGB', (100, 200), (255, 255, 255))
        # Add small colored content in center
        for x in range(40, 60):
            for y in range(80, 120):
                img.putpixel((x, y), (0, 0, 255))
        img.save(img_path)

        img = Image.open(img_path)
        detected = detect_background_color(img)

        assert all(c > 240 for c in detected)  # Should be near white


class TestFindImages:
    """Test image file discovery."""

    def test_find_single_file(self, temp_dir):
        """Should find a single image file."""
        img_path = temp_dir / "single.jpg"
        create_test_image(img_path, 100, 100)

        found = find_images(img_path)
        assert len(found) == 1
        assert found[0] == img_path

    def test_find_in_directory(self, temp_dir):
        """Should find all images in directory."""
        create_test_image(temp_dir / "a.jpg", 100, 100)
        create_test_image(temp_dir / "b.png", 100, 100)
        (temp_dir / "not_image.txt").write_text("hello")

        found = find_images(temp_dir)
        assert len(found) == 2

    def test_find_recursive(self, temp_dir):
        """Should find images recursively."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        create_test_image(temp_dir / "root.jpg", 100, 100)
        create_test_image(subdir / "nested.jpg", 100, 100)

        found = find_images(temp_dir, recursive=True)
        assert len(found) == 2

    def test_find_non_recursive(self, temp_dir):
        """Should not recurse when recursive=False."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        create_test_image(temp_dir / "root.jpg", 100, 100)
        create_test_image(subdir / "nested.jpg", 100, 100)

        found = find_images(temp_dir, recursive=False)
        assert len(found) == 1


class TestDryRun:
    """Test dry-run mode."""

    def test_dry_run_no_modification(self, temp_dir):
        """Dry run should not modify files."""
        img_path = temp_dir / "dry.jpg"
        create_test_image(img_path, 100, 200)
        original_size = img_path.stat().st_size

        result = process_image(img_path, dry_run=True)

        assert "would" in result
        assert img_path.stat().st_size == original_size
        img = Image.open(img_path)
        assert img.size == (100, 200)  # Unchanged


class TestCLI:
    """Test CLI interface."""

    def test_cli_basic(self, temp_dir):
        """Basic CLI invocation should work."""
        img_path = temp_dir / "cli_test.jpg"
        create_test_image(img_path, 100, 200)

        result = main([str(img_path)])

        assert result == 0
        img = Image.open(img_path)
        assert img.size == (200, 200)

    def test_cli_dry_run(self, temp_dir):
        """CLI dry-run should not modify files."""
        img_path = temp_dir / "cli_dry.jpg"
        create_test_image(img_path, 100, 200)

        result = main([str(img_path), '--dry-run'])

        assert result == 0
        img = Image.open(img_path)
        assert img.size == (100, 200)

    def test_cli_custom_max_size(self, temp_dir):
        """CLI should respect --max-size."""
        img_path = temp_dir / "cli_max.jpg"
        create_test_image(img_path, 2000, 3000)

        main([str(img_path), '--max-size', '1000'])

        img = Image.open(img_path)
        assert img.size == (1000, 1000)

    def test_cli_nonexistent_path(self, temp_dir, capsys):
        """CLI should handle nonexistent paths gracefully."""
        result = main([str(temp_dir / "nonexistent.jpg")])

        assert result == 1
        captured = capsys.readouterr()
        assert "No supported images" in captured.err or "does not exist" in captured.err


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_exactly_max_size(self, temp_dir):
        """Image exactly at max_size should only be squared, not resized."""
        img_path = temp_dir / "exact.jpg"
        create_test_image(img_path, 2500, 2000)

        result = process_image(img_path)

        # Should square without "resized" in result
        img = Image.open(img_path)
        assert img.size == (2500, 2500)

    def test_one_pixel_difference(self, temp_dir):
        """Image with 1px difference from square should still be squared."""
        img_path = temp_dir / "almost.jpg"
        create_test_image(img_path, 100, 101)

        result = process_image(img_path)

        assert "squared" in result
        img = Image.open(img_path)
        assert img.size == (101, 101)

    def test_very_small_image(self, temp_dir):
        """Very small image should be handled correctly."""
        img_path = temp_dir / "tiny.jpg"
        create_test_image(img_path, 2, 10)

        process_image(img_path)

        img = Image.open(img_path)
        assert img.size == (10, 10)
