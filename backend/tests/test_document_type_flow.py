import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import settings
from backend.document_processing import extractor
from backend.main import app
from backend.models.document import (
    DocumentType, ExtractedDocumentData, ProcessingResult,
    normalize_document_type,
)

client = TestClient(app)
CANONICAL_TYPES = ["sale_deed", "property_card", "index_ii", "7_12_extract", "id_document"]
DISPLAY_TYPES = ["Sale Deed", "Property Card", "Index II", "7/12 Extract", "ID Document"]


@pytest.fixture(autouse=True)
def disable_external_ai_for_type_flow_tests(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")


@pytest.mark.parametrize("label,canonical", list(zip(DISPLAY_TYPES, CANONICAL_TYPES)))
def test_display_document_labels_normalize_to_canonical_ids(label, canonical):
    assert normalize_document_type(label) == canonical
    assert normalize_document_type(canonical) == canonical


def _install_fake_processor(monkeypatch, document_factory=None):
    def fake_process_document(file_input, filename, document_type_override=None):
        document_type = document_type_override or "sale_deed"
        extracted = document_factory(filename, document_type) if document_factory else ExtractedDocumentData(document_type=document_type)
        return ProcessingResult(
            file_name=filename,
            document_type_detected=document_type,
            ocr_used=False,
            raw_text_length=100,
            extracted_data=extracted,
            fields_extracted=["document_type"],
            fields_missing=[],
        )

    monkeypatch.setattr("backend.main.process_document", fake_process_document)


def _post(filename_types, required_types, monkeypatch, document_factory=None):
    _install_fake_processor(monkeypatch, document_factory)
    files = [
        ("files", (filename, b"fixture", "application/pdf"))
        for filename, _ in filename_types
    ]
    return client.post(
        "/api/verify-documents",
        files=files,
        data={
            "required_documents_json": __import__("json").dumps(required_types),
            "document_types_json": __import__("json").dumps([doc_type for _, doc_type in filename_types]),
        },
    )


def test_id_document_slug_is_recognized_as_provided_and_not_missing(monkeypatch):
    response = _post([("05_ID_Document_Oberoi_Test.pdf", "id_document")], ["id_document"], monkeypatch)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["processed_documents"][0]["document_type_detected"] == "id_document"
    assert result["provided_documents"] == ["id_document"]
    assert result["missing_documents"] == []


def test_id_document_is_missing_when_not_uploaded(monkeypatch):
    response = _post([("01_Sale_Deed_Oberoi_Test.pdf", "sale_deed")], ["sale_deed", "id_document"], monkeypatch)
    assert response.status_code == 200, response.text
    result = response.json()
    assert [item["expected_document_type"] for item in result["missing_documents"]] == ["id_document"]


def test_explicit_id_type_overrides_a_different_classifier_guess(monkeypatch):
    monkeypatch.setattr(extractor.settings, "MIN_TEXT_THRESHOLD", 1)
    monkeypatch.setattr(extractor, "extract_text_from_pdf", lambda *_args, **_kwargs: ("Readable identity document source text.", 1))
    monkeypatch.setattr(extractor, "classify_document", lambda *_args, **_kwargs: "property_card")
    calls = []

    def fake_extract(text, document_type, filename=""):
        calls.append(document_type)
        return ExtractedDocumentData(document_type=document_type, owner_name="Riya Sharma"), "ai", False, None

    monkeypatch.setattr(extractor, "extract_structured_data_with_status", fake_extract)
    result = extractor.process_document(b"pdf", "05_ID_Document_Oberoi_Test.pdf", document_type_override="id_document")
    assert calls == ["ID Document"]
    assert result.document_type_detected == "id_document"
    assert result.extracted_data.document_type == "id_document"


def test_all_five_display_labels_map_to_canonical_required_and_uploaded_values(monkeypatch):
    items = [(f"doc-{index}.pdf", label) for index, label in enumerate(DISPLAY_TYPES)]
    response = _post(items, DISPLAY_TYPES, monkeypatch)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["required_documents"] == CANONICAL_TYPES
    assert set(result["provided_documents"]) == set(CANONICAL_TYPES)
    assert result["missing_documents"] == []


def test_duplicate_index_ii_uploads_remain_separate_with_same_canonical_type(monkeypatch):
    response = _post(
        [("03_Index_II_Oberoi_Test.pdf", "index_ii"), ("03_Index_II_Oberoi_MISMATCH.pdf", "index_ii")],
        ["index_ii"],
        monkeypatch,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert [item["document_type_detected"] for item in result["processed_documents"]] == ["index_ii", "index_ii"]
    assert [item["file_name"] for item in result["processed_documents"]] == ["03_Index_II_Oberoi_Test.pdf", "03_Index_II_Oberoi_MISMATCH.pdf"]
    assert result["provided_documents"] == ["index_ii"]
    assert result["missing_documents"] == []


def test_six_document_verification_keeps_one_survey_mismatch_and_all_types_provided(monkeypatch):
    common = {
        "property_address": "Plot 42, Green Meadows, Baner, Pune, Maharashtra - 411045",
        "property_area": "1500 sq. ft. (139.35 sq. m.)",
        "registration_number": "PUN/REG/2026/06754",
        "document_date": "18 September 2026",
    }
    fixture_data = {
        "01_Sale_Deed_Oberoi_Test.pdf": dict(common, owner_name="Riya Sharma", seller_name="Vikram Deshmukh", buyer_name="Riya Sharma", survey_gat_number="215/7A"),
        "02_Property_Card_Oberoi_Test.pdf": dict(common, owner_name="Riya Sharma", survey_gat_number="215/7A"),
        "03_Index_II_Oberoi_Test.pdf": dict(common, seller_name="Vikram Deshmukh", buyer_name="Riya Sharma", survey_gat_number="215/7A"),
        "03_Index_II_Oberoi_MISMATCH.pdf": dict(common, seller_name="Vikram Deshmukh", buyer_name="Riya Sharma", survey_gat_number="215/9B"),
        "04_7_12_Extract_Oberoi_Test.pdf": dict(common, owner_name="Riya Sharma", survey_gat_number="215/7A"),
        "05_ID_Document_Oberoi_Test.pdf": {"owner_name": "Riya Sharma", "personal_address": "42 Green Meadows", "document_number": "IDP-7842-2026", "date_of_issue": "05 January 2024"},
    }

    def factory(filename, document_type):
        return ExtractedDocumentData(document_type=document_type, **fixture_data[filename])

    types = ["sale_deed", "property_card", "index_ii", "index_ii", "7_12_extract", "id_document"]
    filenames = list(fixture_data)
    response = _post(list(zip(filenames, types)), CANONICAL_TYPES, monkeypatch, factory)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["documents_processed"] == 6
    assert len(result["matches"]) == 7
    assert len(result["mismatches"]) == 1
    assert result["mismatches"][0]["field"] == "survey_gat_number"
    assert result["missing_fields"] == []
    assert result["missing_documents"] == []
    assert result["required_documents"] == CANONICAL_TYPES
    assert set(result["provided_documents"]) == set(CANONICAL_TYPES)

