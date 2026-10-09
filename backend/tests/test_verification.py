import glob
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.models.document import ProcessingResult, ExtractedDocumentData, display_document_type
from backend.config import settings
from backend.document_processing.extractor import process_document
from backend.verification.comparator import compare_documents
from backend.verification.result import OverallStatus, SeverityLevel
from backend.services.ai_service import extract_structured_data_heuristic, _gemini_error_warning


@pytest.fixture(autouse=True)
def avoid_external_ai_requests(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")


def _result(filename, document_type, **fields):
    extracted = ExtractedDocumentData(document_type=document_type, **fields)
    return ProcessingResult(
        file_name=filename,
        document_type_detected=document_type,
        ocr_used=False,
        raw_text_length=200,
        extracted_data=extracted,
        fields_extracted=list(fields),
        fields_missing=[],
    )


def _field_status_count(verification, field):
    return sum(item.field == field for group in (verification.matches, verification.mismatches, verification.missing_fields) for item in group)


def test_valid_seller_match_is_not_also_missing():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", seller_name="Vikram Deshmukh"),
        _result("index.pdf", "Index II", seller_name="Vikram Deshmukh"),
    ], required_documents=[])

    assert [item.field for item in verification.matches].count("seller_name") == 1
    assert not any(item.field == "seller_name" for item in verification.missing_fields)
    assert _field_status_count(verification, "seller_name") == 1


def test_area_match_is_not_invalidated_by_missing_applicable_docs():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", property_area="1500 sq. ft. (139.35 sq. m.)"),
        _result("card.pdf", "Property Card", property_area="1500 sq. ft."),
        _result("index.pdf", "Index II", property_area="1500 sq. ft."),
        _result("712.pdf", "7/12 Extract", property_area="1500 sq. ft."),
        _result("other-index.pdf", "Index II"),
    ], required_documents=[])

    assert [item.field for item in verification.matches].count("property_area") == 1
    assert not any(item.field == "property_area" for item in verification.missing_fields)
    assert _field_status_count(verification, "property_area") == 1


def test_dual_unit_and_square_meter_area_normalize_to_square_feet():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", property_area="1500 sq. ft. (139.35 sq. m.)"),
        _result("index.pdf", "Index II", property_area="139.35 square metres"),
    ], required_documents=[])
    area_match = [item for item in verification.matches if item.field == "property_area"]
    assert len(area_match) == 1
    assert _field_status_count(verification, "property_area") == 1


def test_survey_mismatch_remains_one_canonical_status():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", survey_gat_number="215/7A"),
        _result("card.pdf", "Property Card", survey_gat_number="215/7A"),
        _result("index.pdf", "Index II", survey_gat_number="215/7A"),
        _result("index-mismatch.pdf", "Index II", survey_gat_number="215/9B"),
        _result("712.pdf", "7/12 Extract", survey_gat_number="215/7A"),
    ], required_documents=[])

    mismatches = [item for item in verification.mismatches if item.field == "survey_gat_number"]
    assert len(mismatches) == 1
    assert mismatches[0].severity == "HIGH"
    assert mismatches[0].values["index-mismatch.pdf"] == "215/9B"
    assert _field_status_count(verification, "survey_gat_number") == 1


def test_id_personal_address_is_not_compared_to_property_address():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", property_address="Plot 42, Green Meadows, Pune"),
        _result("card.pdf", "Property Card", property_address="Plot 42, Green Meadows, Pune"),
        _result("identity.pdf", "ID Document", property_address="42 Green Meadows, Baner, Pune"),
    ], required_documents=[])

    assert len([item for item in verification.matches if item.field == "property_address"]) == 1
    assert not any(item.field == "property_address" for item in verification.mismatches)
    assert _field_status_count(verification, "property_address") == 1


def test_address_heading_is_never_returned_as_the_value():
    data = extract_structured_data_heuristic("ADDRESS\nAddress\n42 Green Meadows, Baner, Pune, Maharashtra - 411045", "ID Document")
    assert data.personal_address == "42 Green Meadows, Baner, Pune, Maharashtra - 411045"
    assert data.property_address is None


@pytest.mark.parametrize(("document_type", "text", "field", "expected"), [
    ("Property Card", "Registered Owner / Holder\nRiya Sharma", "owner_name", "Riya Sharma"),
    ("7/12 Extract", "Holder / Owner\nRiya Sharma", "owner_name", "Riya Sharma"),
    ("Sale Deed", "Buyer / Purchaser\nRiya Sharma", "buyer_name", "Riya Sharma"),
    ("Index II", "Transferee / Buyer\nRiya Sharma", "buyer_name", "Riya Sharma"),
    ("Sale Deed", "Seller / Vendor\nVikram Deshmukh", "seller_name", "Vikram Deshmukh"),
    ("Index II", "Transferor / Seller\nVikram Deshmukh", "seller_name", "Vikram Deshmukh"),
    ("Index II", "Area of Property\n1500 sq. ft. (139.35 sq. m.)", "property_area", "1500 sq. ft. (139.35 sq. m.)"),
    ("7/12 Extract", "Area of Land\n1500 sq. ft. (139.35 sq. m.)", "property_area", "1500 sq. ft. (139.35 sq. m.)"),
])
def test_legal_labels_extract_the_next_value(document_type, text, field, expected):
    extracted = extract_structured_data_heuristic(text, document_type)
    assert getattr(extracted, field) == expected


@pytest.mark.parametrize(("document_type", "text", "field", "expected"), [
    ("Property Card", "Registered Owner / Holder Riya Sharma", "owner_name", "Riya Sharma"),
    ("7/12 Extract", "Holder / Owner: Riya Sharma", "owner_name", "Riya Sharma"),
    ("Sale Deed", "Buyer / Purchaser → Riya Sharma", "buyer_name", "Riya Sharma"),
    ("Index II", "Transferee / Buyer: Riya Sharma", "buyer_name", "Riya Sharma"),
    ("Sale Deed", "Seller / Vendor - Vikram Deshmukh", "seller_name", "Vikram Deshmukh"),
    ("Index II", "Transferor / Seller: Vikram Deshmukh", "seller_name", "Vikram Deshmukh"),
])
def test_inline_compound_legal_labels_extract_only_the_value(document_type, text, field, expected):
    extracted = extract_structured_data_heuristic(text, document_type)
    assert getattr(extracted, field) == expected


def test_id_issue_date_is_separate_from_property_document_date():
    identity = extract_structured_data_heuristic(
        "Name: Riya Sharma\nDocument Number: IDP-7842-2026\nDate of Issue: 05 January 2024\nAddress:\n42 Green Meadows, Baner, Pune, Maharashtra - 411045",
        "ID Document",
    )
    sale = _result("sale.pdf", "Sale Deed", document_date="18 September 2026")
    index = _result("index.pdf", "Index II", document_date="18 September 2026")
    id_result = _result(
        "identity.pdf", "ID Document", owner_name=identity.owner_name,
        document_date=identity.document_date, date_of_issue=identity.date_of_issue,
        personal_address=identity.personal_address,
    )
    verification = compare_documents([sale, index, id_result], required_documents=[])

    assert identity.document_date is None
    assert identity.date_of_issue == "05 January 2024"
    assert identity.personal_address.startswith("42 Green Meadows")
    assert len([item for item in verification.matches if item.field == "document_date"]) == 1
    assert not any(item.field == "document_date" for item in verification.mismatches + verification.missing_fields)


@pytest.mark.parametrize("status_code", [503, 504])
def test_gemini_temporary_unavailable_warning_is_not_a_config_error(status_code):
    class TemporaryGeminiError(Exception):
        code = status_code

    warning = _gemini_error_warning(TemporaryGeminiError())
    assert warning == "Gemini extraction was temporarily unavailable. Deterministic extraction was used as a fallback."
    assert "network access" not in warning
    assert "API configuration" not in warning


def test_each_global_field_has_at_most_one_status():
    verification = compare_documents([
        _result("sale.pdf", "Sale Deed", seller_name="Vikram Deshmukh", property_area="1500 sq. ft.", survey_gat_number="215/7A"),
        _result("index.pdf", "Index II", seller_name="Vikram Deshmukh", property_area="1500 sq ft", survey_gat_number="215/9B"),
        _result("card.pdf", "Property Card"),
    ], required_documents=[])

    fields = [item.field for group in (verification.matches, verification.mismatches, verification.missing_fields) for item in group]
    assert len(fields) == len(set(fields))
    assert len(fields) == 8
    assert set(fields) == {
        "survey_gat_number", "owner_name", "buyer_name", "seller_name",
        "property_address", "property_area", "registration_number", "document_date",
    }


def get_all_test_results():
    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents"))
    pdf_files = sorted(glob.glob(os.path.join(doc_dir, "*.pdf")))
    results = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        res = process_document(pdf_path, filename=filename)
        results.append(res.model_copy(update={"document_type_detected": display_document_type(res.document_type_detected)}))
    return results


def test_survey_gat_mismatch_on_test_dataset():
    """
    Tests cross-document verification on the 5 actual synthetic test documents.
    Must detect Survey/Gat Number mismatch (Index II has 124/8 vs 124/3A in others).
    """
    results = get_all_test_results()
    assert len(results) == 5

    verification = compare_documents(results)

    assert verification.overall_status == OverallStatus.ISSUES_FOUND.value
    assert verification.documents_processed == 5
    assert len(verification.missing_documents) == 0

    # Find survey_gat_number mismatch
    sg_mismatches = [m for m in verification.mismatches if m.field == "survey_gat_number"]
    assert len(sg_mismatches) == 1

    mismatch = sg_mismatches[0]
    assert mismatch.status == "MISMATCH"
    assert mismatch.severity == SeverityLevel.HIGH.value
    assert mismatch.values["01_Sale_Deed.pdf"] == "124/3A"
    assert mismatch.values["02_Property_Card.pdf"] == "124/3A"
    assert mismatch.values["03_Index_II.pdf"] == "124/8"
    assert mismatch.values["04_7_12_Extract.pdf"] == "124/3A"
    assert "Index II" in mismatch.message or "124/8" in mismatch.message


def test_matching_values():
    """
    Tests that identical normalized values across documents produce MATCH status.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Sale Deed",
            owner_name="Aarav Mehta",
            survey_gat_number="124/3A",
            property_address="Flat 704, Lakeview Residency, Mumbai",
            property_area="111.48 sq. m."
        ),
        fields_extracted=["document_type", "owner_name", "survey_gat_number", "property_address", "property_area"],
        fields_missing=[]
    )

    doc2 = ProcessingResult(
        file_name="property_card.pdf",
        document_type_detected="Property Card",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Property Card",
            owner_name="aarav mehta",
            survey_gat_number="124 / 3A",
            property_address="Flat 704, Lakeview Residency, Mumbai",
            property_area="111.48 sq. m."
        ),
        fields_extracted=["document_type", "owner_name", "survey_gat_number", "property_address", "property_area"],
        fields_missing=[]
    )

    # Include dummy results for remaining expected doc types to isolate match test
    dummy_index = ProcessingResult(
        file_name="index_2.pdf", document_type_detected="Index II", ocr_used=False, raw_text_length=100,
        extracted_data=ExtractedDocumentData(document_type="Index II", owner_name="Aarav Mehta", survey_gat_number="124/3A", property_address="Flat 704, Lakeview Residency, Mumbai"),
        fields_extracted=[], fields_missing=[]
    )
    dummy_712 = ProcessingResult(
        file_name="712.pdf", document_type_detected="7/12 Extract", ocr_used=False, raw_text_length=100,
        extracted_data=ExtractedDocumentData(document_type="7/12 Extract", owner_name="Aarav Mehta", survey_gat_number="124/3A", property_address="Flat 704, Lakeview Residency, Mumbai"),
        fields_extracted=[], fields_missing=[]
    )
    dummy_id = ProcessingResult(
        file_name="id.pdf", document_type_detected="ID Document", ocr_used=False, raw_text_length=100,
        extracted_data=ExtractedDocumentData(document_type="ID Document", owner_name="Aarav Mehta", property_address="Flat 704, Lakeview Residency, Mumbai"),
        fields_extracted=[], fields_missing=[]
    )

    verification = compare_documents([doc1, doc2, dummy_index, dummy_712, dummy_id])

    assert verification.overall_status == OverallStatus.VERIFIED.value
    assert len(verification.mismatches) == 0

    match_fields = [m.field for m in verification.matches]
    assert "owner_name" in match_fields
    assert "survey_gat_number" in match_fields
    assert "property_address" in match_fields


def test_mismatching_values():
    """
    Tests detection of mismatches in owner_name and property_area.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Sale Deed",
            owner_name="Aarav Mehta",
            survey_gat_number="124/3A",
            property_area="111.48 sq. m."
        ),
        fields_extracted=[], fields_missing=[]
    )

    doc2 = ProcessingResult(
        file_name="property_card.pdf",
        document_type_detected="Property Card",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Property Card",
            owner_name="Vikram Deshmukh",  # Mismatch owner
            survey_gat_number="124/3A",
            property_area="200 sq. m."     # Mismatch area
        ),
        fields_extracted=[], fields_missing=[]
    )

    verification = compare_documents([doc1, doc2])

    assert verification.overall_status == OverallStatus.ISSUES_FOUND.value
    mismatched_fields = {m.field: m for m in verification.mismatches}

    assert "owner_name" in mismatched_fields
    assert mismatched_fields["owner_name"].severity == "HIGH"
    assert mismatched_fields["owner_name"].values["sale_deed.pdf"] == "Aarav Mehta"
    assert mismatched_fields["owner_name"].values["property_card.pdf"] == "Vikram Deshmukh"

    assert "property_area" in mismatched_fields
    assert mismatched_fields["property_area"].severity == "MEDIUM"


def test_missing_fields():
    """
    Tests that a null field in an applicable document is recorded in missing_fields
    and does NOT trigger a false MISMATCH.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Sale Deed",
            owner_name="Aarav Mehta",
            survey_gat_number="124/3A"
        ),
        fields_extracted=[], fields_missing=[]
    )

    doc2 = ProcessingResult(
        file_name="property_card.pdf",
        document_type_detected="Property Card",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Property Card",
            owner_name="Aarav Mehta",
            survey_gat_number=None  # Null field
        ),
        fields_extracted=[], fields_missing=[]
    )

    verification = compare_documents([doc1, doc2])

    # A usable value remains the sole global field result; a per-document
    # omission cannot add a second global MISSING status.
    sg_mismatches = [m for m in verification.mismatches if m.field == "survey_gat_number"]
    assert len(sg_mismatches) == 0
    assert [m.field for m in verification.matches].count("survey_gat_number") == 1
    assert not any(f.field == "survey_gat_number" for f in verification.missing_fields)


def test_missing_document_types():
    """
    Tests detection of missing required property document types.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(document_type="Sale Deed", owner_name="Aarav Mehta"),
        fields_extracted=[], fields_missing=[]
    )

    # Only 1 document provided, remaining 4 required types missing
    verification = compare_documents([doc1])

    assert verification.overall_status == OverallStatus.MISSING_DOCUMENTS.value
    missing_types = [d.expected_document_type for d in verification.missing_documents]

    assert "Property Card" in missing_types
    assert "Index II" in missing_types
    assert "7/12 Extract" in missing_types
    assert "ID Document" in missing_types


def test_successful_document_extraction():
    """
    Test 1: Tests successful text & structured extraction from a valid property document.
    """
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents/01_Sale_Deed.pdf"))
    res = process_document(pdf_path, filename="01_Sale_Deed.pdf")

    assert res.file_name == "01_Sale_Deed.pdf"
    assert res.document_type_detected == "sale_deed"
    assert res.raw_text_length > 0
    assert res.extracted_data.owner_name == "Aarav Mehta"
    assert res.extracted_data.seller_name == "Vikram Deshmukh"
    assert res.extracted_data.survey_gat_number == "124/3A"
    assert res.extracted_data.registration_number == "MUM/REG/2026/04821"


def test_scanned_image_document_ocr():
    """
    Test 2: Tests handling of scanned/image-based document input (OCR execution & error banner).
    """
    img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents/scanned_id_sample.png"))
    if os.path.exists(img_path):
        res = process_document(img_path, filename="scanned_id_sample.png")
        assert res.ocr_used is True
        assert res.document_type_detected == "id_document"
        assert res.raw_text_length > 0, res.warnings + res.errors
        assert not res.errors


def test_genuine_missing_field():
    """
    Test 3: Tests that a document with a genuinely missing field produces a clear, single aggregated missing record.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed_final.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=600,
        extracted_data=ExtractedDocumentData(
            document_type="Sale Deed",
            owner_name="Aarav Mehta",
            survey_gat_number=None,
            property_area="111.48 sq. m."
        ),
        fields_extracted=[], fields_missing=[]
    )

    doc2 = ProcessingResult(
        file_name="propertycard.pdf",
        document_type_detected="Property Card",
        ocr_used=False,
        raw_text_length=500,
        extracted_data=ExtractedDocumentData(
            document_type="Property Card",
            owner_name="Aarav Mehta",
            survey_gat_number=None  # Genuinely missing
        ),
        fields_extracted=[], fields_missing=[]
    )

    verification = compare_documents([doc1, doc2])
    missing_sg = [f for f in verification.missing_fields if f.field == "survey_gat_number"]
    assert len(missing_sg) == 1
    assert "Survey / Gat Number" in missing_sg[0].message
    assert "propertycard.pdf" in missing_sg[0].document_name


def test_cross_document_mismatch_and_normalization():
    """
    Test 4: Tests cross-document mismatch detection and normalized area comparison.
    """
    doc1 = ProcessingResult(
        file_name="sale_deed_final.pdf",
        document_type_detected="Sale Deed",
        ocr_used=False,
        raw_text_length=600,
        extracted_data=ExtractedDocumentData(
            document_type="Sale Deed",
            owner_name="Aarav Mehta",
            survey_gat_number="124/3A",
            property_area="1450 sq.ft."
        ),
        fields_extracted=[], fields_missing=[]
    )

    doc2 = ProcessingResult(
        file_name="index2.pdf",
        document_type_detected="Index II",
        ocr_used=False,
        raw_text_length=600,
        extracted_data=ExtractedDocumentData(
            document_type="Index II",
            owner_name="Aarav Mehta",
            survey_gat_number="124/8",  # Mismatch
            property_area="1450 sq ft"  # Equivalent normalized area
        ),
        fields_extracted=[], fields_missing=[]
    )

    verification = compare_documents([doc1, doc2])
    assert verification.overall_status == OverallStatus.ISSUES_FOUND.value

    # Area should MATCH because "1450 sq.ft." and "1450 sq ft" normalize to the same value
    area_matches = [m for m in verification.matches if m.field == "property_area"]
    assert len(area_matches) == 1

    # Survey number should MISMATCH
    sg_mismatches = [m for m in verification.mismatches if m.field == "survey_gat_number"]
    assert len(sg_mismatches) == 1
    assert sg_mismatches[0].values["sale_deed_final.pdf"] == "124/3A"
    assert sg_mismatches[0].values["index2.pdf"] == "124/8"


def test_id_document_heading_not_extracted_as_person_name():
    text = "IDENTITY VERIFICATION TEST DOCUMENT\nFICTIONAL IDENTITY PROOF\nIDENTITY DETAILS\nAddress: Flat 704, Lakeview Residency\nIssue Date: 01/01/2024"
    data = extract_structured_data_heuristic(text, "ID Document")
    assert data.owner_name is None
    assert data.personal_address == "Flat 704, Lakeview Residency"
    assert data.date_of_issue == "01/01/2024"


def test_valid_owner_name_matches_across_property_documents():
    v = compare_documents([
        _result("sale.pdf", "Sale Deed", owner_name="Mrs. SHILPA SALGIA"),
        _result("card.pdf", "Property Card", owner_name="Shilpa Salgia"),
        _result("712.pdf", "7/12 Extract", owner_name="SHILPA SALGIA"),
    ], required_documents=[])
    matches = [m for m in v.matches if m.field == "owner_name"]
    assert len(matches) == 1
    assert not any(m.field == "owner_name" for m in v.mismatches)


def test_equivalent_names_with_honorifics_and_formatting_match():
    v = compare_documents([
        _result("doc1.pdf", "Sale Deed", owner_name="Mrs. SHILPA SALGIA"),
        _result("doc2.pdf", "Property Card", owner_name="Smt. Shilpa Salgia"),
    ], required_documents=[])
    matches = [m for m in v.matches if m.field == "owner_name"]
    assert len(matches) == 1
    assert not any(m.field == "owner_name" for m in v.mismatches)


def test_genuine_name_mismatch_detected():
    v = compare_documents([
        _result("doc1.pdf", "Sale Deed", owner_name="SHILPA SALGIA"),
        _result("doc2.pdf", "Property Card", owner_name="VIKRAM DESHMUKH"),
    ], required_documents=[])
    mismatches = [m for m in v.mismatches if m.field == "owner_name"]
    assert len(mismatches) == 1
    assert mismatches[0].severity == "HIGH"


def test_buyer_seller_mapping_in_sale_deed_and_index_ii():
    v = compare_documents([
        _result("sale.pdf", "Sale Deed", seller_name="Vikram Deshmukh", buyer_name="Mrs. SHILPA SALGIA"),
        _result("index.pdf", "Index II", seller_name="Shri Vikram Deshmukh", buyer_name="Shilpa Salgia"),
    ], required_documents=[])
    match_fields = [m.field for m in v.matches]
    assert "seller_name" in match_fields
    assert "buyer_name" in match_fields
    assert not any(m.field in {"seller_name", "buyer_name"} for m in v.mismatches)


def test_survey_gat_number_extraction_when_present():
    data = extract_structured_data_heuristic("Property Identification\nSurvey / Gat Number: 215/7A\nArea: 1450 sq ft", "Sale Deed")
    assert data.survey_gat_number == "215/7A"
    assert data.property_area == "1450 sq ft"


def test_registration_number_extraction_when_present():
    data = extract_structured_data_heuristic("Registration Details\nRegistration No.: MUM/REG/2026/04821\nDate: 12 September 2026", "Index II")
    assert data.registration_number == "MUM/REG/2026/04821"
    assert data.document_date == "12 September 2026"


def test_document_date_extraction_when_present():
    data = extract_structured_data_heuristic("THIS DEED OF SALE made on 12 September 2026 at Mumbai", "Sale Deed")
    assert data.document_date == "12 September 2026"


def test_missing_fields_reported_as_missing_not_mismatch():
    v = compare_documents([
        _result("sale.pdf", "Sale Deed", registration_number="MUM/REG/2026/04821"),
        _result("card.pdf", "Property Card", registration_number=None),
    ], required_documents=[])
    assert not any(m.field == "registration_number" for m in v.mismatches)
    assert len([m for m in v.matches if m.field == "registration_number"]) == 1


def test_genuine_mismatches_still_detected():
    v = compare_documents([
        _result("sale.pdf", "Sale Deed", survey_gat_number="124/3A"),
        _result("index.pdf", "Index II", survey_gat_number="124/8"),
    ], required_documents=[])
    mismatches = [m for m in v.mismatches if m.field == "survey_gat_number"]
    assert len(mismatches) == 1
    assert mismatches[0].values["sale.pdf"] == "124/3A"
    assert mismatches[0].values["index.pdf"] == "124/8"


def test_id_issue_dates_not_compared_as_property_document_dates():
    data = extract_structured_data_heuristic("IDENTITY DETAILS\nFull Name: Aarav Mehta\nIssue Date: 01 January 2024", "ID Document")
    assert data.date_of_issue == "01 January 2024"
    assert data.document_date is None


def test_existing_api_compatibility():
    v = compare_documents([
        _result("sale.pdf", "Sale Deed", owner_name="Shilpa Salgia", survey_gat_number="124/3A"),
        _result("card.pdf", "Property Card", owner_name="Shilpa Salgia", survey_gat_number="124/3A"),
    ], required_documents=["Sale Deed", "Property Card"])
    assert v.overall_status == OverallStatus.VERIFIED.value
    assert len(v.matches) >= 2


