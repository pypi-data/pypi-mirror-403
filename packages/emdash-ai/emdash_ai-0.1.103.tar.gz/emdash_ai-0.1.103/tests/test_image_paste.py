#!/usr/bin/env python3
"""Test script for image paste functionality.

Uses pypng for pure-Python PNG handling (no Pillow dependency).
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'packages/core'))

import png

from emdash_core.utils.image import (
    is_clipboard_image_available,
    encode_image_to_base64,
    encode_image_for_llm,
    get_image_info,
    estimate_image_tokens,
    read_and_prepare_image,
    ClipboardImageError,
    ImageFormat,
)


def create_test_png(width: int, height: int, color: tuple = (255, 0, 0)) -> bytes:
    """Create a simple test PNG image.

    Args:
        width: Image width
        height: Image height
        color: RGB color tuple (default red)

    Returns:
        PNG image bytes
    """
    r, g, b = color
    # Create rows with RGB values
    row = [r, g, b] * width
    rows = [row for _ in range(height)]

    output = io.BytesIO()
    writer = png.Writer(width=width, height=height, greyscale=False, alpha=False)
    writer.write(output, rows)
    return output.getvalue()


def test_image_utils():
    """Test image utility functions."""
    print("Testing image utilities...")

    # Create test image (100x100 red)
    test_image = create_test_png(100, 100, (255, 0, 0))

    # Test get_image_info
    info = get_image_info(test_image)
    assert info["width"] == 100
    assert info["height"] == 100
    assert info["format"] == "PNG"
    print(f"  ✓ get_image_info: {info}")

    # Test estimate_image_tokens
    tokens = estimate_image_tokens(test_image)
    assert tokens >= 500  # Base tokens + size factor
    print(f"  ✓ estimate_image_tokens: {tokens}")


def test_image_encoding():
    """Test image encoding functions."""
    print("Testing image encoding...")

    # Create test image (100x100 yellow)
    test_image = create_test_png(100, 100, (255, 255, 0))

    # Test encode_image_to_base64
    b64 = encode_image_to_base64(test_image)
    assert b64.startswith("data:image/png;base64,")
    assert len(b64) > 100
    print(f"  ✓ encode_image_to_base64: {len(b64)} chars")

    # Test encode_image_for_llm
    llm_format = encode_image_for_llm(test_image)
    assert llm_format["type"] == "image_url"
    assert "url" in llm_format["image_url"]
    print(f"  ✓ encode_image_for_llm: {list(llm_format.keys())}")


def test_clipboard_detection():
    """Test clipboard detection (will show False on test systems)."""
    print("Testing clipboard detection...")

    available = is_clipboard_image_available()
    print(f"  Clipboard has image: {available}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Image Paste Functionality Tests (pypng)")
    print("=" * 60)
    print()

    try:
        test_image_utils()
        print()

        test_image_encoding()
        print()

        test_clipboard_detection()
        print()

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
