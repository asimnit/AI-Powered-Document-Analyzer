"""
PDF Parser

Extracts text from PDF documents using PyPDF2 and pdfplumber.
Falls back between libraries if one fails.
"""

import logging
from typing import Optional
from pathlib import Path

from app.services.parsers.base import DocumentParser, ParserResult

logger = logging.getLogger(__name__)


class PDFParser(DocumentParser):
    """
    PDF document parser
    
    Uses pdfplumber as primary method (better text extraction)
    Falls back to PyPDF2 if pdfplumber fails
    """
    
    def parse(self, file_path: str) -> ParserResult:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ParserResult with extracted text
        """
        if not self._validate_file(file_path):
            return ParserResult(
                text="",
                error=f"File not found or not readable: {file_path}"
            )
        
        try:
            # Try pdfplumber first (better quality)
            return self._parse_with_pdfplumber(file_path)
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
            try:
                # Fall back to PyPDF2
                return self._parse_with_pypdf2(file_path)
            except Exception as e2:
                error_msg = f"All PDF parsing methods failed: {str(e2)}"
                logger.error(error_msg)
                return ParserResult(text="", error=error_msg)
    
    def _parse_with_pdfplumber(self, file_path: str) -> ParserResult:
        """Parse PDF using pdfplumber (better quality)"""
        import pdfplumber
        
        text_parts = []
        page_count = 0
        
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = "\n\n".join(text_parts)
        
        return ParserResult(
            text=full_text,
            page_count=page_count,
            metadata={"parser": "pdfplumber"}
        )
    
    def _parse_with_pypdf2(self, file_path: str) -> ParserResult:
        """Parse PDF using PyPDF2 (fallback)"""
        from PyPDF2 import PdfReader
        
        text_parts = []
        
        reader = PdfReader(file_path)
        page_count = len(reader.pages)
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n\n".join(text_parts)
        
        return ParserResult(
            text=full_text,
            page_count=page_count,
            metadata={"parser": "PyPDF2"}
        )
    
    def supports(self, file_extension: str) -> bool:
        """Check if file extension is PDF"""
        return file_extension.lower() == ".pdf"
