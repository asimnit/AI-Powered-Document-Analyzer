"""
Base Document Parser

Abstract base class for all document parsers.
Each parser extracts text from a specific file format.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path


class ParserResult:
    """
    Result from document parsing
    
    Contains extracted text and metadata about the parsing process
    """
    def __init__(
        self,
        text: str,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None,
        metadata: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        self.text = text
        self.page_count = page_count
        self.word_count = word_count or len(text.split())
        self.metadata = metadata or {}
        self.error = error
        
    @property
    def success(self) -> bool:
        """Check if parsing was successful"""
        return self.error is None
        
    @property
    def char_count(self) -> int:
        """Get character count"""
        return len(self.text)


class DocumentParser(ABC):
    """
    Abstract base class for document parsers
    
    Each specific parser (PDF, Word, Excel, etc.) should inherit from this
    and implement the parse() method.
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> ParserResult:
        """
        Parse a document file and extract text
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParserResult with extracted text and metadata
        """
        pass
    
    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        Check if this parser supports a given file extension
        
        Args:
            file_extension: File extension (e.g., ".pdf", ".docx")
            
        Returns:
            True if parser can handle this file type
        """
        pass
    
    def _validate_file(self, file_path: str) -> bool:
        """
        Validate that file exists and is readable
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is valid
        """
        path = Path(file_path)
        return path.exists() and path.is_file()
