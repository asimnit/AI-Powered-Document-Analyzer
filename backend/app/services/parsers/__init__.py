"""
Parser Factory

Manages all document parsers and routes files to the appropriate parser.
"""

import logging
from pathlib import Path
from typing import Optional

from app.services.parsers.base import DocumentParser, ParserResult
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.word_parser import WordParser
from app.services.parsers.excel_parser import ExcelParser
from app.services.parsers.image_parser import ImageParser
from app.services.parsers.text_parser import TextParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory for document parsers
    
    Automatically selects the right parser based on file extension
    """
    
    def __init__(self):
        """Initialize all available parsers"""
        self.parsers: list[DocumentParser] = [
            PDFParser(),
            WordParser(),
            ExcelParser(),
            ImageParser(),
            TextParser(),
        ]
    
    def get_parser(self, file_path: str) -> Optional[DocumentParser]:
        """
        Get appropriate parser for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Parser instance or None if no parser supports this file type
        """
        extension = Path(file_path).suffix
        
        for parser in self.parsers:
            if parser.supports(extension):
                return parser
        
        logger.warning(f"No parser found for file extension: {extension}")
        return None
    
    def parse(self, file_path: str) -> ParserResult:
        """
        Parse a document file
        
        Args:
            file_path: Path to file
            
        Returns:
            ParserResult with extracted text and metadata
        """
        parser = self.get_parser(file_path)
        
        if parser is None:
            extension = Path(file_path).suffix
            return ParserResult(
                text="",
                error=f"Unsupported file type: {extension}"
            )
        
        logger.info(f"Parsing {file_path} with {parser.__class__.__name__}")
        return parser.parse(file_path)
    
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of all supported file extensions"""
        extensions = []
        for parser in self.parsers:
            # Get extensions from parser's supports method
            # This is a simplified version - in production you might want
            # parsers to explicitly declare their supported extensions
            pass
        return [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
