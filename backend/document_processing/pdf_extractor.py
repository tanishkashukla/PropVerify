import os
from typing import Tuple, Union, BinaryIO
import pymupdf


def extract_text_from_pdf(file_input: Union[str, bytes, BinaryIO], filename: str = "") -> Tuple[str, int]:
    """
    Extracts selectable text from a PDF file using PyMuPDF.

    Args:
        file_input: File path (str), raw file bytes, or binary stream.
        filename: Optional filename to identify file extension.

    Returns:
        Tuple of (extracted_text: str, page_count: int)
    """
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:
        return "", 1

    doc = None
    try:
        if isinstance(file_input, str):
            if not os.path.exists(file_input):
                raise FileNotFoundError(f"File not found: {file_input}")
            doc = pymupdf.open(file_input)
        elif isinstance(file_input, bytes):
            ftype = ext.lstrip(".") if ext else "pdf"
            doc = pymupdf.open(stream=file_input, filetype=ftype)
        elif hasattr(file_input, "read"):
            content = file_input.read()
            ftype = ext.lstrip(".") if ext else "pdf"
            doc = pymupdf.open(stream=content, filetype=ftype)
        else:
            raise ValueError("Unsupported file_input type.")

        extracted_pages = []
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()
        return full_text, len(doc)
    except Exception as e:
        raise ValueError("The PDF could not be opened or its text could not be extracted.") from e
    finally:
        if doc is not None:
            doc.close()
