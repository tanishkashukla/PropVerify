from typing import List, Dict, Any, Optional
from collections import Counter
import re
from backend.models.document import ProcessingResult
from backend.verification.result import (
    VerificationResult,
    FieldMatch,
    FieldMismatch,
    FieldMissing,
    MissingDocument,
    OverallStatus,
    SeverityLevel
)
from backend.verification.rules import (
    EXPECTED_DOCUMENT_TYPES,
    DOCUMENT_APPLICABLE_FIELDS,
    FIELD_SEVERITY,
    FIELD_LABELS,
    normalize_field_value
)


FIELD_LABEL_VALUES = {
    "survey_gat_number": {"survey gat number", "survey number", "gat number"},
    "owner_name": {"owner", "owner name", "registered owner", "recorded owner", "property owner", "holder", "holder name", "registered holder", "registered owner holder", "owner holder", "holder owner", "name of owner", "name of holder"},
    "seller_name": {"seller", "seller name", "vendor", "vendor name", "transferor", "transferor name", "first party", "seller vendor", "transferor seller"},
    "buyer_name": {"buyer", "buyer name", "purchaser", "purchaser name", "transferee", "transferee name", "second party", "buyer purchaser", "transferee buyer"},
    "property_address": {"address", "property address", "full address", "personal address", "location"},
    "property_area": {"area", "property area", "area of property", "total area", "plot area", "land area", "area of land", "extent", "measurement"},
    "registration_number": {"registration", "registration number", "registration reference", "record reference"},
    "document_date": {"date", "document date", "date of document", "date of registration", "registration date", "date of instrument", "execution date", "record date", "entry date", "issue date", "date of issue"},
}


def _is_field_label_value(field: str, value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return normalized in FIELD_LABEL_VALUES.get(field, set())


def compare_documents(
    results: List[ProcessingResult],
    required_documents: Optional[List[str]] = None
) -> VerificationResult:
    """
    Compares extracted fields across multiple property documents.

    Args:
        results: List of ProcessingResult objects from document extraction pipeline.
        required_documents: Optional list of document types marked as required by user.
                            Defaults to all 5 standard document types if omitted.

    Returns:
        VerificationResult object.
    """
    if required_documents is None:
        required_documents = EXPECTED_DOCUMENT_TYPES.copy()

    documents_processed = len(results)

    # Detect Provided vs Missing Document Types
    detected_types = set(r.document_type_detected for r in results)
    provided_documents = list(detected_types)
    missing_docs: List[MissingDocument] = []

    for req_type in required_documents:
        if req_type not in detected_types:
            missing_docs.append(
                MissingDocument(
                    expected_document_type=req_type,
                    status="MISSING",
                    severity=SeverityLevel.HIGH.value,
                    message=f"{req_type} was selected as required but was not provided."
                )
            )

    matches: List[FieldMatch] = []
    mismatches: List[FieldMismatch] = []
    missing_fields: List[FieldMissing] = []

    compare_fields = [
        "survey_gat_number",
        "owner_name",
        "buyer_name",
        "seller_name",
        "property_address",
        "property_area",
        "registration_number",
        "document_date"
    ]

    for field in compare_fields:
        field_label = FIELD_LABELS.get(field, field.replace("_", " ").title())
        raw_values: Dict[str, str] = {}
        normalized_values: Dict[str, str] = {}
        doc_type_map: Dict[str, str] = {}
        docs_missing_this_field: List[str] = []

        for res in results:
            doc_type = res.document_type_detected
            applicable = DOCUMENT_APPLICABLE_FIELDS.get(doc_type, set())

            # Identity issue dates are stored separately as date_of_issue;
            # compare only dates from property documents.
            if field == "document_date" and doc_type not in ["Sale Deed", "Property Card", "Index II", "7/12 Extract"]:
                continue

            if field in applicable:
                val = getattr(res.extracted_data, field, None)
                if val is not None and str(val).strip() != "" and not _is_field_label_value(field, str(val)):
                    normalized = normalize_field_value(field, str(val))
                    if normalized:
                        raw_values[res.file_name] = str(val).strip()
                        normalized_values[res.file_name] = normalized
                        doc_type_map[res.file_name] = doc_type
                    else:
                        docs_missing_this_field.append((doc_type, res.file_name))
                else:
                    docs_missing_this_field.append((doc_type, res.file_name))

        # Global status belongs to the field, while per-document omissions are
        # diagnostics. A valid value suppresses a global MISSING status; the
        # available values are compared below and produce exactly one result.
        if not raw_values and docs_missing_this_field:
            missing_filenames = [d[1] for d in docs_missing_this_field]
            missing_types = [d[0] for d in docs_missing_this_field]
            missing_sources_str = ", ".join([f"{d[0]} ({d[1]})" for d in docs_missing_this_field])

            missing_fields.append(
                FieldMissing(
                    field=field,
                    status="MISSING",
                    document_name=", ".join(missing_filenames),
                    document_type=", ".join(missing_types) if len(missing_types) <= 2 else "Multiple",
                    severity=FIELD_SEVERITY.get(field, "MEDIUM"),
                    message=f"{field_label} could not be extracted from {missing_sources_str}."
                )
            )

        # 2. Compare Extracted Values Across Applicable Documents
        if normalized_values:
            unique_norm_vals = set(normalized_values.values())

            if len(unique_norm_vals) == 1:
                first_raw_val = list(raw_values.values())[0]
                matches.append(
                    FieldMatch(
                        field=field,
                        status="MATCH",
                        matched_value=first_raw_val,
                        documents_compared=raw_values
                    )
                )
            else:
                counts = Counter(normalized_values.values())
                majority_norm = counts.most_common(1)[0][0]

                conflicting_docs = []
                for fname, norm_v in normalized_values.items():
                    if norm_v != majority_norm:
                        conflicting_docs.append((fname, doc_type_map[fname], raw_values[fname]))

                if conflicting_docs:
                    fname, d_type, raw_v = conflicting_docs[0]
                    message = f"{field_label} differs in {d_type} ({fname}). Found '{raw_v}'."
                else:
                    message = f"Conflicting values found for {field_label} across documents."

                severity = FIELD_SEVERITY.get(field, "HIGH")

                mismatches.append(
                    FieldMismatch(
                        field=field,
                        status="MISMATCH",
                        values=raw_values,
                        severity=severity,
                        message=message,
                        conflicting_documents=[fname for fname, norm_value in normalized_values.items() if norm_value != majority_norm],
                    )
                )

    # Determine Overall Status
    has_processing_errors = any(result.errors for result in results)
    if mismatches:
        overall_status = OverallStatus.ISSUES_FOUND.value
    elif has_processing_errors:
        overall_status = OverallStatus.ERROR.value
    elif missing_docs:
        overall_status = OverallStatus.MISSING_DOCUMENTS.value
    elif not matches:
        overall_status = OverallStatus.PROCESSING_INCOMPLETE.value
    else:
        overall_status = OverallStatus.VERIFIED.value

    warnings = list(dict.fromkeys(
        message
        for result in results
        for message in (result.errors or [])
    ))
    return VerificationResult(
        overall_status=overall_status,
        documents_processed=documents_processed,
        required_documents=required_documents,
        provided_documents=provided_documents,
        matches=matches,
        mismatches=mismatches,
        missing_fields=missing_fields,
        missing_documents=missing_docs,
        processing_status="failed" if has_processing_errors else "completed",
        ai_used=bool(results) and all(result.ai_used for result in results),
        warnings=warnings,
        processed_documents=results,
    )

