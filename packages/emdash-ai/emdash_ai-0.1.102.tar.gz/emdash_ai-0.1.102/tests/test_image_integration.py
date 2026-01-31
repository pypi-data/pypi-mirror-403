#!/usr/bin/env python3
"""Integration test for image paste with agent runner.

Uses pypng for pure-Python PNG handling (no Pillow dependency).
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import png

from emdash.agent.providers.base import ImageContent
from emdash.agent.providers.openai_provider import OpenAIProvider
from emdash.agent.providers.models import ChatModel
from emdash.agent.runner import AgentRunner

from emdash.utils.logger import log


def create_test_image(color='red', size=(200, 200)):
    """Create a test image and return bytes.

    Args:
        color: Color name ('red', 'green', 'blue', 'orange', 'purple')
        size: Tuple of (width, height)

    Returns:
        PNG image bytes
    """
    # Map color names to RGB
    color_map = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
    }
    r, g, b = color_map.get(color, (255, 0, 0))
    width, height = size

    # Create rows with RGB values
    row = [r, g, b] * width
    rows = [row for _ in range(height)]

    output = io.BytesIO()
    writer = png.Writer(width=width, height=height, greyscale=False, alpha=False)
    writer.write(output, rows)
    return output.getvalue()


def test_image_content_to_provider_format():
    """Test that ImageContent formats correctly for LLM API."""
    print("Testing ImageContent -> LLM format...")

    # Create test image
    image_data = create_test_image(color='blue', size=(150, 150))

    # Create ImageContent
    img_content = ImageContent(image_data=image_data, format="png")

    # Test base64_url property
    url = img_content.base64_url
    assert url.startswith("data:image/png;base64,")
    print(f"  ✓ base64_url: {url[:50]}...")

    # Test encoding manually
    import base64
    encoded = base64.b64encode(image_data).decode("utf-8")
    manual_url = f"data:image/png;base64,{encoded}"
    assert url == manual_url
    print("  ✓ base64_url matches manual encoding")


def test_provider_supports_vision():
    """Test provider vision support detection."""
    print("Testing provider vision support...")

    # Test with vision model (Claude Sonnet 4)
    provider = OpenAIProvider(ChatModel.ANTHROPIC_CLAUDE_SONNET_4)
    assert provider.supports_vision() == True
    print(f"  ✓ Sonnet 4 supports vision: {provider.supports_vision()}")

    # Test with non-vision model (MiniMax M2P1)
    provider = OpenAIProvider(ChatModel.FIREWORKS_MINIMAX_M2P1)
    assert provider.supports_vision() == False
    print(f"  ✓ MiniMax M2P1 supports vision: {provider.supports_vision()}")


def test_format_content_with_images():
    """Test content formatting with images."""
    print("Testing content formatting with images...")

    # Create test images
    images = [
        ImageContent(image_data=create_test_image(color='red'), format="png"),
        ImageContent(image_data=create_test_image(color='green'), format="png"),
    ]

    text = "What's in this image?"

    # Test with vision provider
    vision_provider = OpenAIProvider(ChatModel.ANTHROPIC_CLAUDE_SONNET_4)
    content = vision_provider._format_content_with_images(text, images)

    assert isinstance(content, list)
    assert len(content) == 3  # 1 text + 2 images
    assert content[0]["type"] == "text"
    assert content[0]["text"] == text
    assert content[1]["type"] == "image_url"
    assert content[2]["type"] == "image_url"
    print(f"  ✓ Vision content: {len(content)} blocks (1 text + {len(images)} images)")

    # Test with non-vision provider
    non_vision_provider = OpenAIProvider(ChatModel.FIREWORKS_MINIMAX_M2P1)
    content = non_vision_provider._format_content_with_images(text, images)

    assert isinstance(content, str)  # Should be text only for non-vision
    assert content == text  # Images stripped
    print(f"  ✓ Non-vision content: text only (images stripped)")


def test_runner_with_images():
    """Test agent runner with images."""
    print("Testing agent runner with images...")

    # Create test image
    image_data = create_test_image(color='orange', size=(100, 100))
    images = [ImageContent(image_data=image_data, format="png")]

    # Create runner (will fail without API key, but that's ok for this test)
    runner = AgentRunner(model="haiku", verbose=False, max_iterations=1)

    # Check initial state
    assert runner._pending_images == []
    print("  ✓ Initial state: no pending images")

    # Add images
    runner.add_images(images)
    assert len(runner._pending_images) == 1
    print("  ✓ add_images works")

    # Clear images
    runner.clear_images()
    assert runner._pending_images == []
    print("  ✓ clear_images works")

    # Check vision support detection
    supports_vision, msg = runner._check_vision_support()
    # MiniMax doesn't support vision, so should warn
    assert supports_vision == False or "vision" in msg.lower() or msg == ""
    print(f"  ✓ Vision check works: {msg[:50] if msg else 'No warning (non-vision model)'}...")


def test_token_estimation_with_images():
    """Test token estimation includes images."""
    print("Testing token estimation with images...")

    # Create runner
    runner = AgentRunner(model="haiku", verbose=False)

    # Create large test image
    large_image = ImageContent(
        image_data=create_test_image(color='purple', size=(1000, 1000)),
        format="png"
    )

    # Test single image token estimate
    tokens = runner._estimate_image_tokens(large_image)
    assert tokens > 500  # Should be more than base due to size
    print(f"  ✓ Large image tokens: {tokens}")

    # Test multiple images
    images = [large_image, large_image, large_image]
    total = sum(runner._estimate_image_tokens(img) for img in images)
    print(f"  ✓ 3 images: ~{total} tokens total")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Image Paste Integration Tests (pypng)")
    print("=" * 60)
    print()

    try:
        test_image_content_to_provider_format()
        print()

        test_provider_supports_vision()
        print()

        test_format_content_with_images()
        print()

        test_runner_with_images()
        print()

        test_token_estimation_with_images()
        print()

        print("=" * 60)
        print("All integration tests passed! ✓")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
