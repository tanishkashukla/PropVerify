import logging
import os
import re
from typing import Optional, Union

from backend.config import settings
from backend.document_processing.classifier import classify_document
from backend.document_processing.ocr import OCRProcessingError, perform_ocr
from backend.document_processing.pdf_extractor import extract_text_from_pdf
from backend.models.document import (
    DocumentType, ExtractedDocumentData, ProcessingResult,
    display_document_type, normalize_document_type,
)
from backend.services.ai_service import extract_structured_data_with_status

logger = logging.getLogger("propverify.documents")
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
SUPPORTED_TYPES = {item.value for item in DocumentType if item != DocumentType.UNKNOWN}
NON_LATIN_SCRIPT = re.compile(r"[\u0400-\u052f\u0590-\u08ff\u0900-\u0dff\u0e00-\u0eff\u3040-\u30ff\u3400-\u9fff]")


class DocumentInputError(ValueError):
    """A user-uploaded file is invalid or cannot be read as its declared type."""


def process_document(
    file_input: Union[str, bytes],
    filename: str = "",
    document_type_override: Optional[str] = None,
) -> ProcessingResult:
    if isinstance(file_input, str) and not filename:
        filename = os.path.basename(file_input)
    if not filename:
        raise DocumentInputError("The uploaded document is missing a filename.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DocumentInputError("Unsupported file type. Upload a PDF, JPG, or PNG document.")

    if isinstance(file_input, bytes) and not file_input:
        raise DocumentInputError("The uploaded document is empty.")

    logger.info("[PropVerify] Processing document: %s", os.path.basename(filename)[:100])
    errors = []
    warnings = []
    ocr_used = False

    try:
        text, page_count = extract_text_from_pdf(file_input, filename=filename)
    except Exception as error:
        logger.warning("Text extraction failed for %s (%s)", os.path.basename(filename)[:100], type(error).__name__)
        if ext == ".pdf":
            raise DocumentInputError("This PDF is invalid, encrypted, or could not be opened.") from None
        text, page_count = "", 1

    if len(text.strip()) < settings.MIN_TEXT_THRESHOLD:
        ocr_used = True
        logger.info("[PropVerify] OCR required: true (%s)", os.path.basename(filename)[:100])
        try:
            ocr_text = perform_ocr(file_input, filename=filename)
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
        except OCRProcessingError as error:
            warnings.append(str(error))
        except Exception as error:
            logger.warning("OCR failed for %s (%s)", os.path.basename(filename)[:100], type(error).__name__)
            warnings.append("English OCR could not process this document. Upload a clearer scan or configure an OCR engine.")

    logger.info("[PropVerify] Text extraction completed (characters=%d, pages=%d)", len(text), page_count)
    logger.info("[PropVerify] Text extraction: %s", "SUCCESS" if text.strip() else "FAILED")
    logger.info("[PropVerify] OCR: %s (characters=%d)", "USED" if ocr_used else "NOT USED", len(text) if ocr_used else 0)

    unsupported_language = bool(NON_LATIN_SCRIPT.search(text))
    if unsupported_language:
        warnings.append("This document contains non-English script. PropVerify processes English text only; extracted fields may be incomplete.")

    document_type = classify_document(text, filename=filename)
    selected_type = normalize_document_type(document_type_override)
    # The user-selected upload type is authoritative when supplied. Classifier
    # guesses must not silently replace an explicit document-type assignment.
    if selected_type in SUPPORTED_TYPES:
        document_type = selected_type
    document_type_label = display_document_type(document_type)

    extracted_data = ExtractedDocumentData(document_type=document_type)
    ai_used = False
    extraction_used = "deterministic"
    fallback_used = False
    if not text.strip():
        errors.append("No readable English text could be extracted from this document.")
    elif unsupported_language:
        # Do not guess fields from documents containing unsupported scripts.
        pass
    else:
        try:
            extracted_data, extraction_used, fallback_used, _provider_diagnostic = extract_structured_data_with_status(
                text, document_type_label, filename=filename
            )
            ai_used = extraction_used == "ai"
        except Exception as error:
            logger.error("Structured extraction failed for %s (%s)", os.path.basename(filename)[:100], type(error).__name__)
            errors.append("Document extraction could not be completed. Upload a clearer document or try again later.")

    if ocr_used:
        logger.info("[PropVerify] OCR completed: %s", "text extracted" if text.strip() else "no readable text")
    logger.info("[PropVerify] Document type: %s (%s)", document_type_label, document_type)
    logger.info("[PropVerify] Structured extraction method: %s (fallback_used=%s)", extraction_used, fallback_used)

    all_fields = [
        "document_type", "owner_name", "seller_name", "buyer_name", "property_address", "personal_address",
        "survey_gat_number", "property_area", "registration_number", "document_date", "document_number",
        "date_of_issue",
    ]
    fields_extracted = [field for field in all_fields if (value := getattr(extracted_data, field, None)) is not None and str(value).strip()]
    fields_missing = [field for field in all_fields if field not in fields_extracted]
    extracted_data.document_type = document_type
    for field in ("owner_name", "seller_name", "buyer_name", "property_area", "document_date"):
        logger.info("[PropVerify] %s: %s", field, "FOUND" if field in fields_extracted else "MISSING")
    logger.info("[PropVerify] Structured fields present: %d/%d", len(fields_extracted), len(all_fields))

    return ProcessingResult(
        file_name=filename,
        document_type_detected=document_type,
        ocr_used=ocr_used,
        raw_text_length=len(text),
        extracted_data=extracted_data,
        fields_extracted=fields_extracted,
        fields_missing=fields_missing,
        errors=errors,
        warnings=warnings,
        ai_used=ai_used,
        extraction_used=extraction_used,
        fallback_used=fallback_used,
    )
