"""
Pydantic models for API request and response schemas.

This module defines all data models used in the FastAPI application
with proper validation, type hints, and documentation.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentType(str, Enum):
    """Enumeration of supported document types."""

    GOVERNMENT_ID = "Government ID"
    PAYSLIP = "Payslip"
    BANK_STATEMENT = "Bank Statement"
    EMPLOYMENT_LETTER = "Employment Letter"
    UTILITY_BILL = "Utility Bill"
    SAVINGS_STATEMENT = "Savings Statement"
    UNKNOWN = "Unknown"


class ProcessingStatus(str, Enum):
    """Enumeration of processing status values."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response model for document upload."""

    task_id: str = Field(..., description="Unique task identifier")
    filename: str = Field(..., description="Original filename")
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(
        default="Document queued for processing", description="Status message"
    )
    upload_time: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )


class ClassificationResult(BaseModel):
    """Model for document classification result."""

    category: DocumentType = Field(..., description="Classified document type")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Classification confidence score"
    )
    reasoning: str = Field(..., description="Classification reasoning")
    needs_manual_review: bool = Field(
        default=False, description="Whether document needs manual review"
    )

    @validator("confidence")
    def validate_confidence(cls, v):
        """Validate confidence score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class DocumentProcessingResult(BaseModel):
    """Complete document processing result."""

    task_id: str = Field(..., description="Task identifier")
    filename: str = Field(..., description="Original filename")
    status: ProcessingStatus = Field(..., description="Processing status")
    classification: Optional[ClassificationResult] = Field(
        None, description="Classification result"
    )
    extracted_text_length: Optional[int] = Field(
        None, description="Length of extracted text"
    )
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class TaskStatusResponse(BaseModel):
    """Response model for task status queries."""

    task_id: str = Field(..., description="Task identifier")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: Optional[str] = Field(None, description="Progress description")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    task_id: Optional[str] = Field(None, description="Related task ID if applicable")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str = Field(default="healthy", description="Service status")
    service: str = Field(default="document-classification", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    aws_services: Optional[Dict[str, str]] = Field(
        None, description="AWS services connectivity status"
    )


class EvaluationMetrics(BaseModel):
    """Model for classification evaluation metrics."""

    document_type: DocumentType = Field(..., description="Document type")
    precision: float = Field(..., ge=0.0, le=1.0, description="Precision score")
    recall: float = Field(..., ge=0.0, le=1.0, description="Recall score")
    f1_score: float = Field(..., ge=0.0, le=1.0, description="F1 score")
    support: int = Field(..., ge=0, description="Number of samples")


class OverallMetrics(BaseModel):
    """Model for overall system metrics."""

    overall_accuracy: float = Field(..., ge=0.0, le=1.0, description="Overall accuracy")
    macro_avg_precision: float = Field(
        ..., ge=0.0, le=1.0, description="Macro average precision"
    )
    macro_avg_recall: float = Field(
        ..., ge=0.0, le=1.0, description="Macro average recall"
    )
    macro_avg_f1: float = Field(
        ..., ge=0.0, le=1.0, description="Macro average F1 score"
    )
    weighted_avg_precision: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted average precision"
    )
    weighted_avg_recall: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted average recall"
    )
    weighted_avg_f1: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted average F1 score"
    )
    total_samples: int = Field(..., ge=0, description="Total number of samples")


class EvaluationReport(BaseModel):
    """Complete evaluation report model."""

    report_id: str = Field(..., description="Report identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report creation time"
    )
    per_class_metrics: List[EvaluationMetrics] = Field(
        ..., description="Per-class metrics"
    )
    overall_metrics: OverallMetrics = Field(..., description="Overall system metrics")
    confusion_matrix: List[List[int]] = Field(..., description="Confusion matrix")
    class_names: List[str] = Field(..., description="Class names for confusion matrix")


class BatchUploadRequest(BaseModel):
    """Request model for batch document upload."""

    files: List[str] = Field(..., description="List of file identifiers")
    priority: str = Field(default="normal", description="Processing priority")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload."""

    batch_id: str = Field(..., description="Batch identifier")
    task_ids: List[str] = Field(..., description="Individual task identifiers")
    total_files: int = Field(..., description="Total number of files")
    status: str = Field(default="queued", description="Batch status")


class SystemStatsResponse(BaseModel):
    """System statistics response model."""

    total_documents_processed: int = Field(..., description="Total documents processed")
    documents_by_type: Dict[str, int] = Field(..., description="Document count by type")
    average_processing_time: float = Field(
        ..., description="Average processing time in seconds"
    )
    success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Processing success rate"
    )
    queue_size: int = Field(..., description="Current queue size")
    active_tasks: int = Field(..., description="Currently active tasks")


class ConfigResponse(BaseModel):
    """Configuration response model."""

    max_file_size: int = Field(..., description="Maximum file size in bytes")
    supported_formats: List[str] = Field(..., description="Supported file formats")
    confidence_threshold: float = Field(..., description="Confidence threshold")
    processing_timeout: int = Field(..., description="Processing timeout in seconds")
