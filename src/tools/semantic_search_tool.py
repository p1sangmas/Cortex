"""
Semantic Search Tool - Dense retrieval using embeddings

This tool wraps the HybridRetriever's semantic search functionality for
conceptual/thematic queries.
"""

import logging
from typing import Dict, Any
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class SemanticSearchTool(BaseTool):
    """Tool for semantic/conceptual document search using embeddings"""

    name = "semantic_search"
    description = "Search documents using semantic similarity for conceptual questions (e.g., 'What are the benefits of X?', 'Explain Y')"

    def __init__(self, retriever=None):
        """
        Initialize semantic search tool

        Args:
            retriever: HybridRetriever instance
        """
        super().__init__()
        self.retriever = retriever

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if semantic search is appropriate for this query

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        # Semantic search is good for:
        # - Conceptual questions ("what", "why", "how", "explain")
        # - Thematic queries ("benefits", "advantages", "issues")
        # - General information requests

        query_lower = query.lower()

        # High confidence keywords
        high_confidence_keywords = [
            'what is', 'what are', 'explain', 'describe',
            'tell me about', 'information about', 'details about',
            'how does', 'why', 'benefits', 'advantages',
            'disadvantages', 'pros', 'cons', 'issues'
        ]

        # Medium confidence keywords
        medium_confidence_keywords = [
            'what', 'how', 'understand', 'learn', 'know',
            'concept', 'idea', 'meaning', 'definition'
        ]

        # Check for high confidence match
        for keyword in high_confidence_keywords:
            if keyword in query_lower:
                return 0.9

        # Check for medium confidence match
        for keyword in medium_confidence_keywords:
            if keyword in query_lower:
                return 0.7

        # Semantic search is generally useful for most queries
        # as a baseline retrieval method
        return 0.6

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute semantic search

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

            # Get top_k from context or use default
            top_k = context.get('top_k', 5)

            # Perform hybrid retrieval (semantic + keyword + reranking)
            # Use the full retrieve() method instead of just _semantic_search()
            # This ensures same quality as traditional mode
            logger.info(f"Executing semantic search for: {query[:50]}...")
            results = retriever.retrieve(query, top_k)

            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={'message': 'No documents found'},
                    citations=[]
                )

            # Convert results to EnhancedCitation objects
            citations = []
            for idx, result in enumerate(results):
                metadata = result.get('metadata', {})

                # Extract document name (prioritize title, then original_filename)
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
                    similarity_score=result.get('semantic_score', 0.0),
                    rank_position=idx + 1,
                    metadata=metadata
                )

                citations.append(citation)

            logger.info(f"Semantic search found {len(citations)} results")

            # Calculate confidence score from top results
            # Use average of top 3 cross-encoder scores (most reliable metric)
            confidence = 0.0
            if citations:
                top_scores = [c.cross_encoder_score for c in citations[:3] if c.cross_encoder_score > 0]
                if top_scores:
                    confidence = sum(top_scores) / len(top_scores)
                    logger.info(f"Confidence from cross-encoder scores: {confidence:.3f} (scores: {[f'{s:.3f}' for s in top_scores]})")
                else:
                    # Fallback to similarity scores if cross-encoder not available
                    top_sim_scores = [c.similarity_score for c in citations[:3]]
                    if top_sim_scores:
                        confidence = sum(top_sim_scores) / len(top_sim_scores)
                        logger.info(f"Confidence from similarity scores: {confidence:.3f} (scores: {[f'{s:.3f}' for s in top_sim_scores]})")

            logger.info(f"Semantic search confidence: {confidence:.3f}")

            return ToolResult(
                success=True,
                data=results,
                metadata={
                    'tool': self.name,
                    'method': 'semantic',
                    'query': query,
                    'num_results': len(results),
                    'confidence': confidence  # Add confidence score
                },
                citations=citations
            )

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )
