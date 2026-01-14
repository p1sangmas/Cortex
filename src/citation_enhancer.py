"""
Citation Enhancer - Enhances citations with excerpts and confidence scores

This component takes basic citations and enriches them with:
- Relevant excerpts (50-200 chars) from the source
- Composite confidence scores from multiple signals
- Additional metadata for better source attribution
"""

import logging
import re
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.tools import EnhancedCitation, ToolResult
from config.settings import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class CitationEnhancer:
    """Enhances citations with excerpts and confidence scores"""

    def __init__(self, embedding_model: Optional[str] = None):
        """
        Initialize citation enhancer

        Args:
            embedding_model: Name of sentence transformer model
        """
        self.logger = logging.getLogger(f"{__name__}.CitationEnhancer")

        # Initialize embedding model for excerpt selection
        import torch
        device = 'cpu'  # Force CPU for stability
        model_name = embedding_model or EMBEDDING_MODEL
        self.model = SentenceTransformer(model_name, device=device)

    def enhance(
        self,
        tool_results: List[ToolResult],
        query: Optional[str] = None
    ) -> List[EnhancedCitation]:
        """
        Enhance citations from tool results

        Args:
            tool_results: List of ToolResult objects with citations
            query: Original user query (for relevance scoring)

        Returns:
            List of EnhancedCitation objects with excerpts and confidence
        """
        self.logger.info(f"Enhancing citations from {len(tool_results)} tool results")

        enhanced_citations = []

        for result in tool_results:
            if not result.success or not result.citations:
                continue

            for citation in result.citations:
                # Extract best excerpt
                excerpt = self._extract_excerpt(citation, query)

                # Calculate composite confidence
                confidence = self._calculate_confidence(citation, result)

                # Create enhanced citation
                enhanced = EnhancedCitation(
                    document=citation.document,
                    page_number=citation.page_number or 0,
                    excerpt=excerpt,
                    confidence_score=confidence,
                    similarity_score=citation.similarity_score,
                    cross_encoder_score=citation.cross_encoder_score,
                    rank_position=citation.rank_position,
                    content=citation.content,
                    metadata=citation.metadata
                )

                enhanced_citations.append(enhanced)

        # Sort by confidence (highest first)
        enhanced_citations.sort(key=lambda c: c.confidence_score, reverse=True)

        # Re-rank positions after sorting
        for idx, citation in enumerate(enhanced_citations):
            citation.rank_position = idx + 1

        self.logger.info(f"Enhanced {len(enhanced_citations)} citations")

        return enhanced_citations

    def _extract_excerpt(
        self,
        citation: EnhancedCitation,
        query: Optional[str] = None
    ) -> str:
        """
        Extract most relevant excerpt from citation content

        Args:
            citation: Citation object
            query: User query for relevance matching

        Returns:
            Excerpt string (50-200 chars)
        """
        content = citation.content

        if not content or len(content) < 50:
            return content[:200] if content else ""

        # If no query, return first 200 chars
        if not query:
            return self._truncate_to_sentence(content[:200])

        # Split content into sentences
        sentences = self._split_sentences(content)

        if not sentences:
            return self._truncate_to_sentence(content[:200])

        # Find sentence most similar to query
        try:
            query_emb = self.model.encode([query])
            sent_embs = self.model.encode(sentences)

            similarities = cosine_similarity(query_emb, sent_embs)[0]
            best_idx = similarities.argmax()

            best_sentence = sentences[best_idx]

            # Truncate if too long
            if len(best_sentence) > 200:
                return self._truncate_to_sentence(best_sentence[:200])

            # If too short, add context
            if len(best_sentence) < 50 and best_idx + 1 < len(sentences):
                combined = best_sentence + " " + sentences[best_idx + 1]
                return self._truncate_to_sentence(combined[:200])

            return best_sentence

        except Exception as e:
            self.logger.warning(f"Excerpt extraction failed: {e}")
            return self._truncate_to_sentence(content[:200])

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Enhanced sentence splitting pattern
        sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+'
        sentences = re.split(sentence_pattern, text)

        # Clean and filter
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum sentence length
                cleaned.append(sentence)

        return cleaned

    def _truncate_to_sentence(self, text: str) -> str:
        """
        Truncate text to complete sentence boundary

        Args:
            text: Text to truncate

        Returns:
            Truncated text
        """
        if len(text) <= 200:
            return text

        # Try to truncate at sentence boundary
        for delimiter in ['. ', '! ', '? ']:
            idx = text[:200].rfind(delimiter)
            if idx > 50:  # At least 50 chars
                return text[:idx + 1].strip()

        # Fallback: truncate at word boundary
        words = text[:200].split()
        return ' '.join(words[:-1]) + '...'

    def _calculate_confidence(
        self,
        citation: EnhancedCitation,
        result: ToolResult
    ) -> float:
        """
        Calculate composite confidence score from multiple signals

        Args:
            citation: Citation object with scores
            result: ToolResult for additional context

        Returns:
            Confidence score (0.0-1.0)
        """
        # Component scores
        similarity = citation.similarity_score or 0.0
        cross_score = citation.cross_encoder_score or 0.0
        rank = citation.rank_position or 10

        # Rank-based confidence (decays with position)
        # Top result = 1.0, 5th result = 0.6, 10th result = 0.1
        rank_confidence = max(0.1, 1.0 - (rank - 1) * 0.1)

        # Tool confidence (from metadata)
        tool_confidence = result.metadata.get('confidence', 1.0)

        # Weighted combination
        # Similarity: 30%
        # Cross-encoder: 40% (if available, most accurate)
        # Rank: 20%
        # Tool: 10%

        if cross_score > 0:
            # Use cross-encoder if available (more accurate)
            confidence = (
                similarity * 0.3 +
                cross_score * 0.4 +
                rank_confidence * 0.2 +
                tool_confidence * 0.1
            )
        else:
            # Fall back to similarity + rank + tool
            confidence = (
                similarity * 0.5 +
                rank_confidence * 0.3 +
                tool_confidence * 0.2
            )

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def deduplicate_citations(
        self,
        citations: List[EnhancedCitation],
        similarity_threshold: float = 0.9
    ) -> List[EnhancedCitation]:
        """
        Remove duplicate or highly similar citations

        Args:
            citations: List of citations
            similarity_threshold: Threshold for considering citations duplicate

        Returns:
            Deduplicated list
        """
        if not citations:
            return []

        # Keep track of unique citations
        unique = []
        seen_content = []

        for citation in citations:
            # Check if this citation is too similar to existing ones
            is_duplicate = False

            if citation.content:
                try:
                    # Embed current citation
                    current_emb = self.model.encode([citation.content])

                    # Compare with seen citations
                    if seen_content:
                        seen_embs = self.model.encode(seen_content)
                        similarities = cosine_similarity(current_emb, seen_embs)[0]

                        if np.max(similarities) > similarity_threshold:
                            is_duplicate = True

                except Exception as e:
                    self.logger.warning(f"Deduplication comparison failed: {e}")

            if not is_duplicate:
                unique.append(citation)
                if citation.content:
                    seen_content.append(citation.content)

        self.logger.info(f"Deduplicated {len(citations)} → {len(unique)} citations")

        return unique

    def filter_by_confidence(
        self,
        citations: List[EnhancedCitation],
        min_confidence: float = 0.3
    ) -> List[EnhancedCitation]:
        """
        Filter citations by minimum confidence threshold

        Args:
            citations: List of citations
            min_confidence: Minimum confidence to keep

        Returns:
            Filtered list
        """
        filtered = [c for c in citations if c.confidence_score >= min_confidence]

        self.logger.info(
            f"Filtered citations by confidence {min_confidence}: "
            f"{len(citations)} → {len(filtered)}"
        )

        return filtered

    def group_by_document(
        self,
        citations: List[EnhancedCitation]
    ) -> Dict[str, List[EnhancedCitation]]:
        """
        Group citations by source document

        Args:
            citations: List of citations

        Returns:
            Dictionary mapping document names to citation lists
        """
        groups = {}

        for citation in citations:
            doc_name = citation.document

            if doc_name not in groups:
                groups[doc_name] = []

            groups[doc_name].append(citation)

        # Sort citations within each group by page number
        for doc_name in groups:
            groups[doc_name].sort(key=lambda c: (c.page_number, c.rank_position))

        self.logger.info(f"Grouped {len(citations)} citations into {len(groups)} documents")

        return groups
