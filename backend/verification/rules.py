import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from typing import Dict, List, Set


EXPECTED_DOCUMENT_TYPES: List[str] = [
    "Sale Deed",
    "Property Card",
    "Index II",
    "7/12 Extract",
    "ID Document"
]

FIELD_LABELS: Dict[str, str] = {
    "owner_name": "Owner Name",
    "seller_name": "Seller Name",
    "buyer_name": "Buyer Name",
    "property_address": "Property Address",
    "survey_gat_number": "Survey / Gat Number",
    "property_area": "Property Area",
    "registration_number": "Registration Number",
    "document_date": "Document Date",
    "document_number": "Document Reference Number"
}

DOCUMENT_APPLICABLE_FIELDS: Dict[str, Set[str]] = {
    "Sale Deed": {
        "owner_name", "seller_name", "buyer_name", "property_address",
        "survey_gat_number", "property_area", "registration_number", "document_date"
    },
    "Property Card": {
        "owner_name", "property_address", "survey_gat_number",
        "property_area", "registration_number", "document_date", "document_number"
    },
    "Index II": {
        "seller_name", "buyer_name", "property_address",
        "survey_gat_number", "property_area", "registration_number", "document_date"
    },
    "7/12 Extract": {
        "owner_name", "property_address", "survey_gat_number",
        "property_area", "registration_number", "document_date", "document_number"
    },
    "ID Document": {
        # An ID's residential address is personal identity data and is not a
        # reliable source for the property's address under verification.
        "owner_name", "document_date", "document_number"
    }
}

FIELD_SEVERITY: Dict[str, str] = {
    "survey_gat_number": "HIGH",
    "owner_name": "HIGH",
    "seller_name": "HIGH",
    "buyer_name": "HIGH",
    "registration_number": "HIGH",
    "property_address": "MEDIUM",
    "property_area": "MEDIUM",
    "document_date": "LOW",
    "document_number": "LOW"
}


LABEL_PREFIX_PATTERN = r"^(?:reference|ref|name|full\s+name|matching\s+name|name\s+for\s+matching|owner\s+name|buyer\s+name|seller\s+name|transferee|transferor|purchaser|vendor|holder|holder\s+name|registered\s+owner|recorded\s+holder|applicant|cardholder)\s*[:=:-]\s*"
HONORIFIC_PATTERN = r"^(?:mr|mrs|ms|miss|shri|shree|smt|dr|prof|er)\.?\s+"


def sanitize_person_name_string(val: str) -> str:
    """
    Strips leading label prefixes (such as 'Reference:', 'Full Name:', 'Name:') from a person name string.
    """
    if not val or not isinstance(val, str):
        return ""
    name = val.strip()
    name = re.sub(LABEL_PREFIX_PATTERN, "", name, flags=re.IGNORECASE).strip()
    return name


INVALID_PERSON_NAME_PATTERNS: Set[str] = {
    "owner name", "seller name", "buyer name", "property address",
    "survey / gat number", "survey gat number", "property area",
    "registration number", "document date", "document number",
    "property document set", "secure check", "verification test",
    "index ii", "property card", "sale deed", "7/12 extract", "id document",
    "reference", "full name", "matching name", "name", "holder name", "holder",
    "transferee", "transferor", "purchaser", "vendor", "registered owner"
}


def is_invalid_person_name(name: str) -> bool:
    """
    Returns True if the input string is a document title, heading, field label, or invalid phrase
    rather than a valid person name.
    """
    if not name or not isinstance(name, str):
        return True
    clean_name = sanitize_person_name_string(name)
    clean = re.sub(r"\s+", " ", clean_name.strip().lower())
    if clean in INVALID_PERSON_NAME_PATTERNS:
        return True
    if any(term in clean for term in [
        "verification test", "fictional identity", "test document", "synthetic test",
        "identity proof", "property card", "sale deed", "index ii", "7/12 extract",
        "land record", "test data", "fictional document", "synthetic record"
    ]):
        return True
    if not re.search(r"[a-zA-Z]", clean_name):
        return True
    if len(clean_name) > 70:
        return True
    return False


def normalize_person_name(val: str) -> str:
    """
    Normalizes a person's name for comparison.
    Strips leading label prefixes ('Reference:', 'Full Name:'), common honorifics (Mr., Mrs., Ms., Shri, Smt., Dr., etc.),
    collapses whitespace, and removes punctuation while preserving actual name tokens.
    """
    if not val:
        return ""
    clean_val = sanitize_person_name_string(val)
    if is_invalid_person_name(clean_val):
        return ""
    norm = clean_val.lower().strip()
    # Strip honorifics from start of name
    norm = re.sub(HONORIFIC_PATTERN, "", norm, flags=re.IGNORECASE).strip()
    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def normalize_text(text: str) -> str:
    """
    Normalizes a string for deterministic comparison.
    Collapses internal whitespace, removes line breaks and surrounding punctuation.
    """
    if not text:
        return ""
    text_clean = text.replace("\n", " ").strip()
    text_clean = re.sub(r"[^\w\s/,-]", " ", text_clean)
    text_clean = re.sub(r"\s+", " ", text_clean)
    return text_clean.lower().strip()


def normalize_survey_gat(val: str) -> str:
    """
    Normalizes Survey/Gat numbers (e.g., '124 / 3A' -> '124/3A').
    """
    if not val:
        return ""
    norm = normalize_text(val)
    norm = re.sub(r"\s*/\s*", "/", norm)
    norm = re.sub(r"\s*-\s*", "-", norm)
    return norm


def normalize_area(val: str) -> str:
    """
    Normalizes property area strings (e.g., '1450 sq.ft.', '1450 sq ft', '1450 Square Feet').
    Extracts core numbers and units for equivalent comparison.
    """
    if not val:
        return ""
    val_clean = val.lower().strip()

    # Match sq ft / sq.ft / square feet
    sqft_m = re.search(r"([0-9\.,]+)\s*(?:sq\.?\s*ft\.?|square\s*feet)", val_clean)
    sqm_m = re.search(r"([0-9\.,]+)\s*(?:sq\.?\s*m\.?|square\s*met(?:er|re)s?|sqm|m²)", val_clean)

    # Prefer square feet when a document gives both units. This lets a
    # value such as "1500 sq. ft. (139.35 sq. m.)" compare equal to another
    # document that records only "1500 sq. ft.".
    if sqft_m:
        try:
            number = Decimal(sqft_m.group(1).replace(",", ""))
            normalized = number.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            return f"{normalized.normalize()} sqft"
        except InvalidOperation:
            return normalize_text(val)
    if sqm_m:
        try:
            number = Decimal(sqm_m.group(1).replace(",", ""))
            sqft = (number * Decimal("10.7639104167")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            return f"{sqft.normalize()} sqft"
        except InvalidOperation:
            return normalize_text(val)

    return normalize_text(val)


def normalize_date(val: str) -> str:
    """
    Normalizes date representations for comparison.
    """
    if not val:
        return ""
    v = val.strip().lower()
    date_formats = (
        "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y",
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
    )
    candidate = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", v)
    for date_format in date_formats:
        try:
            return datetime.strptime(candidate, date_format).date().isoformat()
        except ValueError:
            continue

    return normalize_text(val)


def normalize_field_value(field_name: str, value: str) -> str:
    """
    Normalizes a field value depending on field type.
    """
    if not value:
        return ""
    if field_name in {"owner_name", "seller_name", "buyer_name"}:
        return normalize_person_name(value)
    elif field_name == "survey_gat_number":
        return normalize_survey_gat(value)
    elif field_name == "property_area":
        return normalize_area(value)
    elif field_name == "document_date":
        return normalize_date(value)
    return normalize_text(value)

