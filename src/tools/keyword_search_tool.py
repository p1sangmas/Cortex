"""
Keyword Search Tool - Exact term matching using TF-IDF

This tool wraps the HybridRetriever's keyword search functionality for
exact term matching and proper noun searches.
"""

import logging
from typing import Dict, Any
import re
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class KeywordSearchTool(BaseTool):
    """Tool for keyword-based document search using TF-IDF"""

    name = "keyword_search"
    description = "Search documents using exact keyword matching for names, dates, technical terms, and quoted text"

    def __init__(self, retriever=None):
        """
        Initialize keyword search tool

        Args:
            retriever: HybridRetriever instance
        """
        super().__init__()
        self.retriever = retriever

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if keyword search is appropriate for this query

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        # Keyword search is good for:
        # - Queries with quotes (exact matches)
        # - Proper nouns (capitalized words)
        # - Dates and numbers
        # - Technical terms
        # - "Find" or "search" commands

        query_lower = query.lower()

        # Check for quoted text (very high confidence for exact match)
        if '"' in query or "'" in query:
            return 0.95

        # Check for "find" or "search" commands
        find_commands = ['find', 'search for', 'locate', 'look for', 'show me']
        for command in find_commands:
            if query_lower.startswith(command):
                return 0.9

        # Check for proper nouns (capitalized words that aren't at sentence start)
        words = query.split()
        if len(words) > 1:
            # Count capitalized words that aren't the first word
            proper_nouns = sum(1 for i, word in enumerate(words[1:], 1)
                             if word[0].isupper() and word not in ['I', 'A'])
            if proper_nouns > 0:
                return 0.85

        # Check for dates
        date_pattern = r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(January|February|March|April|May|June|July|August|September|October|November|December)\b'
        if re.search(date_pattern, query, re.IGNORECASE):
            return 0.8

        # Check for specific terms that benefit from keyword matching
        keyword_indicators = [
            'named', 'called', 'titled', 'specifically', 'exactly',
            'term', 'word', 'phrase', 'mentions', 'references'
        ]
        for indicator in keyword_indicators:
            if indicator in query_lower:
                return 0.75

        # Keyword search is moderately useful for most queries as backup
        return 0.5

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute keyword search

        Args:
            query: User query
            context: Must contain 'retriever' key with HybridRetriever instance

        Returns:
            ToolResult with retrieved documents and citations
        """
        try:
            # Get retriever (use instance retriever or context)
            retriever = self.retriever or context.get('retriever')
            if not retriever:
                return ToolResult(
                    success=False,
                    error="Retriever not found"
                )

            # Check if keyword search is available
            if retriever.tfidf_matrix is None:
                logger.warning("TF-IDF matrix not built, keyword search unavailable")
                return ToolResult(
                    success=False,
                    error="Keyword search index not available"
                )

            # Get top_k from context or use default
            top_k = context.get('top_k', 5)

            # Perform keyword search
            logger.info(f"Executing keyword search for: {query[:50]}...")
            results = retriever._keyword_search(query, top_k)

            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={'message': 'No matching keywords found'},
                    citations=[]
                )

            # Convert results to EnhancedCitation objects
            citations = []
            for idx, result in enumerate(results):
                metadata = result.get('metadata', {})

                # Extract document name
                doc_name = (
                    metadata.get('title') or
                    metadata.get('original_filename') or
                    metadata.get('display_name') or
                    result.get('id', f'document_{idx}')
                )

                # Create citation
                citation = EnhancedCitation(
                    document=doc_name,
                    page_number=metadata.get('page_number', metadata.get('page', 0)),
                    content=result.get('content', ''),
                    similarity_score=result.get('keyword_score', 0.0),
                    rank_position=idx + 1,
                    metadata=metadata
                )

                citations.append(citation)

            logger.info(f"Keyword search found {len(citations)} results")

            return ToolResult(
                success=True,
                data=results,
                metadata={
                    'tool': self.name,
                    'method': 'keyword',
                    'query': query,
                    'num_results': len(results)
                },
                citations=citations
            )

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )
