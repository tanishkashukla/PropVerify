import os
import sys

import pytest
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.document_processing import extractor
from backend.models.document import ExtractedDocumentData, ProcessingResult
from backend.services import ai_service
from backend.verification.comparator import compare_documents
from backend.verification.result import OverallStatus


def test_ai_success_records_ai_without_fallback(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(ai_service.settings, "GROQ_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service, "_extract_with_configured_provider", lambda *_: (ExtractedDocumentData(owner_name="Riya Sharma"), None))
    data, method, fallback, diagnostic = ai_service.extract_structured_data_with_status("some readable text", "Sale Deed")
    assert data.owner_name == "Riya Sharma"
    assert (method, fallback, diagnostic) == ("ai", False, None)


def test_ai_failure_and_deterministic_success_is_recovered_silently(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(ai_service.settings, "GROQ_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service, "_extract_with_configured_provider", lambda *_: (None, "private provider diagnostic"))
    monkeypatch.setattr(ai_service, "extract_structured_data_heuristic", lambda *_: ExtractedDocumentData(owner_name="Riya Sharma"))
    data, method, fallback, diagnostic = ai_service.extract_structured_data_with_status("some readable text", "Sale Deed")
    assert data.owner_name == "Riya Sharma"
    assert (method, fallback) == ("deterministic", True)
    assert diagnostic == "private provider diagnostic"


def test_ai_and_deterministic_failure_becomes_error(monkeypatch):
    monkeypatch.setattr(ai_service.settings, "AI_PROVIDER", "groq")
    monkeypatch.setattr(ai_service.settings, "GROQ_API_KEY", "test-secret")
    monkeypatch.setattr(ai_service, "_extract_with_configured_provider", lambda *_: (None, "private provider diagnostic"))
    monkeypatch.setattr(ai_service, "extract_structured_data_heuristic", lambda *_: (_ for _ in ()).throw(RuntimeError("deterministic failure")))
    monkeypatch.setattr(extractor.settings, "MIN_TEXT_THRESHOLD", 1)
    monkeypatch.setattr(extractor, "extract_text_from_pdf", lambda *_args, **_kwargs: ("Readable property document text.", 1))
    monkeypatch.setattr(extractor, "classify_document", lambda *_args, **_kwargs: "Sale Deed")
    monkeypatch.setattr(extractor, "extract_structured_data_with_status", ai_service.extract_structured_data_with_status)
    result = extractor.process_document(b"pdf-bytes", filename="failed.pdf")
    verification = compare_documents([result], required_documents=[])
    assert result.errors
    assert "deterministic failure" not in " ".join(result.errors)
    assert verification.overall_status == OverallStatus.ERROR.value
    assert verification.processing_status == "failed"
    assert verification.warnings


def test_actual_mismatch_stays_issues_found_with_successful_deterministic_results():
    def result(name, survey):
        return ProcessingResult(
            file_name=name,
            document_type_detected="Sale Deed",
            ocr_used=False,
            raw_text_length=100,
            extracted_data=ExtractedDocumentData(document_type="Sale Deed", survey_gat_number=survey),
            fields_extracted=["document_type", "survey_gat_number"],
            fields_missing=[],
            extraction_used="deterministic",
            fallback_used=True,
        )

    verification = compare_documents([result("a.pdf", "215/7A"), result("b.pdf", "215/9B")], required_documents=[])
    assert verification.overall_status == OverallStatus.ISSUES_FOUND.value
    assert verification.processing_status == "completed"
    assert len([item for item in verification.mismatches if item.field == "survey_gat_number"]) == 1
    assert "fallback" not in " ".join(verification.warnings).lower()


def test_groq_uses_reasoning_json_when_final_content_is_not_structured(monkeypatch, caplog):
    monkeypatch.setattr(ai_service.settings, "GROQ_API_KEY", "groq-test-secret")
    monkeypatch.setattr(ai_service.settings, "GROQ_MODEL", "openai/gpt-oss-20b")

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"finish_reason": "stop", "message": {
                "content": "4",
                "reasoning": 'The extracted fields are: {"ownerName":"Riya Sharma","sellerName":"Vikram Deshmukh","buyerName":"Riya Sharma","propertyAddress":"Plot 42, Green Meadows","surveyGatNumber":"215/7A","propertyArea":"1500 sq. ft.","registrationNumber":"PUN/REG/2026/06754","documentDate":"18 September 2026","documentNumber":"null"}',
            }}]}

    def fake_post(*_args, **kwargs):
        assert kwargs["json"]["model"] == "openai/gpt-oss-20b"
        return Response()

    monkeypatch.setattr(ai_service.httpx, "post", fake_post)
    with caplog.at_level(logging.INFO, logger="propverify.ai"):
        data, error = ai_service.extract_structured_data_groq("source text", "Sale Deed")
    assert error is None
    assert data.owner_name == "Riya Sharma"
    assert data.seller_name == "Vikram Deshmukh"
    assert data.buyer_name == "Riya Sharma"
    assert data.property_address == "Plot 42, Green Meadows"
    assert data.survey_gat_number == "215/7A"
    assert data.property_area == "1500 sq. ft."
    assert data.registration_number == "PUN/REG/2026/06754"
    assert data.document_date == "18 September 2026"
    assert data.document_number is None
    assert "Groq extraction request started" in caplog.text
    assert "Groq extraction request succeeded" in caplog.text
    assert "model=openai/gpt-oss-20b" in caplog.text


def test_groq_failure_diagnostic_redacts_configured_key(monkeypatch, caplog):
    secret = "groq-test-secret-value"
    monkeypatch.setattr(ai_service.settings, "GROQ_API_KEY", secret)
    monkeypatch.setattr(ai_service.httpx, "post", lambda *_args, **_kwargs: (_ for _ in ()).throw(ai_service.httpx.ConnectError(f"connection failed using {secret}")))
    with caplog.at_level(logging.INFO, logger="propverify.ai"):
        data, warning = ai_service.extract_structured_data_groq("source text", "Sale Deed")
    assert data is None and warning == "Configured AI extraction provider failed."
    assert "request started" in caplog.text
    assert "request failed" in caplog.text
    assert secret not in caplog.text
    assert "[REDACTED]" in caplog.text

