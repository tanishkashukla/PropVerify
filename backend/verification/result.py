from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field
from backend.models.document import ProcessingResult


class OverallStatus(str, Enum):
    VERIFIED = "VERIFIED"
    ISSUES_FOUND = "ISSUES_FOUND"
    MISSING_DOCUMENTS = "MISSING_DOCUMENTS"
    PROCESSING_INCOMPLETE = "PROCESSING_INCOMPLETE"
    ERROR = "ERROR"


class SeverityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FieldMismatch(BaseModel):
    field: str
    status: str = "MISMATCH"
    values: Dict[str, str] = Field(
        ...,
        description="Map of document filename to extracted field value"
    )
    severity: str = Field(
        default="HIGH",
        description="Severity level of the mismatch: HIGH, MEDIUM, LOW"
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the mismatch"
    )
    conflicting_documents: List[str] = Field(default_factory=list)


class FieldMatch(BaseModel):
    field: str
    status: str = "MATCH"
    matched_value: str = Field(
        ...,
        description="The normalized value that matched across all applicable documents"
    )
    documents_compared: Dict[str, str] = Field(
        ...,
        description="Map of document filename to extracted value"
    )


class FieldMissing(BaseModel):
    field: str
    status: str = "MISSING"
    document_name: str
    document_type: str
    severity: str = "MEDIUM"
    message: str


class MissingDocument(BaseModel):
    expected_document_type: str
    status: str = "MISSING"
    severity: str = "HIGH"
    message: str


class VerificationResult(BaseModel):
    overall_status: str = Field(
        ...,
        description="Overall verification status: VERIFIED, ISSUES_FOUND, MISSING_DOCUMENTS, PROCESSING_INCOMPLETE, or ERROR"
    )
    documents_processed: int = Field(
        ...,
        description="Total number of documents analyzed"
    )
    required_documents: List[str] = Field(
        default_factory=list,
        description="List of document types marked as required for this verification"
    )
    provided_documents: List[str] = Field(
        default_factory=list,
        description="List of document types provided in uploaded files"
    )
    matches: List[FieldMatch] = Field(
        default_factory=list,
        description="Fields that matched consistently across applicable documents"
    )
    mismatches: List[FieldMismatch] = Field(
        default_factory=list,
        description="Fields with conflicting values across documents"
    )
    missing_fields: List[FieldMissing] = Field(
        default_factory=list,
        description="Expected fields that were missing in specific documents"
    )
    missing_documents: List[MissingDocument] = Field(
        default_factory=list,
        description="Expected document types missing from the uploaded set"
    )
    processing_status: str = Field(
        default="completed",
        description="completed when extraction completed; failed when extraction had an unresolved system error"
    )
    ai_used: bool = False
    warnings: List[str] = Field(default_factory=list)
    processed_documents: List[ProcessingResult] = Field(default_factory=list)
