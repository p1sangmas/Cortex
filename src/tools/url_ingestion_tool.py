"""
URL Document Ingestion Tool - Ingest PDFs from URLs via n8n

This tool detects when users want to add documents from URLs to the knowledge base
and automatically ingests them via the n8n workflow.
"""

import logging
import re
import requests
from typing import Dict, Any, List
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class URLIngestionTool(BaseTool):
    """Tool for ingesting documents from URLs"""

    name = "url_ingestion"
    description = "Ingest PDF documents from URLs into the knowledge base when user provides a URL and asks to add/ingest/load it"

    def __init__(self):
        """Initialize URL ingestion tool"""
        super().__init__()

        # Get n8n base URL from environment/config
        try:
            from config.settings import N8N_BASE_URL
            self.n8n_base_url = N8N_BASE_URL
        except:
            self.n8n_base_url = "http://n8n:5678"

        self.webhook_url = f"{self.n8n_base_url}/webhook/ingest-url"
        self.timeout = 60  # seconds (document processing can take longer)

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if query is requesting URL document ingestion

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        query_lower = query.lower()

        # Check for URL presence (http:// or https://)
        has_url = bool(re.search(r'https?://[^\s]+', query))

        if not has_url:
            return 0.0  # No URL = can't ingest

        # Ingestion intent keywords
        ingestion_keywords = [
            'ingest', 'add', 'load', 'upload', 'import', 'fetch',
            'download', 'get', 'retrieve', 'index', 'process',
            'include', 'incorporate', 'bring in'
        ]

        # Document keywords
        document_keywords = [
            'document', 'pdf', 'file', 'paper', 'article',
            'report', 'manual', 'guide', 'book'
        ]

        # Knowledge base keywords
        kb_keywords = [
            'knowledge base', 'database', 'collection',
            'system', 'library', 'repository'
        ]

        has_ingestion_intent = any(kw in query_lower for kw in ingestion_keywords)
        has_document_ref = any(kw in query_lower for kw in document_keywords)
        has_kb_ref = any(kw in query_lower for kw in kb_keywords)

        # Very high confidence if has URL + explicit ingestion intent
        if has_url and has_ingestion_intent:
            return 0.95

        # High confidence if has URL + document reference
        if has_url and has_document_ref:
            return 0.85

        # Medium-high confidence if has URL + knowledge base reference
        if has_url and has_kb_ref:
            return 0.8

        # Medium confidence if just has URL and question-like
        # (e.g., "Can you look at https://...")
        if has_url and ('?' in query or query_lower.startswith(('can you', 'could you', 'please'))):
            return 0.6

        # Low confidence - has URL but unclear intent
        if has_url:
            return 0.3

        return 0.0

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute URL document ingestion

        Args:
            query: User query with URL
            context: Additional context

        Returns:
            ToolResult with ingestion status
        """
        try:
            # Extract URL from query
            url = self._extract_url(query)

            if not url:
                return ToolResult(
                    success=False,
                    error="Could not find a valid URL in your request. Please provide a URL starting with http:// or https://",
                    metadata={'tool': self.name}
                )

            # Extract optional filename from query
            filename = self._extract_filename(query, url)

            logger.info(f"Ingesting document from URL: {url}")

            # Check if n8n is available
            if not self._is_n8n_available():
                return ToolResult(
                    success=False,
                    error="Document ingestion service (n8n) is not available. Please ensure n8n is running.",
                    metadata={'tool': self.name, 'url': url}
                )

            # Call n8n webhook to ingest document
            payload = {'url': url}
            if filename:
                payload['filename'] = filename

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"n8n ingestion failed: {response.status_code}")
                return ToolResult(
                    success=False,
                    error=f"Document ingestion failed with status {response.status_code}. {response.text[:200]}",
                    metadata={'tool': self.name, 'url': url}
                )

            # Parse response
            data = response.json()

            if not data.get('success'):
                error_msg = data.get('error', 'Unknown error during ingestion')
                return ToolResult(
                    success=False,
                    error=f"Document ingestion failed: {error_msg}",
                    metadata={'tool': self.name, 'url': url}
                )

            # Extract file info
            file_info = data.get('file_info', {})
            filename = data.get('filename', filename or 'document.pdf')
            chunks = file_info.get('chunks', 0)
            size_kb = file_info.get('size', 0) / 1024 if file_info.get('size') else 0

            # Build success message
            answer = self._format_success_message(filename, url, chunks, size_kb, file_info)

            logger.info(f"Document ingested successfully: {filename} ({chunks} chunks)")

            return ToolResult(
                success=True,
                data={
                    'answer': answer,
                    'filename': filename,
                    'url': url,
                    'chunks': chunks,
                    'size_kb': size_kb
                },
                metadata={
                    'tool': self.name,
                    'url': url,
                    'filename': filename,
                    'chunks': chunks,
                    'ingestion_source': 'url'
                },
                citations=[]
            )

        except requests.exceptions.Timeout:
            logger.error(f"n8n webhook timeout after {self.timeout}s")
            return ToolResult(
                success=False,
                error=f"Document ingestion timed out after {self.timeout} seconds. The document may be too large or the service is busy.",
                metadata={'tool': self.name}
            )

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to n8n service")
            return ToolResult(
                success=False,
                error="Cannot connect to document ingestion service (n8n). Please ensure n8n is running.",
                metadata={'tool': self.name}
            )

        except Exception as e:
            logger.error(f"URL ingestion failed: {e}")
            return ToolResult(
                success=False,
                error=f"Document ingestion failed: {str(e)}",
                metadata={'tool': self.name}
            )

    def _extract_url(self, query: str) -> str:
        """
        Extract URL from query text

        Args:
            query: User query

        Returns:
            Extracted URL or empty string
        """
        # Match http:// or https:// URLs
        url_pattern = r'https?://[^\s<>"\'\)]+(?:\.pdf)?'
        match = re.search(url_pattern, query, re.IGNORECASE)

        if match:
            url = match.group(0)
            # Clean up trailing punctuation
            url = url.rstrip('.,;!?')
            return url

        return ""

    def _extract_filename(self, query: str, url: str) -> str:
        """
        Try to extract filename from query or URL

        Args:
            query: User query
            url: Document URL

        Returns:
            Filename or empty string
        """
        # Try to extract from patterns like "as <filename>" or "name it <filename>"
        patterns = [
            r'(?:as|name(?:\s+it)?|call(?:\s+it)?)\s+["\']?([a-zA-Z0-9_-]+\.pdf)["\']?',
            r'filename[:\s]+["\']?([a-zA-Z0-9_-]+\.pdf)["\']?'
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback: Extract from URL
        url_parts = url.split('/')
        if url_parts:
            potential_filename = url_parts[-1].split('?')[0]  # Remove query params
            if potential_filename.lower().endswith('.pdf'):
                return potential_filename

        return ""

    def _is_n8n_available(self) -> bool:
        """
        Check if n8n service is available

        Returns:
            True if n8n is reachable
        """
        try:
            response = requests.get(self.n8n_base_url, timeout=2)
            return response.status_code in [200, 401, 403]
        except:
            return False

    def _format_success_message(
        self,
        filename: str,
        url: str,
        chunks: int,
        size_kb: float,
        file_info: Dict[str, Any]
    ) -> str:
        """
        Format success message for user

        Args:
            filename: Document filename
            url: Source URL
            chunks: Number of chunks created
            size_kb: File size in KB
            file_info: Additional file information

        Returns:
            Formatted success message
        """
        extraction_method = file_info.get('extraction_method', 'PyMuPDF')

        message = f"""✅ **Document successfully ingested!**

**File:** `{filename}`
**Source:** {url}
**Size:** {size_kb:.1f} KB
**Chunks:** {chunks} chunks created
**Extraction:** {extraction_method}

The document has been processed and added to the knowledge base. You can now ask questions about its contents!"""

        return message
