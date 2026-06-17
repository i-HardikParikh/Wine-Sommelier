import io
from typing import Optional
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
from loguru import logger


def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhance image quality before OCR for better accuracy."""
    # Convert to grayscale
    image = image.convert("L")
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)
    # Resize if too small (Tesseract works better with larger images)
    width, height = image.size
    if width < 1000:
        scale = 1000 / width
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    return image


def extract_text_from_image(image: Image.Image, lang: str = "eng") -> str:
    """
    Run Tesseract OCR on a PIL Image.
    Returns extracted text string.
    """
    try:
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(
            processed,
            lang=lang,
            config="--psm 6 --oem 3",  # Assume uniform block of text, LSTM engine
        )
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""


def extract_text_from_bytes(image_bytes: bytes, lang: str = "eng") -> str:
    """Run OCR on raw image bytes."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return extract_text_from_image(image, lang=lang)
    except Exception as e:
        logger.warning(f"OCR from bytes failed: {e}")
        return ""


def ocr_is_available() -> bool:
    """Check if Tesseract is installed and reachable."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False
