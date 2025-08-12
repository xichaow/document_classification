"""
Document classification agent for orchestrating the classification pipeline.

This module provides the main DocumentClassificationAgent that coordinates
between AWS Textract for OCR and AWS Bedrock for classification.
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime

from .tools import TextractClient, BedrockClient
from .offline_classifier import create_offline_classification_result
from ..api.models import DocumentType, ProcessingStatus
from ..utils.config import settings

logger = logging.getLogger(__name__)


class DocumentClassificationAgent:
    """
    Main agent for document classification pipeline.

    Orchestrates the complete workflow from PDF input to classification result,
    including text extraction, classification, and confidence validation.
    """

    def __init__(self):
        """Initialize the classification agent with AWS clients."""
        self.textract_client = TextractClient()
        self.bedrock_client = BedrockClient()
        self.document_types = [doc_type.value for doc_type in DocumentType]
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD

        logger.info("DocumentClassificationAgent initialized")

    async def classify_document(
        self, pdf_bytes: bytes, filename: str = ""
    ) -> Dict[str, Any]:
        """
        Classify a PDF document through the complete pipeline.

        Args:
            pdf_bytes: PDF file content as bytes.
            filename: Original filename for logging.

        Returns:
            Dict[str, Any]: Complete classification result with metadata.
        """
        start_time = time.time()

        try:
            logger.info(
                f"Starting classification for {filename} ({len(pdf_bytes)} bytes)"
            )

            # Step 1: Extract text (with AWS fallback to pypdf)
            logger.info("Step 1: Extracting text with Textract (fallback to pypdf if needed)")
            extracted_text = await self._extract_text_with_fallback(pdf_bytes)

            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.warning(f"Insufficient text extracted from {filename} - using offline classification")
                processing_time = time.time() - start_time
                return create_offline_classification_result(
                    extracted_text or "",
                    filename,
                    processing_time
                )

            logger.info(f"Extracted {len(extracted_text)} characters")

            # Step 2: Classify using Bedrock (with fallback to offline classifier)
            logger.info("Step 2: Classifying document with Bedrock (fallback to offline if needed)")
            classification_result = await self._classify_text_with_fallback(extracted_text)

            # Step 3: Validate and post-process results
            logger.info("Step 3: Validating classification results")
            final_result = self._validate_classification(
                classification_result,
                extracted_text,
                filename,
                time.time() - start_time,
            )

            processing_time = time.time() - start_time
            logger.info(
                f"Classification completed for {filename} in {processing_time:.2f}s: "
                f"{final_result['classification']['category']} "
                f"(confidence: {final_result['classification']['confidence']:.2f})"
            )

            return final_result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Classification failed for {filename}: {str(e)} - using offline fallback")
            
            # Try offline fallback as last resort
            try:
                fallback_result = create_offline_classification_result(
                    "",  # No text available
                    filename,
                    processing_time
                )
                fallback_result['error_message'] = str(e)
                fallback_result['status'] = 'completed_with_fallback'
                return fallback_result
            except Exception:
                return self._create_error_result(str(e), filename, processing_time)

    async def _extract_text_with_fallback(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using Textract with pypdf fallback.

        Args:
            pdf_bytes: PDF file content.

        Returns:
            str: Extracted text content.
        """
        try:
            # Try AWS Textract first
            extracted_text = await self.textract_client.extract_text(pdf_bytes)
            
            if extracted_text and len(extracted_text.strip()) > 10:
                logger.info("Textract extraction successful")
                return extracted_text
            else:
                logger.warning("Textract returned insufficient text, trying pypdf fallback...")
                raise Exception("Insufficient text from Textract")

        except Exception as e:
            logger.info(f"Textract failed ({str(e)}), attempting pypdf fallback...")
            
            # Fallback to direct pypdf extraction
            try:
                fallback_text = self.textract_client._extract_text_fallback(pdf_bytes)
                if fallback_text and len(fallback_text.strip()) > 10:
                    logger.info(f"pypdf fallback successful: {len(fallback_text)} characters")
                    return fallback_text
                else:
                    logger.warning(f"pypdf fallback also returned insufficient text: '{fallback_text[:50] if fallback_text else 'None'}...'")
                    return fallback_text or ""
            except Exception as fallback_error:
                logger.error(f"Both Textract and pypdf fallback failed: {fallback_error}")
                return ""
            
    async def _extract_text(self, pdf_bytes: bytes) -> str:
        """
        Legacy method - kept for backward compatibility.
        
        Args:
            pdf_bytes: PDF file content.

        Returns:
            str: Extracted text content.

        Raises:
            Exception: If text extraction fails.
        """
        return await self._extract_text_with_fallback(pdf_bytes)

    async def _classify_text_with_fallback(self, text: str) -> Dict[str, Any]:
        """
        Classify extracted text using Bedrock with offline fallback.

        Args:
            text: Extracted text content.

        Returns:
            Dict[str, Any]: Classification result.
        """
        try:
            # Try Bedrock first
            classification = await self.bedrock_client.classify_document(text)

            # Ensure valid category
            if classification["category"] not in self.document_types:
                logger.warning(
                    f"Invalid category returned: {classification['category']}"
                )
                classification["category"] = DocumentType.UNKNOWN.value
                classification["confidence"] = 0.0
                classification["reasoning"] = (
                    f"Unknown category: {classification['category']}"
                )

            logger.info("Bedrock classification successful")
            return classification

        except Exception as e:
            logger.info(f"Bedrock failed ({str(e)}), using offline classification fallback...")
            
            # Fallback to offline classifier
            from .offline_classifier import OfflineClassifier
            
            try:
                offline_classifier = OfflineClassifier()
                offline_result = offline_classifier.classify_text(text)
                
                # Ensure valid category from offline classifier
                if offline_result["category"] not in self.document_types and offline_result["category"] != "Unknown":
                    offline_result["category"] = DocumentType.UNKNOWN.value
                    offline_result["confidence"] = 0.0
                
                # Add fallback note to reasoning
                offline_result["reasoning"] = offline_result["reasoning"] + " (AWS Bedrock unavailable, used offline classification)"
                
                logger.info(f"Offline classification successful: {offline_result['category']} (confidence: {offline_result['confidence']:.2f})")
                return offline_result
                
            except Exception as fallback_error:
                logger.error(f"Both Bedrock and offline classification failed: {fallback_error}")
                return {
                    "category": DocumentType.UNKNOWN.value,
                    "confidence": 0.0,
                    "reasoning": f"Both Bedrock and offline classification failed: {str(fallback_error)}"
                }

    async def _classify_text(self, text: str) -> Dict[str, Any]:
        """
        Legacy method - kept for backward compatibility.
        
        Args:
            text: Extracted text content.

        Returns:
            Dict[str, Any]: Classification result.

        Raises:
            Exception: If classification fails.
        """
        return await self._classify_text_with_fallback(text)

    def _validate_classification(
        self,
        classification: Dict[str, Any],
        extracted_text: str,
        filename: str,
        processing_time: float,
    ) -> Dict[str, Any]:
        """
        Validate and post-process classification results.

        Args:
            classification: Raw classification result.
            extracted_text: Original extracted text.
            filename: Document filename.
            processing_time: Processing time in seconds.

        Returns:
            Dict[str, Any]: Validated and enriched result.
        """
        # Apply confidence threshold
        needs_manual_review = classification["confidence"] < self.confidence_threshold

        if needs_manual_review:
            logger.info(
                f"Document {filename} flagged for manual review "
                f"(confidence: {classification['confidence']:.2f})"
            )

        # Create enriched result
        result = {
            "status": ProcessingStatus.COMPLETED.value,
            "filename": filename,
            "classification": {
                "category": classification["category"],
                "confidence": classification["confidence"],
                "reasoning": classification["reasoning"],
                "needs_manual_review": needs_manual_review,
            },
            "extracted_text_length": len(extracted_text),
            "processing_time": processing_time,
            "completed_at": datetime.utcnow().isoformat(),
            "metadata": {
                "textract_success": True,
                "bedrock_success": True,
                "confidence_threshold": self.confidence_threshold,
            },
        }

        return result

    def _create_error_result(
        self, error_message: str, filename: str, processing_time: float
    ) -> Dict[str, Any]:
        """
        Create error result for failed classification.

        Args:
            error_message: Error description.
            filename: Document filename.
            processing_time: Processing time in seconds.

        Returns:
            Dict[str, Any]: Error result.
        """
        return {
            "status": ProcessingStatus.FAILED.value,
            "filename": filename,
            "error_message": error_message,
            "processing_time": processing_time,
            "completed_at": datetime.utcnow().isoformat(),
            "classification": {
                "category": DocumentType.UNKNOWN.value,
                "confidence": 0.0,
                "reasoning": f"Processing failed: {error_message}",
                "needs_manual_review": True,
            },
        }

    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on AWS services.

        Returns:
            Dict[str, str]: Health status of each service.
        """
        health_status = {}

        try:
            # Test Textract connectivity
            test_pdf = (
                b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
            )
            await self.textract_client.extract_text(test_pdf)
            health_status["textract"] = "healthy"
        except Exception as e:
            logger.error(f"Textract health check failed: {e}")
            health_status["textract"] = "unhealthy"

        try:
            # Test Bedrock connectivity with simple text
            await self.bedrock_client.classify_document("test document text")
            health_status["bedrock"] = "healthy"
        except Exception as e:
            logger.error(f"Bedrock health check failed: {e}")
            health_status["bedrock"] = "unhealthy"

        return health_status

    def get_supported_document_types(self) -> list:
        """
        Get list of supported document types.

        Returns:
            list: Supported document type names.
        """
        return [
            doc_type
            for doc_type in self.document_types
            if doc_type != DocumentType.UNKNOWN.value
        ]

    def get_classification_stats(self) -> Dict[str, Any]:
        """
        Get classification statistics and configuration.

        Returns:
            Dict[str, Any]: System statistics and configuration.
        """
        return {
            "supported_document_types": self.get_supported_document_types(),
            "confidence_threshold": self.confidence_threshold,
            "textract_confidence_threshold": settings.TEXTRACT_CONFIDENCE_THRESHOLD,
            "max_file_size": settings.MAX_FILE_SIZE,
            "model_id": settings.BEDROCK_MODEL_ID,
        }
