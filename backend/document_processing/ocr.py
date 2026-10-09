import io
import logging
import os
import shutil
from functools import lru_cache
from typing import List, Union

import pymupdf
import pytesseract
from PIL import Image

from backend.config import settings

logger = logging.getLogger("propverify.ocr")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}


class OCRProcessingError(RuntimeError):
    """Raised when scanned content cannot be transcribed by an available engine."""


def _tesseract_path() -> str | None:
    configured = settings.TESSERACT_CMD
    if configured and os.path.isfile(configured):
        return configured
    return shutil.which("tesseract")


def file_to_images(file_input: Union[str, bytes], filename: str = "") -> List[Image.Image]:
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    if ext in IMAGE_EXTENSIONS:
        source = file_input if isinstance(file_input, str) else io.BytesIO(file_input)
        with Image.open(source) as image:
            return [image.convert("RGB")]

    if isinstance(file_input, str):
        doc = pymupdf.open(file_input)
    else:
        doc = pymupdf.open(stream=file_input, filetype=ext.lstrip(".") or "pdf")
    try:
        return [Image.open(io.BytesIO(page.get_pixmap(dpi=200).tobytes("png"))).convert("RGB") for page in doc]
    finally:
        doc.close()


@lru_cache(maxsize=1)
def _easyocr_reader():
    import easyocr
    # EasyOCR downloads only its English model weights on first scanned upload.
    # A caller can disable that fetch for offline environments with
    # EASYOCR_DOWNLOAD_MODELS=false; the OCRProcessingError remains actionable.
    download_enabled = os.getenv("EASYOCR_DOWNLOAD_MODELS", "true").strip().lower() not in {"0", "false", "no"}
    return easyocr.Reader(["en"], gpu=False, download_enabled=download_enabled, verbose=False)


def perform_ocr(file_input: Union[str, bytes], filename: str = "") -> str:
    try:
        images = file_to_images(file_input, filename)
    except Exception as error:
        logger.warning("OCR image preparation failed (%s)", type(error).__name__)
        raise OCRProcessingError("The scanned document could not be rendered for English OCR.") from None

    if not images:
        raise OCRProcessingError("The scanned document has no readable pages for OCR.")

    tesseract = _tesseract_path()
    if tesseract:
        pytesseract.pytesseract.tesseract_cmd = tesseract
        try:
            parts = []
            for page_no, image in enumerate(images, start=1):
                text = pytesseract.image_to_string(image, lang="eng")
                if text and text.strip():
                    parts.append(f"--- OCR PAGE {page_no} ---\n{text.strip()}")
            if parts:
                logger.info("English OCR completed with Tesseract (pages=%d)", len(parts))
                return "\n\n".join(parts)
        except Exception as error:
            logger.warning("Tesseract OCR failed (%s)", type(error).__name__)

    easyocr_ready = False
    try:
        reader = _easyocr_reader()
        easyocr_ready = True
        import numpy as np

        parts = []
        for page_no, image in enumerate(images, start=1):
            detected = reader.readtext(np.asarray(image), detail=0)
            text = " ".join(part.strip() for part in detected if part and part.strip())
            if text:
                parts.append(f"--- OCR PAGE {page_no} ---\n{text}")
        if parts:
            logger.info("English OCR completed with EasyOCR (pages=%d)", len(parts))
            return "\n\n".join(parts)
    except Exception as error:
        logger.warning("EasyOCR unavailable (%s)", type(error).__name__)

    # If local OCR is unavailable, use Gemini Vision only when configured. Its
    # output remains server-side and failures do not claim OCR succeeded.
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options=types.HttpOptions(timeout=20000))
            parts = []
            for page_no, image in enumerate(images, start=1):
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/png"),
                              "Transcribe the English text visible in this image. Return only the transcription."],
                )
                if response and response.text and response.text.strip():
                    parts.append(f"--- OCR PAGE {page_no} ---\n{response.text.strip()}")
            if parts:
                logger.info("English OCR transcription completed with Gemini Vision")
                return "\n\n".join(parts)
        except Exception as error:
            logger.warning("Gemini Vision OCR unavailable (%s)", type(error).__name__)

    if not tesseract and not easyocr_ready:
        raise OCRProcessingError(
            "English OCR could not run: Tesseract is not installed and the EasyOCR English model is unavailable. "
            "Install Tesseract or install the EasyOCR English model files, then retry."
        )
    raise OCRProcessingError("OCR ran but could not read English text from this document. Upload a clearer scan.")
