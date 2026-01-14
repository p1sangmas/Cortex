"""Document processing module with fallback mechanisms for PDF extraction"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
from datetime import datetime
import io

# Import settings
try:
    from config.settings import OCR_DPI, OCR_LANGUAGE, OCR_CONFIG, OCR_ENABLED
except ImportError:
    # Default settings if config not available
    OCR_DPI = 300
    OCR_LANGUAGE = "eng"
    OCR_CONFIG = "--psm 1 --oem 3"
    OCR_ENABLED = True

# Set up logging
logger = logging.getLogger(__name__)

# Import OCR-related libraries
try:
    if OCR_ENABLED:
        import pytesseract
        from pdf2image import convert_from_path
        from PIL import Image
        OCR_AVAILABLE = True
        logger.info("OCR support is enabled and available")
    else:
        OCR_AVAILABLE = False
        logger.info("OCR support is disabled in settings")
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR dependencies not available. Install with: pip install pytesseract pdf2image pillow pytesseract")

class DocumentProcessor:
    """Multi-format PDF processor with hierarchical fallback mechanisms"""
    
    def __init__(self):
        self.processors = {
            'pymupdf': self._pymupdf_extract,
            'pdfplumber': self._pdfplumber_extract,
            'pypdf2': self._pypdf2_extract,
        }
        
        # Add OCR processor if available
        if OCR_AVAILABLE:
            self.processors['ocr'] = self._ocr_extract
        
    def extract_with_fallback(self, pdf_path: str) -> Tuple[str, str, Dict]:
        """
        Hierarchical extraction with fallback mechanisms
        Returns: (extracted_text, method_used, metadata)
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        metadata = self._extract_metadata(pdf_path)

        best_text = ""
        best_method = "none"

        # Try standard extractors first
        standard_extractors = ['pymupdf', 'pdfplumber', 'pypdf2']
        for method_name in standard_extractors:
            if method_name not in self.processors:
                continue

            method = self.processors[method_name]
            try:
                logger.info(f"Attempting extraction with {method_name}")
                text = method(str(pdf_path))

                # Add debug logging
                logger.debug(f"{method_name} extracted {len(text)} characters, {len(text.split())} words")

                if self._validate_extraction(text):
                    logger.info(f"Successfully extracted text using {method_name}")
                    return text, method_name, metadata
                else:
                    logger.warning(f"{method_name} extraction failed validation")
                    logger.debug(f"Text preview: {text[:200]}...")

                    # Keep track of the best extraction so far
                    if len(text.strip()) > len(best_text.strip()):
                        best_text = text
                        best_method = method_name

            except Exception as e:
                logger.warning(f"{method_name} extraction failed: {str(e)}")
                continue

        # Try OCR as a last resort if standard methods failed or produced poor results
        if (not best_text.strip() or len(best_text.split()) < 50 or self._needs_ocr(best_text)):
            if 'ocr' in self.processors:
                try:
                    logger.info("Attempting OCR extraction as fallback")
                    text = self.processors['ocr'](str(pdf_path))
                    logger.debug(f"OCR extracted {len(text)} characters, {len(text.split())} words")

                    # OCR results don't need to pass strict validation
                    if text.strip() and len(text.split()) > 10:
                        logger.info("Successfully extracted text using OCR")
                        return text, 'ocr', metadata

                except Exception as e:
                    logger.warning(f"OCR extraction failed: {str(e)}")
            else:
                logger.warning("OCR would be helpful but dependencies are not installed")

        # If we still have some text from earlier methods, use it
        if best_text.strip():
            logger.warning(f"No extraction method passed validation, using best result from {best_method}")
            logger.info(f"Extracted {len(best_text)} characters, {len(best_text.split())} words")
            return best_text, best_method, metadata

        raise Exception("All extraction methods failed")

    def extract_with_pages(self, pdf_path: str) -> Tuple[List[Tuple[str, int]], str, Dict]:
        """
        Extract text with page number tracking
        Returns: (list of (page_text, page_number) tuples, method_used, metadata)
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        metadata = self._extract_metadata(pdf_path)

        # Try methods that support page tracking
        page_aware_methods = ['pymupdf', 'pdfplumber', 'pypdf2']

        for method_name in page_aware_methods:
            if method_name not in self.processors:
                continue

            try:
                logger.info(f"Attempting page-aware extraction with {method_name}")

                if method_name == 'pymupdf':
                    pages_data = self._pymupdf_extract_with_pages(str(pdf_path))
                elif method_name == 'pdfplumber':
                    pages_data = self._pdfplumber_extract_with_pages(str(pdf_path))
                elif method_name == 'pypdf2':
                    pages_data = self._pypdf2_extract_with_pages(str(pdf_path))
                else:
                    continue

                # Validate extraction
                combined_text = " ".join([text for text, _ in pages_data])
                if self._validate_extraction(combined_text):
                    logger.info(f"Successfully extracted {len(pages_data)} pages using {method_name}")
                    return pages_data, method_name, metadata
                else:
                    logger.warning(f"{method_name} page extraction failed validation")

            except Exception as e:
                logger.warning(f"{method_name} page extraction failed: {str(e)}")
                continue

        # Fallback: Use regular extraction and assign all text to page 0
        logger.warning("Page-aware extraction failed, using fallback with page 0")
        text, method, metadata = self.extract_with_fallback(str(pdf_path))
        return [(text, 0)], method, metadata
    
    def _pymupdf_extract(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (best for complex layouts)"""
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text += page.get_text()
            text += "\n\n"  # Add page break

        doc.close()
        return text.strip()

    def _pymupdf_extract_with_pages(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text with page numbers using PyMuPDF"""
        doc = fitz.open(pdf_path)
        pages_data = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()

            if page_text.strip():  # Only add if page has text
                pages_data.append((page_text.strip(), page_num + 1))  # 1-indexed pages

        doc.close()
        return pages_data
    
    def _pdfplumber_extract(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (good for tables)"""
        text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        return text.strip()

    def _pdfplumber_extract_with_pages(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text with page numbers using pdfplumber"""
        pages_data = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()

                if page_text and page_text.strip():
                    pages_data.append((page_text.strip(), page_num + 1))  # 1-indexed

        return pages_data
    
    def _pypdf2_extract(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (fallback option)"""
        text = ""

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        return text.strip()

    def _pypdf2_extract_with_pages(self, pdf_path: str) -> List[Tuple[str, int]]:
        """Extract text with page numbers using PyPDF2"""
        pages_data = []

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()

                if page_text and page_text.strip():
                    pages_data.append((page_text.strip(), page_num + 1))  # 1-indexed

        return pages_data
    
    def _ocr_extract(self, pdf_path: str) -> str:
        """Extract text using OCR for PDFs that can't be parsed correctly"""
        if not OCR_AVAILABLE:
            raise ImportError("OCR dependencies not available")
            
        logger.info(f"Attempting OCR extraction on {pdf_path}")
        text = ""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Convert PDF to images using settings from config
                pages = convert_from_path(
                    pdf_path, 
                    dpi=OCR_DPI,  # From config
                    output_folder=temp_dir
                )
                
                logger.info(f"Converted {len(pages)} pages to images for OCR")
                
                # Process each page with OCR
                for i, page in enumerate(pages):
                    logger.debug(f"OCR processing page {i+1}/{len(pages)}")
                    # Improve image quality for OCR
                    page = page.convert('L')  # Convert to grayscale
                    
                    # Run OCR with settings from config
                    page_text = pytesseract.image_to_string(
                        page, 
                        lang=OCR_LANGUAGE,
                        config=OCR_CONFIG
                    )
                    
                    if page_text:
                        text += page_text + "\n\n"
                
            except Exception as e:
                logger.error(f"OCR extraction error: {e}")
                raise
                
        return text.strip()
    
    def _validate_extraction(self, text: str) -> bool:
        """Validate if extraction was successful"""
        if not text or len(text.strip()) < 10:
            return False
            
        # Check for reasonable word count
        words = text.split()
        if len(words) < 5:
            return False
            
        # Check for reasonable character distribution
        if text.count('?') > len(text) * 0.3:
            return False
            
        # Check for common failure patterns in web-saved PDFs
        unusual_char_ratio = sum(c in '□▯�' for c in text) / max(1, len(text))
        if unusual_char_ratio > 0.05:  # More than 5% unusual replacement characters
            logger.warning(f"Text contains {unusual_char_ratio:.1%} unusual characters, likely encoding issues")
            return False
        
        # Check for reasonable text density (chars per word)
        avg_word_length = sum(len(word) for word in words) / max(1, len(words))
        if avg_word_length < 2.0 or avg_word_length > 15.0:
            logger.warning(f"Unusual average word length: {avg_word_length:.1f} chars/word")
            return False
            
        return True
        
    def _needs_ocr(self, text: str) -> bool:
        """Determine if a text extraction likely needs OCR to improve results"""
        if not text or len(text.strip()) == 0:
            return True
            
        # Look for common issues with web-saved PDFs
        words = text.split()
        
        # Check for high percentage of special characters or unusual symbols
        special_chars = set('�□▯¿⍰¤◌○●◦§¶†‡©®™«»""''‹›€£¥¢¡')
        special_char_count = sum(c in special_chars for c in text)
        special_ratio = special_char_count / max(1, len(text))
        
        # Check for common web PDF extraction issues
        char_per_line = len(text) / max(1, text.count('\n') + 1)
        
        # Common website-to-PDF conversion artifacts
        has_artifacts = ('CSS' in text and 'HTML' in text) or ('javascript' in text.lower())
        
        # Determine if OCR might help
        if special_ratio > 0.01 or has_artifacts or char_per_line < 20:
            logger.info(f"Text likely needs OCR: special_ratio={special_ratio:.3f}, " 
                       f"artifacts={has_artifacts}, char_per_line={char_per_line:.1f}")
            return True
            
        return False
    
    def _extract_metadata(self, pdf_path: Path) -> Dict:
        """Extract metadata from PDF file"""
        metadata = {
            'filename': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'creation_date': datetime.fromtimestamp(pdf_path.stat().st_ctime).isoformat(),
            'modification_date': datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
        }
        
        # Try to extract PDF metadata
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.metadata:
                    pdf_metadata = pdf_reader.metadata
                    metadata.update({
                        'title': pdf_metadata.get('/Title', ''),
                        'author': pdf_metadata.get('/Author', ''),
                        'subject': pdf_metadata.get('/Subject', ''),
                        'creator': pdf_metadata.get('/Creator', ''),
                        'producer': pdf_metadata.get('/Producer', ''),
                    })
                    
                metadata['page_count'] = len(pdf_reader.pages)
                
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
            
        return metadata

class MetadataEnhancer:
    """Enhance chunks with contextual metadata"""
    
    def __init__(self):
        pass
        
    def enhance_chunks(self, chunks: List[str], document_metadata: Dict) -> List[Dict]:
        """Add contextual metadata to each chunk"""
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                'source_document': document_metadata['filename'],
                'chunk_index': i,
                'chunk_length': len(chunk),
                'word_count': len(chunk.split()),
                'creation_date': document_metadata.get('creation_date'),
                'author': document_metadata.get('author', 'Unknown'),
                'page_count': document_metadata.get('page_count', 0),
                'document_type': self._classify_document_type(chunk),
                'section_header': self._extract_section_header(chunk),
                # Store original filename for better source citation
                'original_filename': document_metadata.get('original_filename', document_metadata.get('filename')),
            }
            
            enhanced_chunks.append({
                'content': chunk,
                'metadata': metadata
            })
            
        return enhanced_chunks
    
    def _classify_document_type(self, chunk: str) -> str:
        """Simple document type classification based on content"""
        chunk_lower = chunk.lower()
        
        if any(keyword in chunk_lower for keyword in ['policy', 'procedure', 'guideline', 'rule']):
            return 'policy'
        elif any(keyword in chunk_lower for keyword in ['manual', 'instruction', 'how to', 'step']):
            return 'manual'
        elif any(keyword in chunk_lower for keyword in ['report', 'analysis', 'summary', 'finding']):
            return 'report'
        elif any(keyword in chunk_lower for keyword in ['contract', 'agreement', 'terms']):
            return 'legal'
        else:
            return 'general'
    
    def _extract_section_header(self, chunk: str) -> str:
        """Extract potential section header from chunk"""
        lines = chunk.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and (line.isupper() or line.endswith(':') or len(line.split()) <= 6):
                return line
        return ""
