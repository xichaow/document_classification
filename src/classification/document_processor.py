"""
Document processing utilities for PDF handling and preprocessing.

This module provides utility functions for processing PDF documents
including text cleaning, validation, and metadata extraction.
"""

import re
import logging
from typing import Dict, Any, Tuple
import pypdf

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Utility class for document processing operations.

    Provides methods for PDF validation, text preprocessing,
    and metadata extraction.
    """

    def __init__(self):
        """Initialize document processor."""
        self.max_text_length = 10000  # Maximum text length for classification

    def validate_pdf_structure(self, pdf_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate PDF file structure and integrity.

        Args:
            pdf_bytes: PDF file content as bytes.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check PDF header
            if not pdf_bytes.startswith(b"%PDF-"):
                return False, "Invalid PDF header"

            # Try to read with pypdf
            import io

            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

            # Check if we can read pages
            if len(pdf_reader.pages) == 0:
                return False, "PDF contains no pages"

            # Try to extract text from first page
            try:
                first_page = pdf_reader.pages[0]
                first_page.extract_text()
            except Exception as e:
                logger.warning(f"Could not extract text from first page: {e}")

            return True, "Valid PDF"

        except Exception as e:
            logger.error(f"PDF validation error: {e}")
            return False, f"PDF validation failed: {str(e)}"

    def extract_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF document.

        Args:
            pdf_bytes: PDF file content.

        Returns:
            Dict[str, Any]: PDF metadata.
        """
        try:
            import io

            pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

            metadata = {
                "page_count": len(pdf_reader.pages),
                "title": "",
                "author": "",
                "subject": "",
                "creator": "",
                "producer": "",
                "creation_date": None,
                "modification_date": None,
                "encrypted": pdf_reader.is_encrypted,
            }

            # Extract document info if available
            if pdf_reader.metadata:
                info = pdf_reader.metadata
                metadata.update(
                    {
                        "title": info.get("/Title", ""),
                        "author": info.get("/Author", ""),
                        "subject": info.get("/Subject", ""),
                        "creator": info.get("/Creator", ""),
                        "producer": info.get("/Producer", ""),
                        "creation_date": info.get("/CreationDate"),
                        "modification_date": info.get("/ModDate"),
                    }
                )

            return metadata

        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            return {"page_count": 0, "error": str(e)}

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess extracted text for classification.

        Args:
            text: Raw extracted text.

        Returns:
            str: Preprocessed text.
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Remove non-printable characters but keep common symbols
        text = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)

        # Normalize line breaks
        text = re.sub(r"\r\n|\r", "\n", text)

        # Remove excessive line breaks
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Truncate if too long
        if len(text) > self.max_text_length:
            text = text[: self.max_text_length] + "..."
            logger.info(f"Text truncated to {self.max_text_length} characters")

        return text

    def extract_key_patterns(self, text: str) -> Dict[str, list]:
        """
        Extract key patterns that might help with classification.

        Args:
            text: Document text.

        Returns:
            Dict[str, list]: Extracted patterns by type.
        """
        patterns = {
            "dates": [],
            "amounts": [],
            "ids": [],
            "addresses": [],
            "phone_numbers": [],
            "emails": [],
        }

        try:
            # Date patterns
            date_pattern = (
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"
            )
            patterns["dates"] = re.findall(date_pattern, text)

            # Amount patterns
            amount_pattern = r"\$[\d,]+\.?\d*|\b\d+\.\d{2}\b"
            patterns["amounts"] = re.findall(amount_pattern, text)

            # ID patterns (numbers that might be IDs)
            id_pattern = r"\b\d{6,}\b"
            patterns["ids"] = re.findall(id_pattern, text)

            # Email patterns
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            patterns["emails"] = re.findall(email_pattern, text)

            # Phone number patterns
            phone_pattern = (
                r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
            )
            patterns["phone_numbers"] = re.findall(phone_pattern, text)

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")

        return patterns

    def calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Calculate statistics about the text content.

        Args:
            text: Document text.

        Returns:
            Dict[str, Any]: Text statistics.
        """
        if not text:
            return {"error": "No text provided"}

        lines = text.split("\n")
        words = text.split()

        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "average_word_length": (
                sum(len(word) for word in words) / len(words) if words else 0
            ),
            "average_line_length": len(text) / len(lines) if lines else 0,
            "uppercase_ratio": (
                sum(1 for c in text if c.isupper()) / len(text) if text else 0
            ),
            "digit_ratio": (
                sum(1 for c in text if c.isdigit()) / len(text) if text else 0
            ),
        }

    def detect_document_language(self, text: str) -> str:
        """
        Simple language detection based on common patterns.

        Args:
            text: Document text.

        Returns:
            str: Detected language ('en' for English, 'unknown' for others).
        """
        if not text:
            return "unknown"

        # Simple English detection based on common words
        english_indicators = [
            "the",
            "and",
            "or",
            "of",
            "to",
            "a",
            "in",
            "is",
            "it",
            "you",
            "that",
            "he",
            "was",
            "for",
            "on",
            "are",
            "as",
            "with",
            "his",
        ]

        words = text.lower().split()
        english_count = sum(1 for word in words[:100] if word in english_indicators)

        # If more than 20% of first 100 words are common English words
        if len(words) > 0 and english_count / min(len(words), 100) > 0.2:
            return "en"

        return "unknown"
