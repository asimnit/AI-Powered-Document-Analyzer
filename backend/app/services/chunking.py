"""
Text Chunking Service

Splits large text into smaller, manageable chunks for processing and storage.
Uses character-based chunking with configurable overlap.
"""

import logging
import re
from typing import List
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


class TextChunk:
    """Represents a single chunk of text"""
    
    def __init__(
        self,
        content: str,
        index: int,
        char_count: int,
        word_count: int,
        page_numbers: List[int] = None
    ):
        self.content = content
        self.index = index
        self.char_count = char_count
        self.word_count = word_count
        self.page_numbers = page_numbers or []


class TextChunker:
    """
    Text chunking service
    
    Splits text into chunks using character-based approach with overlap.
    Strategy: ~2000 characters per chunk with 200 character overlap
    """
    
    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 10
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target characters per chunk
            chunk_overlap: Characters to overlap between chunks
            min_chunk_size: Minimum chunk size (discard smaller chunks)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into chunks
        
        Args:
            text: Full text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or len(text) < self.min_chunk_size:
            logger.warning("Text too short to chunk")
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                window_start = max(start, end - 100)
                window_end = min(len(text), end + 100)
                window = text[window_start:window_end]
                
                # Find last sentence boundary (., !, ?)
                sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s', window)]
                if sentence_endings:
                    # Use the last sentence ending within window
                    last_ending = sentence_endings[-1]
                    end = window_start + last_ending
            
            # Extract chunk content
            chunk_content = text[start:end].strip()
            
            # Only create chunk if it meets minimum size
            if len(chunk_content) >= self.min_chunk_size:
                word_count = len(chunk_content.split())
                
                chunk = TextChunk(
                    content=chunk_content,
                    index=chunk_index,
                    char_count=len(chunk_content),
                    word_count=word_count
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position (with overlap)
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            ISO language code (e.g., "en", "es", "fr") or "unknown"
        """
        try:
            # Use first 1000 chars for detection (faster)
            sample = text[:1000]
            return detect(sample)
        except LangDetectException:
            logger.warning("Could not detect language")
            return "unknown"
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return "unknown"
