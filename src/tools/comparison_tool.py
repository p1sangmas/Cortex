"""
Document Comparison Tool - Side-by-side comparison of documents

This tool extracts entities from comparison queries and generates
structured comparisons using the LLM.
"""

import logging
import re
from typing import Dict, Any, List, Tuple
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class DocumentComparisonTool(BaseTool):
    """Tool for comparing documents or sections side-by-side"""

    name = "comparison"
    description = "Compare two or more documents, sections, or concepts side-by-side (e.g., 'Compare Policy A and Policy B', 'Differences between X and Y')"

    def __init__(self, retriever=None, llm_handler=None, qa_chain=None):
        """
        Initialize comparison tool

        Args:
            retriever: HybridRetriever instance for document retrieval
            llm_handler: OllamaHandler instance for LLM-based comparison
            qa_chain: AdaptiveQAChain instance for comparison chain
        """
        super().__init__()
        self.retriever = retriever
        self.llm_handler = llm_handler
        self.qa_chain = qa_chain

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if this is a comparison query

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        query_lower = query.lower()

        # Very high confidence keywords
        high_confidence_keywords = [
            'compare', 'comparison', 'versus', ' vs ', ' vs.',
            'difference between', 'differences between',
            'contrast', 'contrasting'
        ]

        # Medium confidence keywords
        medium_confidence_keywords = [
            'differ', 'similar', 'similarities',
            'against', 'relative to', 'compared to',
            'better than', 'worse than'
        ]

        # Check for high confidence
        for keyword in high_confidence_keywords:
            if keyword in query_lower:
                return 0.95

        # Check for medium confidence
        for keyword in medium_confidence_keywords:
            if keyword in query_lower:
                return 0.75

        # Check for "A and B" pattern (likely comparison)
        if ' and ' in query_lower:
            words = query_lower.split()
            if 'and' in words and len(words) > 3:
                return 0.6

        return 0.2

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute document comparison

        Args:
            query: User query
            context: Must contain:
                - 'retriever': HybridRetriever instance
                - 'qa_chain': AdaptiveQAChain instance

        Returns:
            ToolResult with comparison and citations
        """
        try:
            # Get dependencies (use instance or context)
            retriever = self.retriever or context.get('retriever')
            llm_handler = self.llm_handler or context.get('llm_handler')
            qa_chain = self.qa_chain or context.get('qa_chain')

            if not retriever:
                return ToolResult(
                    success=False,
                    error="Retriever not found"
                )

            if not qa_chain:
                return ToolResult(
                    success=False,
                    error="QA chain required for comparison"
                )

            # Extract entities to compare
            entities = self._extract_comparison_entities(query)
            logger.info(f"Extracted entities for comparison: {entities}")

            # If we have specific entities, retrieve documents for each
            all_documents = []
            if entities:
                for entity in entities:
                    # Search for documents related to this entity
                    docs = retriever._semantic_search(entity, 3)
                    all_documents.extend(docs)
            else:
                # Generic comparison - use original query
                all_documents = retriever.retrieve(query, 5)

            if not all_documents:
                return ToolResult(
                    success=False,
                    error="No documents found for comparison",
                    metadata={'entities': entities}
                )

            # Use comparison chain to generate structured comparison
            logger.info(f"Generating comparison with {len(all_documents)} documents")
            result = qa_chain._comparison_chain(query, all_documents)

            # Extract answer and sources
            answer = result.get('answer', '')
            sources = result.get('sources', [])

            if not answer:
                return ToolResult(
                    success=False,
                    error="Comparison generated empty response"
                )

            # Convert sources to EnhancedCitation objects
            citations = self._convert_to_citations(sources, all_documents)

            logger.info(f"Comparison completed with {len(citations)} citations")

            return ToolResult(
                success=True,
                data={
                    'answer': answer,
                    'query_type': 'comparison',
                    'entities': entities
                },
                metadata={
                    'tool': self.name,
                    'query': query,
                    'num_documents': len(all_documents),
                    'entities_compared': entities,
                    'confidence': result.get('confidence', 'medium')
                },
                citations=citations
            )

        except Exception as e:
            logger.error(f"Document comparison failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )

    def _extract_comparison_entities(self, query: str) -> List[str]:
        """
        Extract entities to compare from query

        Args:
            query: User query

        Returns:
            List of entity strings to compare
        """
        entities = []

        # Pattern 1: "Compare X and Y"
        pattern1 = r'compare\s+([^,]+?)\s+and\s+([^,]+?)(?:\s|$|\.)'
        match1 = re.search(pattern1, query, re.IGNORECASE)
        if match1:
            entities.append(match1.group(1).strip())
            entities.append(match1.group(2).strip())
            return entities

        # Pattern 2: "X versus Y" or "X vs Y"
        pattern2 = r'([^,]+?)\s+(?:versus|vs\.?|vs)\s+([^,]+?)(?:\s|$|\.)'
        match2 = re.search(pattern2, query, re.IGNORECASE)
        if match2:
            entities.append(match2.group(1).strip())
            entities.append(match2.group(2).strip())
            return entities

        # Pattern 3: "Difference between X and Y"
        pattern3 = r'difference(?:s)?\s+between\s+([^,]+?)\s+and\s+([^,]+?)(?:\s|$|\.)'
        match3 = re.search(pattern3, query, re.IGNORECASE)
        if match3:
            entities.append(match3.group(1).strip())
            entities.append(match3.group(2).strip())
            return entities

        # Pattern 4: "X and Y" (generic)
        pattern4 = r'([A-Z][a-zA-Z0-9\s]+?)\s+and\s+([A-Z][a-zA-Z0-9\s]+)'
        match4 = re.search(pattern4, query)
        if match4:
            entities.append(match4.group(1).strip())
            entities.append(match4.group(2).strip())
            return entities

        # If no specific entities found, return empty list
        # The tool will fall back to semantic search with full query
        return entities

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
