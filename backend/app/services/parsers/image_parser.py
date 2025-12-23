"""
Image OCR Parser

Extracts text from images using pytesseract (Tesseract OCR).
Note: Requires Tesseract OCR to be installed on the system.
"""

import logging
from app.services.parsers.base import DocumentParser, ParserResult

logger = logging.getLogger(__name__)


class ImageParser(DocumentParser):
    """
    Image OCR parser
    
    Extracts text from images using Tesseract OCR:
    - Supports: PNG, JPG, JPEG, TIFF, BMP
    - Requires Tesseract OCR installed on system
    """
    
    def parse(self, file_path: str) -> ParserResult:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            ParserResult with extracted text
        """
        if not self._validate_file(file_path):
            return ParserResult(
                text="",
                error=f"File not found or not readable: {file_path}"
            )
        
        try:
            import pytesseract
            from PIL import Image
            
            # Open image
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from image: {file_path}")
                return ParserResult(
                    text="",
                    error="No text found in image"
                )
            
            return ParserResult(
                text=text.strip(),
                page_count=1,
                metadata={
                    "parser": "pytesseract",
                    "image_size": image.size,
                    "image_format": image.format
                }
            )
            
        except ImportError:
            error_msg = "Tesseract OCR is not installed. Please install it to process images."
            logger.error(error_msg)
            return ParserResult(text="", error=error_msg)
        except Exception as e:
            error_msg = f"Failed to perform OCR on image: {str(e)}"
            logger.error(error_msg)
            return ParserResult(text="", error=error_msg)
    
    def supports(self, file_extension: str) -> bool:
        """Check if file extension is a supported image format"""
        return file_extension.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
