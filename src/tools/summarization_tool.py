"""
Summarization Tool - Extract key points from documents

This tool wraps the AdaptiveQAChain's summarization functionality for
creating summaries and overviews.
"""

import logging
from typing import Dict, Any, List
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class SummarizationTool(BaseTool):
    """Tool for summarizing document content"""

    name = "summarization"
    description = "Summarize documents or extract key points (e.g., 'Summarize the main findings', 'Give me an overview')"

    def __init__(self, qa_chain=None):
        """
        Initialize summarization tool

        Args:
            qa_chain: AdaptiveQAChain instance
        """
        super().__init__()
        self.qa_chain = qa_chain

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if summarization is appropriate for this query

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        # Summarization is good for:
        # - Explicit summarization requests
        # - Overview/key points requests
        # - "Main" or "important" content extraction

        query_lower = query.lower()

        # High confidence keywords
        high_confidence_keywords = [
            'summarize', 'summary', 'overview', 'sum up',
            'key points', 'main points', 'highlights',
            'brief', 'in short', 'tldr', 'tl;dr'
        ]

        # Medium confidence keywords
        medium_confidence_keywords = [
            'main', 'important', 'significant', 'notable',
            'essential', 'critical', 'primary', 'core',
            'gist', 'essence', 'outline'
        ]

        # Check for high confidence match
        for keyword in high_confidence_keywords:
            if keyword in query_lower:
                return 0.95

        # Check for medium confidence match
        for keyword in medium_confidence_keywords:
            if keyword in query_lower:
                return 0.7

        # Not a summarization query
        return 0.2

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute summarization

        Args:
            query: User query
            context: Must contain:
                - 'qa_chain': AdaptiveQAChain instance
                - 'context_documents': Retrieved documents to summarize

        Returns:
            ToolResult with summary and citations
        """
        try:
            # Get qa_chain (use instance qa_chain or context)
            qa_chain = self.qa_chain or context.get('qa_chain')
            if not qa_chain:
                return ToolResult(
                    success=False,
                    error="QA chain not found"
                )

            # Get context documents
            context_documents = context.get('context_documents', [])
            if not context_documents:
                return ToolResult(
                    success=False,
                    error="No documents provided for summarization"
                )

            # Execute summarization
            logger.info(f"Executing summarization for: {query[:50]}...")
            result = qa_chain._summarization_chain(query, context_documents)

            # Extract answer and sources
            answer = result.get('answer', '')
            sources = result.get('sources', [])

            if not answer:
                return ToolResult(
                    success=False,
                    error="Summarization generated empty response"
                )

            # Convert sources to EnhancedCitation objects
            citations = self._convert_to_citations(sources, context_documents)

            logger.info(f"Summarization completed with {len(citations)} citations")

            return ToolResult(
                success=True,
                data={
                    'answer': answer,
                    'query_type': 'summarization'
                },
                metadata={
                    'tool': self.name,
                    'query': query,
                    'num_documents': len(context_documents),
                    'confidence': result.get('confidence', 'medium')
                },
                citations=citations
            )

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )

    def _convert_to_citations(
        self,
        sources: List[Dict[str, Any]],
        context_documents: List[Dict[str, Any]]
    ) -> List[EnhancedCitation]:
        """
        Convert source dictionaries to EnhancedCitation objects

        Args:
            sources: Source information from QA chain
            context_documents: Original context documents

        Returns:
            List of EnhancedCitation objects
        """
        citations = []

        # Match sources with context documents
        for idx, source in enumerate(sources):
            # Find matching document in context
            doc_name = source.get('document', f'document_{idx}')
            metadata = {}
            content = ""

            # Try to find matching context document
            for doc in context_documents:
                doc_metadata = doc.get('metadata', {})
                doc_id = (
                    doc_metadata.get('title') or
                    doc_metadata.get('original_filename') or
                    doc.get('id', '')
                )

                if doc_id == doc_name or doc_name in doc_id:
                    metadata = doc_metadata
                    content = doc.get('content', '')
                    break

            # Create citation
            citation = EnhancedCitation(
                document=doc_name,
                page_number=metadata.get('page_number', metadata.get('page', 0)),
                content=content,
                rank_position=idx + 1,
                metadata=metadata
            )

            citations.append(citation)

        return citations
