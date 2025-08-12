"""
Logging configuration for the document classification system.

This module sets up structured logging with proper formatting,
log levels, and output destinations for monitoring and debugging.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
import json

from .config import settings


def setup_logging() -> None:
    """
    Configure application logging with proper formatting and handlers.
    """
    # Create logs directory
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "application.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "errors.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

    # Classification specific handler
    classification_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "classification.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8",
    )
    classification_handler.setLevel(logging.INFO)
    classification_handler.setFormatter(detailed_formatter)

    # Add classification handler to classification logger
    classification_logger = logging.getLogger("src.classification")
    classification_logger.addHandler(classification_handler)

    # Performance metrics handler
    metrics_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "metrics.log"),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    metrics_handler.setLevel(logging.INFO)
    metrics_formatter = logging.Formatter("%(asctime)s | %(message)s")
    metrics_handler.setFormatter(metrics_formatter)

    # Create metrics logger
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(logging.INFO)
    metrics_logger.addHandler(metrics_handler)
    metrics_logger.propagate = False  # Don't propagate to root logger

    logging.info("Logging system initialized")


class MetricsLogger:
    """
    Logger for performance and business metrics.
    """

    def __init__(self):
        """Initialize metrics logger."""
        self.logger = logging.getLogger("metrics")

    def log_classification_metrics(
        self,
        task_id: str,
        filename: str,
        category: str,
        confidence: float,
        processing_time: float,
        extracted_text_length: int,
        success: bool = True,
    ) -> None:
        """
        Log classification metrics.

        Args:
            task_id: Task identifier.
            filename: Document filename.
            category: Classified category.
            confidence: Classification confidence.
            processing_time: Processing time in seconds.
            extracted_text_length: Length of extracted text.
            success: Whether classification was successful.
        """
        metrics = {
            "event_type": "classification",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "filename": filename,
            "category": category,
            "confidence": confidence,
            "processing_time": processing_time,
            "extracted_text_length": extracted_text_length,
            "success": success,
        }

        self.logger.info(json.dumps(metrics))

    def log_upload_metrics(
        self,
        task_id: str,
        filename: str,
        file_size_bytes: int,
        client_ip: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log file upload metrics.

        Args:
            task_id: Task identifier.
            filename: Original filename.
            file_size_bytes: File size in bytes.
            client_ip: Client IP address.
            success: Whether upload was successful.
            error_message: Error message if failed.
        """
        metrics = {
            "event_type": "upload",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "filename": filename,
            "file_size_bytes": file_size_bytes,
            "client_ip": client_ip,
            "success": success,
            "error_message": error_message,
        }

        self.logger.info(json.dumps(metrics))

    def log_system_metrics(
        self,
        active_tasks: int,
        queued_tasks: int,
        completed_tasks: int,
        failed_tasks: int,
        aws_textract_healthy: bool,
        aws_bedrock_healthy: bool,
    ) -> None:
        """
        Log system health metrics.

        Args:
            active_tasks: Number of active tasks.
            queued_tasks: Number of queued tasks.
            completed_tasks: Number of completed tasks.
            failed_tasks: Number of failed tasks.
            aws_textract_healthy: Textract service health.
            aws_bedrock_healthy: Bedrock service health.
        """
        metrics = {
            "event_type": "system_health",
            "timestamp": datetime.utcnow().isoformat(),
            "active_tasks": active_tasks,
            "queued_tasks": queued_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "aws_textract_healthy": aws_textract_healthy,
            "aws_bedrock_healthy": aws_bedrock_healthy,
        }

        self.logger.info(json.dumps(metrics))


class PerformanceLogger:
    """
    Logger for performance monitoring and debugging.
    """

    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger("performance")

    def log_execution_time(
        self, operation: str, execution_time: float, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log execution time for operations.

        Args:
            operation: Operation name.
            execution_time: Execution time in seconds.
            metadata: Additional metadata.
        """
        log_data = {
            "operation": operation,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            log_data.update(metadata)

        self.logger.info(f"Performance: {operation} took {execution_time:.3f}s")

        # Log detailed data to metrics
        metrics_logger = logging.getLogger("metrics")
        log_data["event_type"] = "performance"
        metrics_logger.info(json.dumps(log_data))


def get_metrics_logger() -> MetricsLogger:
    """
    Get metrics logger instance.

    Returns:
        MetricsLogger: Metrics logger instance.
    """
    return MetricsLogger()


def get_performance_logger() -> PerformanceLogger:
    """
    Get performance logger instance.

    Returns:
        PerformanceLogger: Performance logger instance.
    """
    return PerformanceLogger()


# Initialize logging when module is imported
setup_logging()
