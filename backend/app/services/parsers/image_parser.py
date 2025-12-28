"""
Image OCR Parser

Extracts text from images using pytesseract (Tesseract OCR).
Note: Requires Tesseract OCR to be installed on the system.
"""

import logging
from app.services.parsers.base import DocumentParser, ParserResult
from app.core.config import settings

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
            from PIL import Image, ImageEnhance, ImageFilter
            
            # Set Tesseract path if configured
            if settings.TESSERACT_CMD:
                logger.info(f"Setting Tesseract path from config: {settings.TESSERACT_CMD}")
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            else:
                logger.warning("TESSERACT_CMD not set in config, using system PATH")
            
            # Open image
            image = Image.open(file_path)
            logger.info(f"Original image size: {image.size}, mode: {image.mode}")
            
            # Try multiple OCR strategies
            text = None
            strategies = []
            
            # Strategy 1: Original image
            try:
                text = pytesseract.image_to_string(image, config='--psm 3')
                strategies.append(f"original (length: {len(text.strip())})")
                if text and len(text.strip()) > 10:
                    logger.info(f"Strategy 1 (original) succeeded: {len(text.strip())} chars")
            except Exception as e:
                logger.warning(f"Strategy 1 failed: {e}")
                text = ""
            
            # Strategy 2: Enhanced contrast and sharpness (if first attempt was poor)
            if not text or len(text.strip()) < 10:
                try:
                    # Convert to grayscale
                    enhanced = image.convert('L')
                    # Enhance contrast
                    enhancer = ImageEnhance.Contrast(enhanced)
                    enhanced = enhancer.enhance(2.0)
                    # Sharpen
                    enhanced = enhanced.filter(ImageFilter.SHARPEN)
                    
                    text2 = pytesseract.image_to_string(enhanced, config='--psm 3')
                    strategies.append(f"enhanced (length: {len(text2.strip())})")
                    if len(text2.strip()) > len(text.strip()):
                        text = text2
                        logger.info(f"Strategy 2 (enhanced) succeeded: {len(text.strip())} chars")
                except Exception as e:
                    logger.warning(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Try different page segmentation mode (if still poor)
            if not text or len(text.strip()) < 10:
                try:
                    # PSM 6: Assume a single uniform block of text
                    text3 = pytesseract.image_to_string(image, config='--psm 6')
                    strategies.append(f"psm6 (length: {len(text3.strip())})")
                    if len(text3.strip()) > len(text.strip()):
                        text = text3
                        logger.info(f"Strategy 3 (psm 6) succeeded: {len(text.strip())} chars")
                except Exception as e:
                    logger.warning(f"Strategy 3 failed: {e}")
            
            # Strategy 4: Try with auto orientation and script detection
            if not text or len(text.strip()) < 10:
                try:
                    # PSM 1: Automatic page segmentation with OSD
                    text4 = pytesseract.image_to_string(image, config='--psm 1')
                    strategies.append(f"psm1 (length: {len(text4.strip())})")
                    if len(text4.strip()) > len(text.strip()):
                        text = text4
                        logger.info(f"Strategy 4 (psm 1) succeeded: {len(text.strip())} chars")
                except Exception as e:
                    logger.warning(f"Strategy 4 failed: {e}")
            
            logger.info(f"Tried strategies: {', '.join(strategies)}")
            
            if not text or not text.strip():
                logger.warning(f"No text extracted from image after trying all strategies: {file_path}")
                return ParserResult(
                    text="",
                    error="No text found in image. The image may be too low quality, or the text may be too small or unclear."
                )
            
            final_text = text.strip()
            logger.info(f"Final extracted text length: {len(final_text)} characters")
            
            return ParserResult(
                text=final_text,
                page_count=1,
                metadata={
                    "parser": "pytesseract",
                    "image_size": image.size,
                    "image_format": image.format,
                    "strategies_tried": strategies
                }
            )
            
        except ImportError as e:
            error_msg = f"Import error: {str(e)}. Tesseract OCR or PIL may not be installed properly."
            logger.error(error_msg)
            return ParserResult(text="", error=error_msg)
        except Exception as e:
            error_msg = f"Failed to perform OCR on image: {str(e)}"
            logger.error(error_msg)
            return ParserResult(text="", error=error_msg)
    
    def supports(self, file_extension: str) -> bool:
        """Check if file extension is a supported image format"""
        return file_extension.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
