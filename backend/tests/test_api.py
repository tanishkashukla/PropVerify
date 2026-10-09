import glob
import os
import sys
from fastapi.testclient import TestClient
import pymupdf
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app
from backend.config import settings
from backend.models.document import ExtractedDocumentData, ProcessingResult
from backend.verification.result import VerificationResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def avoid_external_ai_requests(monkeypatch):
    # API integration tests exercise the deterministic fallback. Groq request
    # behavior is covered separately with mocked OpenAI-compatible responses.
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["health_check"] == "/api/health"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    health = response.json()
    assert health["status"] == "healthy"
    assert isinstance(health["gemini_configured"], bool)
    assert "key_source" in health


def test_ocr_not_loaded_on_app_startup():
    from backend.document_processing.ocr import is_easyocr_loaded
    # OCR initialization must remain deferred until a scanned image upload occurs.
    # At app startup, the EasyOCR model cache must not be pre-loaded in memory.
    assert is_easyocr_loaded() is False



def test_process_document_api():
    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents"))
    pdf_files = sorted(glob.glob(os.path.join(doc_dir, "*.pdf")))

    assert len(pdf_files) > 0, "No test PDF files found"

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/process-document",
                files={"file": (filename, f, "application/pdf")}
            )

        assert response.status_code == 200, f"API call failed for {filename}: {response.text}"
        data = response.json()

        assert "document_type_detected" in data
        assert "extracted_data" in data
        assert "fields_extracted" in data
        assert "fields_missing" in data


def test_process_scanned_document_api_runs_english_ocr():
    image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents/scanned_id_sample.png"))
    assert os.path.exists(image_path), "Scanned English sample is missing"
    with open(image_path, "rb") as image:
        response = client.post(
            "/api/process-document",
            files={"file": ("scanned_id_sample.png", image, "image/png")},
        )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ocr_used"] is True
    assert result["raw_text_length"] > 0
    assert result["errors"] == []


def test_verify_documents_api():
    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents"))
    pdf_files = sorted(glob.glob(os.path.join(doc_dir, "*.pdf")))

    files_payload = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        files_payload.append(("files", (filename, open(pdf_path, "rb"), "application/pdf")))

    response = client.post("/api/verify-documents", files=files_payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "ISSUES_FOUND"
    assert data["documents_processed"] == 5
    assert len(data["processed_documents"]) == 5
    assert isinstance(data["ai_used"], bool)
    assert data["processing_status"] == "completed"
    assert all(document["extraction_used"] == "deterministic" for document in data["processed_documents"])
    assert all(document["fallback_used"] is False for document in data["processed_documents"])
    assert not any("Gemini extraction failed" in warning for warning in data["warnings"])
    mismatches = {item["field"]: item for item in data["mismatches"]}
    assert set(mismatches) == {"survey_gat_number", "document_date"}
    assert mismatches["survey_gat_number"]["values"]["03_Index_II.pdf"] == "124/8"
    assert mismatches["survey_gat_number"]["conflicting_documents"] == ["03_Index_II.pdf"]
    assert mismatches["document_date"]["values"]["02_Property_Card.pdf"] == "15 September 2026"
    assert "registration_number" not in mismatches

    report = client.post("/api/generate-report", json=data)
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")
    pdf_doc = pymupdf.open(stream=report.content, filetype="pdf")
    report_text = "\n".join(page.get_text() for page in pdf_doc)
    pdf_doc.close()
    assert "EXTRACTED DOCUMENT INFORMATION" in report_text
    assert "Aarav Mehta" in report_text


def test_verify_reports_selected_missing_document(monkeypatch):
    def fake_process_document(file_input, filename, document_type_override=None):
        detected = document_type_override or "Sale Deed"
        return ProcessingResult(
            file_name=filename,
            document_type_detected=detected,
            ocr_used=False,
            raw_text_length=50,
            extracted_data=ExtractedDocumentData(document_type=detected),
            fields_extracted=["document_type"],
            fields_missing=["owner_name"],
            ai_used=True,
        )

    monkeypatch.setattr("backend.main.process_document", fake_process_document)
    response = client.post(
        "/api/verify-documents",
        files={"files": ("sale.pdf", b"test", "application/pdf")},
        data={
            "required_documents_json": '["Sale Deed", "7/12 Extract"]',
            "document_types_json": '["Sale Deed"]',
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["required_documents"] == ["sale_deed", "7_12_extract"]
    assert [item["expected_document_type"] for item in result["missing_documents"]] == ["7_12_extract"]


def test_empty_required_document_selection_stays_empty(monkeypatch):
    def fake_process_document(file_input, filename, document_type_override=None):
        detected = document_type_override or "Sale Deed"
        return ProcessingResult(
            file_name=filename,
            document_type_detected=detected,
            ocr_used=False,
            raw_text_length=50,
            extracted_data=ExtractedDocumentData(document_type=detected),
            fields_extracted=["document_type"],
            fields_missing=[],
            ai_used=True,
        )

    monkeypatch.setattr("backend.main.process_document", fake_process_document)
    response = client.post(
        "/api/verify-documents",
        files={"files": ("sale.pdf", b"test", "application/pdf")},
        data={"required_documents_json": "[]", "document_types_json": '["Sale Deed"]'},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["required_documents"] == []
    assert result["missing_documents"] == []


def test_invalid_required_document_json_returns_422():
    response = client.post(
        "/api/verify-documents",
        files={"files": ("sale.pdf", b"test", "application/pdf")},
        data={"required_documents_json": "not-json"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "required_documents_json must be valid JSON."


def test_cors_preflight_accepts_local_frontends():
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = client.options(
            "/api/verify-documents",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_generate_report_returns_pdf():
    result = VerificationResult(
        overall_status="MISSING_DOCUMENTS",
        documents_processed=1,
        required_documents=["Sale Deed", "7/12 Extract"],
        provided_documents=["Sale Deed"],
        missing_documents=[{
            "expected_document_type": "7/12 Extract",
            "message": "7/12 Extract was selected as required but was not provided.",
        }],
    )
    response = client.post("/api/generate-report", json=result.model_dump())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_report_uses_one_final_status_for_each_field():
    result = VerificationResult(
        overall_status="ISSUES_FOUND",
        documents_processed=2,
        required_documents=[],
        provided_documents=["Sale Deed", "Index II"],
        matches=[
            {"field": "seller_name", "matched_value": "Vikram Deshmukh", "documents_compared": {"sale.pdf": "Vikram Deshmukh", "index.pdf": "Vikram Deshmukh"}},
            {"field": "property_area", "matched_value": "1500 sq. ft.", "documents_compared": {"sale.pdf": "1500 sq. ft.", "index.pdf": "1500 sq. ft."}},
        ],
        mismatches=[{
            "field": "survey_gat_number", "values": {"sale.pdf": "215/7A", "index.pdf": "215/9B"},
            "severity": "HIGH", "message": "Survey / Gat Number differs in Index II.", "conflicting_documents": ["index.pdf"],
        }],
    )
    response = client.post("/api/generate-report", json=result.model_dump())
    assert response.status_code == 200
    report = pymupdf.open(stream=response.content, filetype="pdf")
    text = "\n".join(page.get_text() for page in report)
    lines = text.splitlines()
    assert lines[lines.index("Fields Evaluated") + 1] == "3"
    assert lines[lines.index("Matched Fields") + 1] == "2"
    assert lines[lines.index("Mismatched Fields") + 1] == "1"
    assert lines[lines.index("Missing Fields") + 1] == "0"
    assert text.count("Seller Name") == 1
    assert text.count("Property Area") == 1
    assert text.count("Survey Gat Number") == 2  # Results table and mismatch detail section.
    assert "Vikram Deshmukh" in text
    assert "1500 sq. ft." in text
