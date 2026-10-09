
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from backend.config import settings
from backend.document_processing.extractor import DocumentInputError, process_document
from backend.models.document import (
    DocumentType,
    ProcessingResult,
    display_document_type,
    normalize_document_type,
)
from backend.services.report_generator import generate_pdf_report
from backend.verification.comparator import compare_documents
from backend.verification.result import (
    MissingDocument,
    OverallStatus,
    SeverityLevel,
    VerificationResult,
)

# Configure logging to unbuffered stdout so application logs flush immediately in cloud platforms (Render).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("propverify.api")

SUPPORTED_DOCUMENT_TYPES = {
    item.value for item in DocumentType if item != DocumentType.UNKNOWN
}
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.getenv("PORT", "8001")
    logger.info(
        "[PropVerify] Server starting up. Listening for requests on PORT=%s (Gemini configured=%s)...",
        port,
        bool(settings.GEMINI_API_KEY),
    )
    yield
    logger.info("[PropVerify] Server shutting down.")


app = FastAPI(
    title="PropVerify Document Processing & Verification API",
    description=(
        "English property-document extraction, cross-document verification, "
        "and PDF report generation."
    ),
    version="3.1.0",
    lifespan=lifespan,
)

# Allow the deployed Vercel frontend, preview frontends, and local development frontends.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://prop-verify.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
def root_check():
    return {
        "status": "healthy",
        "service": "PropVerify Document Processing & Verification API",
        "health_check": "/api/health",
        "version": "3.1.0",
    }


@app.get("/api/health")
def health_check():
    # Health is local configuration only; never makes a Gemini request.
    return {
        "status": "healthy",
        "service": "PropVerify Verification Engine",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "key_source": settings.KEY_SOURCE,
    }



async def _read_upload(file: UploadFile) -> bytes:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Every uploaded document must have a filename.",
        )

    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail=f"The uploaded file '{file.filename}' is empty.",
        )

    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"'{file.filename}' exceeds the 25 MB upload limit.",
        )

    return content


def _parse_string_list(
    value: Optional[str],
    field_label: str,
) -> Optional[List[str]]:
    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=422,
            detail=f"{field_label} must be valid JSON.",
        ) from None

    if not isinstance(parsed, list) or any(
        not isinstance(item, str) for item in parsed
    ):
        raise HTTPException(
            status_code=422,
            detail=f"{field_label} must be a JSON array of strings.",
        )

    return parsed


@app.post("/api/process-document", response_model=ProcessingResult)
async def process_uploaded_document(file: UploadFile = File(...)):
    content = await _read_upload(file)

    try:
        return await run_in_threadpool(
            process_document,
            file_input=content,
            filename=file.filename,
        )
    except DocumentInputError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    except Exception as error:
        logger.exception(
            "Unexpected document processing failure (%s)",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed. Check the server configuration "
                "and try again."
            ),
        ) from None


@app.post("/api/verify-documents", response_model=VerificationResult)
async def verify_uploaded_documents(
    files: List[UploadFile] = File(...),
    required_documents: Optional[List[str]] = Form(None),
    required_documents_json: Optional[str] = Form(None),
    document_types_json: Optional[str] = Form(None),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one document to start verification.",
        )

    if required_documents_json is not None:
        required_values = _parse_string_list(
            required_documents_json,
            "required_documents_json",
        )
    else:
        required_values = required_documents

    parsed_required_docs = None

    if required_values is not None:
        parsed_required_docs = list(
            dict.fromkeys(
                normalize_document_type(value)
                for value in required_values
            )
        )

        if any(
            doc not in SUPPORTED_DOCUMENT_TYPES
            for doc in parsed_required_docs
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "required_documents contains an unsupported "
                    "document type."
                ),
            )

    selected_types = _parse_string_list(
        document_types_json,
        "document_types_json",
    )

    if selected_types is not None:
        if len(selected_types) != len(files):
            raise HTTPException(
                status_code=422,
                detail=(
                    "document_types_json must include one selection "
                    "for each uploaded file."
                ),
            )

        selected_types = [
            normalize_document_type(doc) if doc else ""
            for doc in selected_types
        ]

        if any(
            doc and doc not in SUPPORTED_DOCUMENT_TYPES
            for doc in selected_types
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "document_types_json contains an unsupported "
                    "document type."
                ),
            )
    else:
        selected_types = [""] * len(files)

    results: List[ProcessingResult] = []

    logger.info(
        "[PropVerify] Verification started (documents=%d)",
        len(files),
    )

    for index, file in enumerate(files):
        content = await _read_upload(file)

        extension = (
            "." + file.filename.rsplit(".", 1)[-1].lower()
            if "." in file.filename
            else ""
        )

        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type for '{file.filename}'. "
                    "Upload PDF, JPG, or PNG."
                ),
            )

        try:
            result = await run_in_threadpool(
                process_document,
                file_input=content,
                filename=file.filename,
                document_type_override=selected_types[index] or None,
            )
        except DocumentInputError as error:
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}': {error}",
            ) from None
        except Exception as error:
            logger.exception(
                "Unexpected document processing failure (%s)",
                type(error).__name__,
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Processing '{file.filename}' failed. "
                    "Check the server logs for details."
                ),
            ) from None

        canonical_type = normalize_document_type(
            result.document_type_detected
        )

        if canonical_type:
            result = result.model_copy(
                update={
                    "document_type_detected": canonical_type,
                    "extracted_data": result.extracted_data.model_copy(
                        update={"document_type": canonical_type}
                    ),
                }
            )

        results.append(result)

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No uploaded documents could be processed.",
        )

    canonical_required_docs = (
        parsed_required_docs
        if parsed_required_docs is not None
        else [
            item.value
            for item in DocumentType
            if item != DocumentType.UNKNOWN
        ]
    )

    canonical_provided_docs = list(
        dict.fromkeys(
            normalize_document_type(result.document_type_detected)
            or result.document_type_detected
            for result in results
        )
    )

    # Required type selection and presence are canonical IDs here.
    # Adapt to readable labels only at the comparator boundary.
    provided_set = set(canonical_provided_docs)

    missing_required_types = [
        doc
        for doc in canonical_required_docs
        if doc not in provided_set
    ]

    comparator_results = [
        result.model_copy(
            update={
                "document_type_detected": display_document_type(
                    result.document_type_detected
                )
            }
        )
        for result in results
    ]

    try:
        verification = compare_documents(
            comparator_results,
            required_documents=[],
        )
    except Exception as error:
        logger.exception(
            "Verification comparison failed (%s)",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Document comparison failed. "
                "Check the server logs for details."
            ),
        ) from None

    canonical_missing_docs = [
        MissingDocument(
            expected_document_type=doc,
            status="MISSING",
            severity=SeverityLevel.HIGH.value,
            message=(
                f"{display_document_type(doc)} was selected as required "
                "but was not provided."
            ),
        )
        for doc in missing_required_types
    ]

    status = verification.overall_status

    if (
        status
        not in {
            OverallStatus.ISSUES_FOUND.value,
            OverallStatus.ERROR.value,
        }
        and canonical_missing_docs
    ):
        status = OverallStatus.MISSING_DOCUMENTS.value

    verification = verification.model_copy(
        update={
            "overall_status": status,
            "required_documents": canonical_required_docs,
            "provided_documents": canonical_provided_docs,
            "missing_documents": canonical_missing_docs,
            "processed_documents": results,
        }
    )

    logger.info(
        "[PropVerify] Verification completed "
        "(status=%s, mismatches=%d, missing_documents=%d, ai_used=%s)",
        verification.overall_status,
        len(verification.mismatches),
        len(verification.missing_documents),
        verification.ai_used,
    )

    return verification


@app.post("/api/generate-report")
async def generate_verification_report(result: VerificationResult):
    try:
        pdf_bytes = await run_in_threadpool(
            generate_pdf_report,
            result,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    "attachment; filename=PropVerify_Verification_Report.pdf"
                )
            },
        )
    except Exception as error:
        logger.exception(
            "Report generation failed (%s)",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Report generation failed. "
                "Check the server logs for details."
            ),
        ) from None


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)

