"""
Plain Text Parser

Extracts text from plain text files (.txt).
"""

import logging
from app.services.parsers.base import DocumentParser, ParserResult

logger = logging.getLogger(__name__)


class TextParser(DocumentParser):
    """
    Plain text file parser
    
    Simply reads text files with automatic encoding detection
    """
    
    def parse(self, file_path: str) -> ParserResult:
        """
        Read plain text file
        
        Args:
            file_path: Path to .txt file
            
        Returns:
            ParserResult with file contents
        """
        if not self._validate_file(file_path):
            return ParserResult(
                text="",
                error=f"File not found or not readable: {file_path}"
            )
        
        try:
            # Try UTF-8 first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                # Fall back to latin-1 if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
            
            return ParserResult(
                text=text,
                page_count=1,
                metadata={"parser": "plain-text"}
            )
            
        except Exception as e:
            error_msg = f"Failed to read text file: {str(e)}"
            logger.error(error_msg)
            return ParserResult(text="", error=error_msg)
    
    def supports(self, file_extension: str) -> bool:
        """Check if file extension is .txt"""
        return file_extension.lower() == ".txt"
