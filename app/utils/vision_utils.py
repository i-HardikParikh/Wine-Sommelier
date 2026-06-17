import base64
import io
from PIL import Image
from loguru import logger

from app.utils.llm_client import get_llm_client

VISION_PROMPT = """You are an expert wine analyst and sommelier.
When analyzing images, extract all relevant wine-related information including:
- Wine names, vintages, regions, varietals
- Tasting notes, flavor profiles, color descriptions
- Food pairing suggestions
- Price points, ratings, scores
- Producer/chateau information
- Any tables, charts, or structured data about wines

Return your analysis in clear, structured text that preserves all key facts."""


def image_to_base64(image: Image.Image, fmt: str = "JPEG") -> str:
    """Convert PIL image to base64 string."""
    buffer = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def bytes_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_image(
    image: Image.Image,
    prompt: str = "Extract all wine-related information from this image.",
    detail: str = "high",
) -> str:
    """
    Send image to GPT-4o Vision (OpenAI, primary). Automatically falls back to
    Groq's Llama-4 Scout vision model if OpenAI is unavailable or fails.
    """
    try:
        b64 = image_to_base64(image)
        client = get_llm_client()
        full_prompt = f"{VISION_PROMPT}\n\n{prompt}"
        return client.vision(image_b64=b64, prompt=full_prompt, max_tokens=1500)
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return ""


def analyze_image_bytes(image_bytes: bytes, prompt: str = "Extract all wine-related information.") -> str:
    """Analyze raw image bytes with the configured vision model."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return analyze_image(image, prompt=prompt)
    except Exception as e:
        logger.error(f"Vision analysis from bytes failed: {e}")
        return ""
