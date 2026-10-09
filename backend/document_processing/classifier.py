import re
from backend.models.document import DocumentType


def classify_document(text: str, filename: str = "") -> str:
    """
    Classifies the document type based primarily on text content, with filename fallback.

    Supported document types:
    - Sale Deed
    - Property Card
    - Index II
    - 7/12 Extract
    - ID Document

    Returns:
        Document type string matching DocumentType enum.
    """
    text_upper = text.upper() if text else ""
    filename_upper = filename.upper() if filename else ""

    # 1. Content-based Classification Heuristics

    # Check for Index II (must check before Sale Deed because Index II references Sale Deeds)
    if "INDEX II" in text_upper or "INDEX-II" in text_upper or "INDEX 2" in text_upper or "REGISTRATION SUMMARY" in text_upper or "REGISTRATION PARTICULARS" in text_upper:
        return DocumentType.INDEX_II.value

    # Check for 7/12 Extract / Land Record
    if "7/12" in text_upper or "7 / 12" in text_upper or "7-12" in text_upper or "VILLAGE FORM NO. 7" in text_upper or "LAND RECORD" in text_upper or "HOLDER / OCCUPANT DETAILS" in text_upper:
        return DocumentType.EXTRACT_7_12.value

    # Check for Property Card
    if "PROPERTY CARD" in text_upper or "PROPERTY REGISTER CARD" in text_upper or "RECORDED HOLDER" in text_upper or "NATURE OF HOLDING" in text_upper or "WARD K/EAST" in text_upper:
        return DocumentType.PROPERTY_CARD.value

    # Check for Sale Deed
    if "SALE DEED" in text_upper or "DEED OF SALE" in text_upper or "PURCHASER" in text_upper or "DEED" in text_upper and "SELLER" in text_upper:
        return DocumentType.SALE_DEED.value

    # Check for ID Document / Identity Proof
    if ("IDENTITY" in text_upper or "ID DOCUMENT" in text_upper or "IDENTITY PROOF" in text_upper or
            "DATE OF BIRTH" in text_upper or "AADHAAR" in text_upper or "PAN CARD" in text_upper or "PASSPORT" in text_upper or "NAME FOR MATCHING" in text_upper):
        return DocumentType.ID_DOCUMENT.value

    # 2. Filename-based Fallback Heuristics
    if re.search(r"INDEX", filename_upper):
        return DocumentType.INDEX_II.value
    if re.search(r"7[_\-\s]?12|LAND[_\-\s]?RECORD", filename_upper):
        return DocumentType.EXTRACT_7_12.value
    if re.search(r"PROPERTY[_\-\s]?CARD|PROP[_\-\s]?CARD", filename_upper):
        return DocumentType.PROPERTY_CARD.value
    if re.search(r"SALE[_\-\s]?DEED|DEED", filename_upper):
        return DocumentType.SALE_DEED.value
    if re.search(r"ID|IDENTITY|PASSPORT|AADHAAR|PAN|OWNER[_\-\s]?DOC", filename_upper):
        return DocumentType.ID_DOCUMENT.value

    return DocumentType.UNKNOWN.value

