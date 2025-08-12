"""
AWS integration tools for document classification.

This module provides client classes for AWS Textract and Bedrock services
with proper error handling, retry logic, and response parsing.
"""

import json
import boto3
import asyncio
from typing import Dict, Any
from botocore.exceptions import ClientError
# Removed textractcaller dependency - using direct boto3 response parsing
import logging

from ..utils.config import settings

logger = logging.getLogger(__name__)


class TextractClient:
    """
    AWS Textract client for document text extraction.

    Provides methods for extracting text, forms, and tables from PDF documents
    with confidence scoring and error handling.
    """

    def __init__(self):
        """Initialize Textract client with AWS credentials."""
        self.client = boto3.client(
            "textract",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.confidence_threshold = settings.TEXTRACT_CONFIDENCE_THRESHOLD

    async def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF document.

        Args:
            pdf_bytes: PDF file content as bytes.

        Returns:
            str: Extracted text from the document.

        Raises:
            Exception: If text extraction fails.
        """
        try:
            # Try simple text detection first (more compatible)
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.detect_document_text(
                        Document={"Bytes": pdf_bytes}
                    ),
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "UnsupportedDocumentException":
                    # Fallback to analyze_document without advanced features
                    logger.warning("Falling back to analyze_document due to format issues")
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.client.analyze_document(
                            Document={"Bytes": pdf_bytes}, FeatureTypes=[]
                        ),
                    )
                else:
                    raise

            # Parse response and extract text directly
            text_content = self._extract_text_from_response(response)

            logger.info(f"Successfully extracted text: {len(text_content)} characters")
            return text_content

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Textract error {error_code}: {e}")
            
            # Try fallback text extraction using pypdf for various AWS errors
            aws_fallback_errors = [
                "UnsupportedDocumentException", 
                "InvalidParameterException", 
                "ThrottlingException",
                "InvalidSignatureException",  # Missing AWS credentials
                "UnauthorizedOperation",      # Invalid credentials
                "AccessDeniedException",      # No permission
                "CredentialsNotFound"         # No credentials
            ]
            
            if error_code in aws_fallback_errors:
                logger.info(f"Attempting fallback PDF text extraction due to {error_code}...")
                try:
                    fallback_text = self._extract_text_fallback(pdf_bytes)
                    if fallback_text and len(fallback_text.strip()) > 10:
                        logger.info(f"Fallback extraction successful: {len(fallback_text)} characters")
                        return fallback_text
                    else:
                        logger.warning(f"Fallback extraction returned insufficient text: '{fallback_text[:50]}...'")
                except Exception as fallback_error:
                    logger.error(f"Fallback extraction failed: {fallback_error}")
            
            raise Exception(f"Textract extraction failed: {error_code}")
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            raise Exception(f"Failed to extract text: {str(e)}")

    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from raw Textract response.

        Args:
            response: Raw Textract response.

        Returns:
            str: Combined text content from all blocks.
        """
        text_blocks = []

        # Extract text from LINE blocks with confidence filtering
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                confidence = block.get("Confidence", 0)
                if confidence >= self.confidence_threshold * 100:  # Textract uses 0-100 scale
                    text_blocks.append(block.get("Text", ""))

        # If no LINE blocks found or very little text, try WORD blocks
        if len(text_blocks) == 0 or len("\n".join(text_blocks).strip()) < 10:
            word_blocks = []
            for block in response.get("Blocks", []):
                if block["BlockType"] == "WORD":
                    confidence = block.get("Confidence", 0)
                    if confidence >= self.confidence_threshold * 100:
                        word_blocks.append(block.get("Text", ""))
            
            if word_blocks:
                # Join words with spaces and create lines
                text_blocks = [" ".join(word_blocks)]

        # Try to extract form data (key-value pairs) if available
        key_blocks = {}
        value_blocks = {}
        
        for block in response.get("Blocks", []):
            if block["BlockType"] == "KEY_VALUE_SET":
                if "KEY" in block.get("EntityTypes", []):
                    key_blocks[block["Id"]] = block
                elif "VALUE" in block.get("EntityTypes", []):
                    value_blocks[block["Id"]] = block

        # Match keys with values
        for key_id, key_block in key_blocks.items():
            if "Relationships" in key_block:
                for relationship in key_block["Relationships"]:
                    if relationship["Type"] == "VALUE":
                        for value_id in relationship["Ids"]:
                            if value_id in value_blocks:
                                key_text = self._get_text_from_block(key_block, response)
                                value_text = self._get_text_from_block(value_blocks[value_id], response)
                                if key_text and value_text:
                                    text_blocks.append(f"{key_text}: {value_text}")

        return "\n".join(text_blocks)

    def _get_text_from_block(self, block: Dict[str, Any], response: Dict[str, Any]) -> str:
        """
        Get text from a block by following child relationships.
        
        Args:
            block: Block to extract text from.
            response: Full Textract response.
            
        Returns:
            str: Extracted text.
        """
        text_parts = []
        
        if "Relationships" in block:
            for relationship in block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        # Find child block
                        for child_block in response.get("Blocks", []):
                            if child_block["Id"] == child_id and child_block["BlockType"] == "WORD":
                                text_parts.append(child_block.get("Text", ""))
        
        return " ".join(text_parts)

    def _extract_text_fallback(self, pdf_bytes: bytes) -> str:
        """
        Fallback text extraction using pypdf when Textract fails.
        
        Args:
            pdf_bytes: PDF file content.
            
        Returns:
            str: Extracted text.
        """
        try:
            import io
            import pypdf
            
            logger.info("Starting pypdf fallback text extraction...")
            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text_blocks = []
            
            logger.info(f"PDF has {len(pdf_reader.pages)} pages")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    logger.info(f"Page {page_num + 1}: extracted {len(page_text) if page_text else 0} characters")
                    
                    if page_text and page_text.strip():
                        # Clean up the text
                        cleaned_text = page_text.strip().replace('\n', ' ').replace('\r', ' ')
                        # Remove excessive whitespace
                        import re
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
                        
                        if len(cleaned_text) > 5:  # Only add if substantial text
                            text_blocks.append(cleaned_text)
                            logger.info(f"Added text from page {page_num + 1}: '{cleaned_text[:50]}...'")
                        else:
                            logger.warning(f"Page {page_num + 1} has insufficient text: '{cleaned_text}'")
                    else:
                        logger.warning(f"Page {page_num + 1} returned no text")
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {e}")
                    continue
            
            combined_text = "\n".join(text_blocks)
            logger.info(f"pypdf fallback completed: {len(combined_text)} total characters")
            
            if combined_text.strip():
                return combined_text
            else:
                logger.error("pypdf fallback returned empty text")
                return ""
            
        except Exception as e:
            logger.error(f"pypdf fallback failed completely: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ""


class BedrockClient:
    """
    AWS Bedrock client for document classification.

    Provides methods for classifying documents using large language models
    with structured prompts and response parsing.
    """

    def __init__(self):
        """Initialize Bedrock client with AWS credentials."""
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.model_id = settings.BEDROCK_MODEL_ID

    async def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Classify document based on extracted text.

        Args:
            text: Extracted text from document.

        Returns:
            Dict[str, Any]: Classification result with category, confidence, reasoning.

        Raises:
            Exception: If classification fails.
        """
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(text)

            # Prepare request body for Claude 3.5 Sonnet
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Make async API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType="application/json",
                    accept="application/json",
                ),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            classification_result = self._parse_classification_response(response_body)

            logger.info(
                f"Classification result: {classification_result['category']} "
                f"(confidence: {classification_result['confidence']})"
            )

            return classification_result

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Bedrock error {error_code}: {e}")
            raise Exception(f"Bedrock classification failed: {error_code}")
        except Exception as e:
            logger.error(f"Classification error: {e}")
            raise Exception(f"Failed to classify document: {str(e)}")

    def _build_classification_prompt(self, text: str) -> str:
        """
        Build classification prompt with few-shot examples.

        Args:
            text: Document text to classify.

        Returns:
            str: Formatted classification prompt.
        """
        from .prompts import CLASSIFICATION_PROMPT_TEMPLATE

        # Truncate text if too long (keep within token limits)
        max_text_length = 4000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."

        return CLASSIFICATION_PROMPT_TEMPLATE.format(extracted_text=text)

    def _parse_classification_response(
        self, response_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse classification response from Bedrock.

        Args:
            response_body: Response body from Bedrock API.

        Returns:
            Dict[str, Any]: Parsed classification result.
        """
        try:
            # Extract completion text from Claude 3.5 format
            completion = ""
            if "content" in response_body and response_body["content"]:
                # Claude 3.5 format with content array
                for content_block in response_body["content"]:
                    if content_block.get("type") == "text":
                        completion = content_block.get("text", "")
                        break
            else:
                # Fallback to old format
                completion = response_body.get("completion", "")

            # Try to parse as JSON first
            if "{" in completion and "}" in completion:
                json_start = completion.find("{")
                json_end = completion.rfind("}") + 1
                json_str = completion[json_start:json_end]

                try:
                    result = json.loads(json_str)
                    return {
                        "category": result.get("category", "Unknown"),
                        "confidence": float(result.get("confidence", 0.0)),
                        "reasoning": result.get("reasoning", "No reasoning provided"),
                    }
                except json.JSONDecodeError:
                    pass

            # Fallback: Parse text response
            lines = completion.strip().split("\n")
            category = "Unknown"
            confidence = 0.0
            reasoning = "Unable to parse response"

            for line in lines:
                if "category" in line.lower():
                    category = line.split(":")[-1].strip().strip("\"'")
                elif "confidence" in line.lower():
                    try:
                        confidence = float(line.split(":")[-1].strip())
                    except ValueError:
                        confidence = 0.0
                elif "reasoning" in line.lower():
                    reasoning = line.split(":")[-1].strip().strip("\"'")

            return {
                "category": category,
                "confidence": confidence,
                "reasoning": reasoning,
            }

        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return {
                "category": "Unknown",
                "confidence": 0.0,
                "reasoning": f"Response parsing error: {str(e)}",
            }


class ClassificationResult:
    """
    Document classification result container.

    Encapsulates classification results with validation and utility methods.
    """

    def __init__(self, category: str, confidence: float, reasoning: str = ""):
        """
        Initialize classification result.

        Args:
            category: Document category.
            confidence: Classification confidence score (0.0-1.0).
            reasoning: Classification reasoning/explanation.
        """
        self.category = category
        self.confidence = confidence
        self.reasoning = reasoning
        self.needs_manual_review = confidence < settings.CONFIDENCE_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            Dict[str, Any]: Result as dictionary.
        """
        return {
            "category": self.category,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "needs_manual_review": self.needs_manual_review,
        }
