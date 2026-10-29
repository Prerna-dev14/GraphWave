"""GraphWeave standard exceptions and consistent API error envelope."""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized API Error Envelope."""
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic details")
    trace_id: Optional[str] = Field(default=None, description="Correlation trace ID")


class GraphWeaveException(Exception):
    """Base exception for all domain and operational errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ScopeViolationError(GraphWeaveException):
    def __init__(self, message: str = "Access denied: entity or document outside authorized scope"):
        super().__init__(message, code="SCOPE_VIOLATION")


class DocumentNotFoundError(GraphWeaveException):
    def __init__(self, document_id: str):
        super().__init__(f"Document '{document_id}' not found", code="DOCUMENT_NOT_FOUND", details={"document_id": document_id})


class IngestionJobError(GraphWeaveException):
    def __init__(self, job_id: str, reason: str):
        super().__init__(f"Ingestion job '{job_id}' failed: {reason}", code="INGESTION_JOB_FAILED", details={"job_id": job_id, "reason": reason})


class GraphTimeoutError(GraphWeaveException):
    def __init__(self, timeout_sec: float):
        super().__init__(f"Graph traversal exceeded budget of {timeout_sec}s", code="GRAPH_TRAVERSAL_TIMEOUT", details={"timeout": timeout_sec})


class SchemaValidationError(GraphWeaveException):
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Ontology schema validation failed: {reason}", code="SCHEMA_VALIDATION_ERROR", details=details)
