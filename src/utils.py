"""Utility functions for the Cortex Knowledge Base Assistant"""

import logging
import os
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import wraps
import streamlit as st

logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/documind.log') if Path('data').exists() else logging.NullHandler()
        ]
    )

def timing_decorator(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
        
        # Store timing in result if it's a dictionary
        if isinstance(result, dict):
            result['execution_time'] = execution_time
            
        return result
    return wrapper

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extract key phrases from text using simple heuristics"""
    import re
    
    # Simple extraction based on capitalized words and common patterns
    phrases = []
    
    # Find capitalized phrases (potential proper nouns)
    capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    capitalized_matches = re.findall(capitalized_pattern, text)
    phrases.extend(capitalized_matches[:max_phrases//2])
    
    # Find quoted text
    quoted_pattern = r'"([^"]*)"'
    quoted_matches = re.findall(quoted_pattern, text)
    phrases.extend(quoted_matches[:max_phrases//2])
    
    # Remove duplicates and return
    unique_phrases = list(dict.fromkeys(phrases))  # Preserve order
    return unique_phrases[:max_phrases]

def calculate_readability_score(text: str) -> Dict[str, float]:
    """Calculate simple readability metrics"""
    if not text:
        return {'words': 0, 'sentences': 0, 'avg_word_length': 0, 'avg_sentence_length': 0}
    
    # Count words and sentences
    words = len(text.split())
    sentences = len([s for s in text.split('.') if s.strip()])
    
    if sentences == 0:
        sentences = 1  # Avoid division by zero
    
    # Calculate averages
    avg_word_length = sum(len(word) for word in text.split()) / words if words > 0 else 0
    avg_sentence_length = words / sentences
    
    return {
        'words': words,
        'sentences': sentences,
        'avg_word_length': avg_word_length,
        'avg_sentence_length': avg_sentence_length
    }

class StreamlitUtils:
    """Utility functions for Streamlit UI"""
    
    @staticmethod
    def display_metrics(metrics: Dict[str, float], title: str = "Performance Metrics"):
        """Display metrics in a nice format"""
        with st.container():
            st.markdown(f"### 📊 {title}")
            
            # Create columns for metrics
            num_cols = min(4, len(metrics))  # Limit to 4 columns per row for readability
            num_rows = (len(metrics) + num_cols - 1) // num_cols
            
            # For each row of metrics
            for row in range(num_rows):
                # Calculate slice for this row
                start_idx = row * num_cols
                end_idx = min(start_idx + num_cols, len(metrics))
                row_metrics = list(metrics.items())[start_idx:end_idx]
                
                # Create columns for this row
                cols = st.columns(len(row_metrics))
                
                # Fill in the columns
                for i, (metric_name, value) in enumerate(row_metrics):
                    with cols[i]:
                        # Format metric name
                        display_name = metric_name.replace('_', ' ').title()
                        
                        # Format value based on type
                        if isinstance(value, float):
                            if 0 <= value <= 1:
                                formatted_value = f"{value:.2%}"
                            else:
                                formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = str(value)
                        
                        st.metric(display_name, formatted_value)
    
    @staticmethod
    def display_sources(sources: List[Dict[str, str]], title: str = "Sources"):
        """Display source information"""
        if not sources:
            return
            
        with st.container():
            st.markdown(f"### 📚 {title}")
            
            for i, source in enumerate(sources, 1):
                # Get the source document ID, with enhanced extraction
                doc_id = source.get('document', 'Unknown')
                
                # Normalize document IDs - strip any problematic prefixes
                if doc_id.startswith('doc_'):
                    # For generic doc IDs, try to use a better identifier
                    if 'original_filename' in source:
                        doc_id = source.get('original_filename')
                    elif 'title' in source:
                        doc_id = source.get('title')
                
                # Priority 1: Try to use title if available
                if 'title' in source and source['title']:
                    display_name = source.get('title')
                # Priority 2: Try to use display_name if available
                elif 'display_name' in source and source['display_name']:
                    display_name = source.get('display_name')
                # Priority 3: Try to use original_filename if available
                elif 'original_filename' in source:
                    display_name = source.get('original_filename')
                    # Remove .pdf extension if present
                    if display_name.lower().endswith('.pdf'):
                        display_name = display_name[:-4]
                # Priority 4: Try to extract from doc_id
                elif '_' in doc_id and not doc_id.startswith('doc_') and not doc_id.startswith('tmp'):
                    # Try to parse the friendly name from ID format
                    try:
                        # Get anything before the last underscore as the filename part
                        filename_part = doc_id.rsplit('_', 1)[0]
                        display_name = filename_part.replace('_', ' ')
                        
                        # Check if it's from original document naming format
                        if display_name.startswith('doc ') or len(display_name.strip()) < 3:
                            display_name = doc_id
                    except:
                        display_name = doc_id
                else:
                    display_name = doc_id
                
                # Extract page number if available
                page_info = ""
                if 'page' in source:
                    page_info = f" (Page {source['page']})"
                    
                # Improve display name for doc_ID type sources
                if display_name.startswith('doc_') or display_name == 'Unknown':
                    display_name = f"Document {i}"
                
                # Create a styled expander for each source
                with st.expander(f"📄 {display_name}{page_info}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Only show Source ID if it's not a generic doc_ID format
                        if not doc_id.startswith('doc_'):
                            st.write(f"**Source ID:** {doc_id}")
                            
                        # Show author
                        author = source.get('author', 'Unknown')
                        st.write(f"**Author:** {author}")
                    
                    with col2:
                        # Original filename if available
                        if 'original_filename' in source:
                            st.write(f"**File:** {source.get('original_filename')}")
                        elif doc_id.startswith('doc_'):
                            # If we only have a doc_ID, it's likely from collection
                            st.write(f"**Source Type:** Generated from collection")
                        
                        # Format date nicely if possible
                        creation_date = source.get('creation_date', 'Unknown')
                        if creation_date != 'Unknown':
                            try:
                                from datetime import datetime
                                date_obj = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                                formatted_date = date_obj.strftime('%Y-%m-%d')
                                st.write(f"**Date:** {formatted_date}")
                            except:
                                st.write(f"**Date:** {creation_date}")
                        else:
                            # Check if we're in a known default
                            if doc_id.startswith('doc_'): 
                                # For unknown dates in doc_ format, don't show anything
                                pass
                            else:
                                st.write(f"**Date:** {creation_date}")
    
    @staticmethod
    def display_confidence_indicator(confidence: str):
        """Display confidence level with appropriate styling"""
        confidence_colors = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }
        
        confidence_descriptions = {
            'high': 'High confidence - Answer well supported by documents',
            'medium': 'Medium confidence - Some supporting evidence found',
            'low': 'Low confidence - Limited supporting evidence'
        }
        
        icon = confidence_colors.get(confidence, '⚪')
        description = confidence_descriptions.get(confidence, 'Unknown confidence level')
        
        with st.container():
            st.markdown(f"### {icon} Confidence")
            st.markdown(f"**{confidence.title()}** - {description}")
    
    @staticmethod
    def display_error_message(error_type: str, message: str = None):
        """Display standardized error messages"""
        error_messages = {
            'ollama_unavailable': '🤖 AI service is currently unavailable. Please ensure Ollama is running.',
            'no_documents': '📄 No documents found. Please upload some documents first.',
            'processing_error': '⚠️ An error occurred while processing your request.',
            'generation_failed': '🔧 Failed to generate response. Please try again.',
            'upload_error': '📤 Failed to upload document. Please check the file format.'
        }
        
        display_message = message or error_messages.get(error_type, 'An unknown error occurred.')
        st.error(display_message)
    
    @staticmethod
    def display_processing_status(status: str, progress: Optional[float] = None):
        """Display processing status with optional progress bar"""
        status_messages = {
            'uploading': '📤 Uploading document...',
            'extracting': '📝 Extracting text from document...',
            'chunking': '✂️ Breaking document into chunks...',
            'embedding': '🧠 Generating embeddings...',
            'indexing': '🗂️ Adding to knowledge base...',
            'querying': '🔍 Searching documents...',
            'generating': '💭 Generating response...',
            'complete': '✅ Process completed successfully!'
        }
        
        message = status_messages.get(status, f'Processing: {status}')
        
        if progress is not None:
            st.progress(progress, text=message)
        else:
            st.info(message)

class ValidationUtils:
    """Utility functions for data validation"""
    
    @staticmethod
    def validate_pdf_file(uploaded_file) -> tuple[bool, str]:
        """Validate uploaded PDF file"""
        import logging
        logger = logging.getLogger(__name__)
        
        if uploaded_file is None:
            logger.warning("Validation failed: No file uploaded")
            return False, "No file uploaded"
        
        # Log file details for debugging
        try:
            file_details = f"File: {uploaded_file.name}, "
            if hasattr(uploaded_file, 'content_type'):
                file_details += f"Content-Type: {uploaded_file.content_type}, "
            if hasattr(uploaded_file, 'size'):
                file_details += f"Size: {uploaded_file.size} bytes, "
            else:
                file_details += "Size: unknown, "
            logger.info(f"Validating file: {file_details}")
        except Exception as e:
            logger.warning(f"Error getting file details: {e}")
        
        # Check file extension
        if not uploaded_file.filename.lower().endswith('.pdf'):
            logger.warning(f"Validation failed: Invalid extension - {uploaded_file.filename}")
            return False, "File must be a PDF"
        
        # Check file size (limit to 50MB)
        try:
            # Different file objects might have size as an attribute or a method
            file_size = 0
            if hasattr(uploaded_file, 'size'):
                file_size = uploaded_file.size
            
            if file_size > 50 * 1024 * 1024:
                logger.warning(f"Validation failed: File too large - {file_size} bytes")
                return False, "File size must be less than 50MB"
            
            # Check if file is not empty
            if file_size == 0:
                # Try to read the first few bytes to double-check
                try:
                    current_position = uploaded_file.tell()
                    sample = uploaded_file.read(1024)
                    uploaded_file.seek(current_position)  # Reset position
                    
                    if not sample or len(sample) == 0:
                        logger.error(f"Validation failed: File is empty - {uploaded_file.filename}")
                        return False, "File is empty (no content)"
                except Exception as e:
                    logger.error(f"Error reading file sample: {e}")
            
        except Exception as e:
            logger.error(f"Error checking file size: {e}")
        
        logger.info(f"File validation successful: {uploaded_file.filename}")
        return True, "Valid PDF file"
    
    @staticmethod
    def validate_query(query: str) -> tuple[bool, str]:
        """Validate user query"""
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(query.strip()) < 3:
            return False, "Query must be at least 3 characters long"
        
        if len(query) > 1000:
            return False, "Query must be less than 1000 characters"
        
        return True, "Valid query"
    
    @staticmethod
    def validate_feedback_rating(rating: int) -> tuple[bool, str]:
        """Validate feedback rating"""
        if not isinstance(rating, int):
            return False, "Rating must be an integer"
        
        if rating < 1 or rating > 5:
            return False, "Rating must be between 1 and 5"
        
        return True, "Valid rating"

def safe_execute(func, default_return=None, log_error=True):
    """Safely execute a function with error handling"""
    try:
        return func()
    except Exception as e:
        if log_error:
            logger.error(f"Error in {func.__name__ if hasattr(func, '__name__') else 'function'}: {e}")
        return default_return

def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging"""
    import platform
    import psutil
    
    try:
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {'error': str(e)}
