"""
FastAPI routes for document classification API.

This module defines all API endpoints for file upload, status checking,
and result retrieval with proper error handling and background processing.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form
import logging

from .models import (
    UploadResponse,
    DocumentProcessingResult,
    TaskStatusResponse,
    HealthCheckResponse,
    ProcessingStatus,
)
from ..classification.agent import DocumentClassificationAgent
from ..utils.file_handler import FileValidator, FileStorage, ResultStorage
from ..utils.config import settings
from ..evaluation.metrics import MetricsCalculator

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize components
classification_agent = DocumentClassificationAgent()
file_validator = FileValidator()
file_storage = FileStorage()
result_storage = ResultStorage()
metrics_calculator = MetricsCalculator()

# In-memory task status tracking (use Redis in production)
task_status: Dict[str, str] = {}
task_progress: Dict[str, str] = {}


async def classify_document_task(pdf_bytes: bytes, task_id: str, filename: str) -> None:
    """
    Background task for document classification.

    Args:
        pdf_bytes: PDF file content.
        task_id: Unique task identifier.
        filename: Original filename.
    """
    try:
        logger.info(f"Starting background classification for task {task_id}")

        # Update task status
        task_status[task_id] = ProcessingStatus.PROCESSING.value
        task_progress[task_id] = "Initializing classification pipeline"

        # Update progress
        task_progress[task_id] = "Extracting text with AWS Textract"

        # Perform classification
        result = await classification_agent.classify_document(pdf_bytes, filename)
        result["task_id"] = task_id

        # Save result
        await result_storage.save_result(task_id, result)

        # Update final status
        task_status[task_id] = ProcessingStatus.COMPLETED.value
        task_progress[task_id] = "Classification completed successfully"

        logger.info(f"Background classification completed for task {task_id}")

    except Exception as e:
        logger.error(f"Background classification failed for task {task_id}: {e}")

        # Create error result
        error_result = {
            "task_id": task_id,
            "status": ProcessingStatus.FAILED.value,
            "filename": filename,
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }

        try:
            await result_storage.save_result(task_id, error_result)
        except Exception as save_error:
            logger.error(
                f"Failed to save error result for task {task_id}: {save_error}"
            )

        task_status[task_id] = ProcessingStatus.FAILED.value
        task_progress[task_id] = f"Classification failed: {str(e)}"


@router.post("/upload-document/", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
) -> UploadResponse:
    """
    Upload and classify a PDF document.

    Args:
        background_tasks: FastAPI background tasks.
        file: Uploaded PDF file.

    Returns:
        UploadResponse: Upload confirmation with task ID.

    Raises:
        HTTPException: If upload validation fails.
    """
    try:
        logger.info(f"Received upload request: {file.filename}")

        # Validate file
        content, validated_filename = await file_validator.validate_pdf_file(file)

        # Generate task ID
        task_id = str(uuid.uuid4())

        # Initialize task tracking
        task_status[task_id] = ProcessingStatus.QUEUED.value
        task_progress[task_id] = "Document uploaded, queued for processing"

        # Start background classification
        background_tasks.add_task(
            classify_document_task, content, task_id, validated_filename
        )

        logger.info(f"Document queued for classification: {task_id}")

        return UploadResponse(
            task_id=task_id,
            filename=validated_filename,
            status=ProcessingStatus.QUEUED,
            message="Document uploaded successfully and queued for processing",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get processing status for a task.

    Args:
        task_id: Unique task identifier.

    Returns:
        TaskStatusResponse: Current task status.

    Raises:
        HTTPException: If task not found.
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    current_status = task_status[task_id]
    progress = task_progress.get(task_id, "No progress information available")

    return TaskStatusResponse(
        task_id=task_id, status=ProcessingStatus(current_status), progress=progress
    )


@router.get("/result/{task_id}", response_model=DocumentProcessingResult)
async def get_classification_result(task_id: str) -> DocumentProcessingResult:
    """
    Get classification result for a completed task.

    Args:
        task_id: Unique task identifier.

    Returns:
        DocumentProcessingResult: Complete classification result.

    Raises:
        HTTPException: If task not found or not completed.
    """
    # Check if task exists
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    current_status = task_status[task_id]

    # Check if task is completed
    if current_status not in [
        ProcessingStatus.COMPLETED.value,
        ProcessingStatus.FAILED.value,
    ]:
        raise HTTPException(
            status_code=202, detail=f"Task still processing. Status: {current_status}"
        )

    # Get result from storage
    result = await result_storage.get_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return DocumentProcessingResult(**result)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for service monitoring.

    Returns:
        HealthCheckResponse: Service health status.
    """
    try:
        # Check AWS services
        aws_status = await classification_agent.health_check()

        return HealthCheckResponse(
            status="healthy",
            service="document-classification",
            version="1.0.0",
            aws_services=aws_status,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            service="document-classification",
            version="1.0.0",
            aws_services={"error": str(e)},
        )


@router.get("/config")
async def get_system_config() -> Dict[str, Any]:
    """
    Get system configuration and supported features.

    Returns:
        Dict[str, Any]: System configuration.
    """
    stats = classification_agent.get_classification_stats()
    upload_stats = file_storage.get_upload_stats()

    return {
        "classification": stats,
        "upload": {
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "supported_formats": ["pdf"],
            "current_upload_stats": upload_stats,
        },
        "processing": {
            "active_tasks": len(
                [
                    s
                    for s in task_status.values()
                    if s == ProcessingStatus.PROCESSING.value
                ]
            ),
            "queued_tasks": len(
                [s for s in task_status.values() if s == ProcessingStatus.QUEUED.value]
            ),
            "total_tasks": len(task_status),
        },
    }


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str) -> Dict[str, str]:
    """
    Cancel a processing task (if possible).

    Args:
        task_id: Task identifier to cancel.

    Returns:
        Dict[str, str]: Cancellation status.

    Raises:
        HTTPException: If task not found or cannot be cancelled.
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    current_status = task_status[task_id]

    if current_status in [
        ProcessingStatus.COMPLETED.value,
        ProcessingStatus.FAILED.value,
    ]:
        raise HTTPException(
            status_code=400, detail="Cannot cancel completed or failed task"
        )

    if current_status == ProcessingStatus.PROCESSING.value:
        # Note: Cannot actually cancel running background tasks in FastAPI
        # This would require a more sophisticated task queue like Celery
        return {
            "message": "Task is currently processing and cannot be cancelled",
            "task_id": task_id,
            "status": current_status,
        }

    # Cancel queued task
    task_status[task_id] = ProcessingStatus.FAILED.value
    task_progress[task_id] = "Task cancelled by user"

    return {
        "message": "Task cancelled successfully",
        "task_id": task_id,
        "status": "cancelled",
    }


@router.get("/tasks")
async def list_tasks() -> Dict[str, Any]:
    """
    List all tasks with their current status.

    Returns:
        Dict[str, Any]: List of all tasks and their status.
    """
    task_list = []

    for task_id, status in task_status.items():
        task_info = {
            "task_id": task_id,
            "status": status,
            "progress": task_progress.get(task_id, "No progress available"),
        }

        # Try to get additional info from result if available
        if status in [ProcessingStatus.COMPLETED.value, ProcessingStatus.FAILED.value]:
            result = await result_storage.get_result(task_id)
            if result:
                task_info.update(
                    {
                        "filename": result.get("filename", "Unknown"),
                        "completed_at": result.get("completed_at"),
                        "classification": result.get("classification"),
                    }
                )

        task_list.append(task_info)

    return {
        "tasks": task_list,
        "summary": {
            "total": len(task_status),
            "queued": len(
                [s for s in task_status.values() if s == ProcessingStatus.QUEUED.value]
            ),
            "processing": len(
                [
                    s
                    for s in task_status.values()
                    if s == ProcessingStatus.PROCESSING.value
                ]
            ),
            "completed": len(
                [
                    s
                    for s in task_status.values()
                    if s == ProcessingStatus.COMPLETED.value
                ]
            ),
            "failed": len(
                [s for s in task_status.values() if s == ProcessingStatus.FAILED.value]
            ),
        },
    }


@router.post("/batch-upload")
async def batch_upload(
    background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)
) -> Dict[str, Any]:
    """
    Upload multiple documents for batch processing.

    Args:
        background_tasks: FastAPI background tasks.
        files: List of uploaded files.

    Returns:
        Dict[str, Any]: Batch upload response.
    """
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Batch size limit exceeded. Maximum 10 files per batch.",
        )

    batch_id = str(uuid.uuid4())
    task_ids = []
    successful_uploads = 0
    errors = []

    for file in files:
        try:
            # Validate file
            content, validated_filename = await file_validator.validate_pdf_file(file)

            # Generate task ID
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)

            # Initialize task tracking
            task_status[task_id] = ProcessingStatus.QUEUED.value
            task_progress[task_id] = f"Batch {batch_id}: Queued for processing"

            # Start background classification
            background_tasks.add_task(
                classify_document_task, content, task_id, validated_filename
            )

            successful_uploads += 1

        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    return {
        "batch_id": batch_id,
        "task_ids": task_ids,
        "successful_uploads": successful_uploads,
        "total_files": len(files),
        "errors": errors,
        "message": f"Batch upload completed. {successful_uploads}/{len(files)} files processed successfully.",
    }


# Evaluation storage (use database in production)
evaluation_results: Dict[str, Dict[str, Any]] = {}


@router.post("/evaluation/batch-test")
async def batch_evaluation_test(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    labels: str = Form("")
) -> Dict[str, Any]:
    """
    Upload labeled test documents for batch evaluation.
    
    Args:
        background_tasks: FastAPI background tasks.
        files: List of test PDF files.
        labels: JSON string mapping filenames to true labels.
        
    Returns:
        Dict[str, Any]: Batch evaluation response.
    """
    try:
        # Parse labels
        import json
        try:
            ground_truth = json.loads(labels) if labels else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid labels JSON format")
        
        if len(files) > 20:  # Limit evaluation batch size
            raise HTTPException(
                status_code=400,
                detail="Evaluation batch size limit exceeded. Maximum 20 files per batch."
            )
        
        evaluation_id = str(uuid.uuid4())
        task_ids = []
        successful_uploads = 0
        errors = []
        
        logger.info(f"Starting batch evaluation {evaluation_id} with {len(files)} files")
        
        for file in files:
            try:
                # Validate file
                content, validated_filename = await file_validator.validate_pdf_file(file)
                
                # Generate task ID
                task_id = str(uuid.uuid4())
                task_ids.append(task_id)
                
                # Initialize task tracking
                task_status[task_id] = ProcessingStatus.QUEUED.value
                task_progress[task_id] = f"Evaluation {evaluation_id}: Queued for processing"
                
                # Start background classification
                background_tasks.add_task(
                    classify_document_task, content, task_id, validated_filename
                )
                
                successful_uploads += 1
                
            except Exception as e:
                errors.append({"filename": file.filename, "error": str(e)})
        
        # Store evaluation metadata
        evaluation_results[evaluation_id] = {
            "evaluation_id": evaluation_id,
            "task_ids": task_ids,
            "ground_truth": ground_truth,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "errors": errors,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Start background evaluation calculation
        background_tasks.add_task(
            calculate_evaluation_metrics_task, evaluation_id
        )
        
        return {
            "evaluation_id": evaluation_id,
            "task_ids": task_ids,
            "successful_uploads": successful_uploads,
            "total_files": len(files),
            "errors": errors,
            "ground_truth_provided": len(ground_truth),
            "message": f"Batch evaluation started. {successful_uploads}/{len(files)} files queued for processing."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")


async def calculate_evaluation_metrics_task(evaluation_id: str) -> None:
    """
    Background task to calculate evaluation metrics once all documents are classified.
    
    Args:
        evaluation_id: Evaluation batch identifier.
    """
    try:
        logger.info(f"Starting metrics calculation for evaluation {evaluation_id}")
        
        eval_data = evaluation_results.get(evaluation_id)
        if not eval_data:
            logger.error(f"Evaluation data not found for {evaluation_id}")
            return
        
        # Wait for all tasks to complete
        import asyncio
        max_wait_time = 300  # 5 minutes timeout
        wait_interval = 5    # Check every 5 seconds
        total_waited = 0
        
        while total_waited < max_wait_time:
            task_ids = eval_data["task_ids"]
            completed_tasks = 0
            
            for task_id in task_ids:
                if task_id in task_status and task_status[task_id] in [
                    ProcessingStatus.COMPLETED.value,
                    ProcessingStatus.FAILED.value
                ]:
                    completed_tasks += 1
            
            if completed_tasks == len(task_ids):
                break
                
            await asyncio.sleep(wait_interval)
            total_waited += wait_interval
        
        # Collect results
        y_true = []
        y_pred = []
        confidences = []
        classification_details = []
        
        ground_truth = eval_data["ground_truth"]
        
        for task_id in eval_data["task_ids"]:
            try:
                result = await result_storage.get_result(task_id)
                if result and "filename" in result:
                    filename = result["filename"]
                    
                    # Get ground truth label
                    if filename in ground_truth:
                        true_label = ground_truth[filename]
                        pred_label = result.get("classification", {}).get("category", "Unknown")
                        confidence = result.get("classification", {}).get("confidence", 0.0)
                        
                        y_true.append(true_label)
                        y_pred.append(pred_label)
                        confidences.append(confidence)
                        
                        classification_details.append({
                            "filename": filename,
                            "true_label": true_label,
                            "predicted_label": pred_label,
                            "confidence": confidence,
                            "correct": true_label == pred_label,
                            "processing_time": result.get("processing_time", 0.0),
                            "reasoning": result.get("classification", {}).get("reasoning", "")
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to get result for task {task_id}: {e}")
        
        if len(y_true) == 0:
            evaluation_results[evaluation_id]["status"] = "failed"
            evaluation_results[evaluation_id]["error"] = "No valid results found"
            return
        
        # Calculate comprehensive metrics
        metrics = metrics_calculator.calculate_classification_metrics(
            y_true, y_pred, confidences
        )
        
        # Generate confusion matrix data
        confusion_data = metrics_calculator.generate_confusion_matrix_data(y_true, y_pred)
        
        # Generate classification summary
        summary = metrics_calculator.generate_classification_summary(y_true, y_pred)
        
        # Update evaluation results
        evaluation_results[evaluation_id].update({
            "status": "completed",
            "metrics": metrics,
            "confusion_matrix": confusion_data,
            "summary": summary,
            "classification_details": classification_details,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Evaluation metrics calculated for {evaluation_id}: {metrics['overall_accuracy']:.2f} accuracy")
        
    except Exception as e:
        logger.error(f"Failed to calculate evaluation metrics for {evaluation_id}: {e}")
        if evaluation_id in evaluation_results:
            evaluation_results[evaluation_id]["status"] = "failed"
            evaluation_results[evaluation_id]["error"] = str(e)


@router.get("/evaluation/{evaluation_id}")
async def get_evaluation_results(evaluation_id: str) -> Dict[str, Any]:
    """
    Get evaluation results for a completed evaluation batch.
    
    Args:
        evaluation_id: Evaluation batch identifier.
        
    Returns:
        Dict[str, Any]: Complete evaluation results.
    """
    if evaluation_id not in evaluation_results:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    eval_data = evaluation_results[evaluation_id]
    
    if eval_data["status"] == "processing":
        raise HTTPException(
            status_code=202, 
            detail="Evaluation still processing. Please check back later."
        )
    
    return eval_data


@router.get("/evaluation/{evaluation_id}/status")
async def get_evaluation_status(evaluation_id: str) -> Dict[str, Any]:
    """
    Get evaluation processing status.
    
    Args:
        evaluation_id: Evaluation batch identifier.
        
    Returns:
        Dict[str, Any]: Evaluation status information.
    """
    if evaluation_id not in evaluation_results:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    eval_data = evaluation_results[evaluation_id]
    task_ids = eval_data["task_ids"]
    
    # Count task statuses
    completed = 0
    failed = 0
    processing = 0
    queued = 0
    
    for task_id in task_ids:
        if task_id in task_status:
            status = task_status[task_id]
            if status == ProcessingStatus.COMPLETED.value:
                completed += 1
            elif status == ProcessingStatus.FAILED.value:
                failed += 1
            elif status == ProcessingStatus.PROCESSING.value:
                processing += 1
            elif status == ProcessingStatus.QUEUED.value:
                queued += 1
    
    return {
        "evaluation_id": evaluation_id,
        "overall_status": eval_data["status"],
        "task_progress": {
            "total": len(task_ids),
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "queued": queued,
            "progress_percentage": (completed + failed) / len(task_ids) * 100 if task_ids else 0
        },
        "created_at": eval_data.get("created_at"),
        "completed_at": eval_data.get("completed_at")
    }


@router.get("/evaluations")
async def list_evaluations() -> Dict[str, Any]:
    """
    List all evaluation batches.
    
    Returns:
        Dict[str, Any]: List of evaluation batches.
    """
    evaluations = []
    
    for eval_id, eval_data in evaluation_results.items():
        evaluations.append({
            "evaluation_id": eval_id,
            "status": eval_data["status"],
            "total_files": eval_data["total_files"],
            "successful_uploads": eval_data["successful_uploads"],
            "ground_truth_provided": len(eval_data["ground_truth"]),
            "created_at": eval_data.get("created_at"),
            "completed_at": eval_data.get("completed_at"),
            "overall_accuracy": eval_data.get("metrics", {}).get("overall_accuracy")
        })
    
    return {
        "evaluations": evaluations,
        "total_evaluations": len(evaluations)
    }
