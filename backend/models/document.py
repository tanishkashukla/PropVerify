from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    SALE_DEED = "sale_deed"
    PROPERTY_CARD = "property_card"
    INDEX_II = "index_ii"
    EXTRACT_7_12 = "7_12_extract"
    ID_DOCUMENT = "id_document"
    UNKNOWN = "unknown"


DOCUMENT_TYPE_LABELS = {
    DocumentType.SALE_DEED.value: "Sale Deed",
    DocumentType.PROPERTY_CARD.value: "Property Card",
    DocumentType.INDEX_II.value: "Index II",
    DocumentType.EXTRACT_7_12.value: "7/12 Extract",
    DocumentType.ID_DOCUMENT.value: "ID Document",
    DocumentType.UNKNOWN.value: "Unknown",
}


def normalize_document_type(value: Optional[str]) -> Optional[str]:
    """Return one canonical ID for a known slug or legacy display label."""
    if value is None:
        return None
    import re
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    aliases = {
        "sale_deed": DocumentType.SALE_DEED.value,
        "property_card": DocumentType.PROPERTY_CARD.value,
        "index_ii": DocumentType.INDEX_II.value,
        "7_12_extract": DocumentType.EXTRACT_7_12.value,
        "extract_7_12": DocumentType.EXTRACT_7_12.value,
        "id_document": DocumentType.ID_DOCUMENT.value,
    }
    return aliases.get(normalized)


def display_document_type(value: Optional[str]) -> str:
    """Map canonical IDs (or existing display labels) to readable labels."""
    canonical = normalize_document_type(value)
    if canonical:
        return DOCUMENT_TYPE_LABELS[canonical]
    return value or DOCUMENT_TYPE_LABELS[DocumentType.UNKNOWN.value]


class ExtractedDocumentData(BaseModel):
    document_type: Optional[str] = Field(
        default=None,
        description="Type of document (Sale Deed, Property Card, Index II, 7/12 Extract, ID Document)"
    )
    owner_name: Optional[str] = Field(
        default=None,
        description="Name of current recorded owner, holder, or purchaser"
    )
    seller_name: Optional[str] = Field(
        default=None,
        description="Name of seller or transferor if applicable"
    )
    buyer_name: Optional[str] = Field(
        default=None,
        description="Name of buyer, purchaser, or transferee if applicable"
    )
    property_address: Optional[str] = Field(
        default=None,
        description="Complete property address; never use an ID document's personal address here"
    )
    personal_address: Optional[str] = Field(
        default=None,
        description="Personal/residential address shown on an identity document, not the property address"
    )
    survey_gat_number: Optional[str] = Field(
        default=None,
        description="Survey or Gat Number of the land/property"
    )
    property_area: Optional[str] = Field(
        default=None,
        description="Total property or built-up area"
    )
    registration_number: Optional[str] = Field(
        default=None,
        description="Registration reference number"
    )
    document_date: Optional[str] = Field(
        default=None,
        description="Date of a property record or instrument; do not put ID issue dates here"
    )
    date_of_issue: Optional[str] = Field(
        default=None,
        description="Issue date of an identity document"
    )
    document_number: Optional[str] = Field(
        default=None,
        description="Document or record number if distinct from registration number"
    )


class ProcessingResult(BaseModel):
    file_name: str
    document_type_detected: str
    ocr_used: bool
    raw_text_length: int
    extracted_data: ExtractedDocumentData
    fields_extracted: List[str]
    fields_missing: List[str]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ai_used: bool = False
    extraction_used: str = Field(default="deterministic", description="Extraction implementation used: ai or deterministic")
    fallback_used: bool = Field(default=False, description="Whether deterministic extraction recovered from a configured AI provider failure")
