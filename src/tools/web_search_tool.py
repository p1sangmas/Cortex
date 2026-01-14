"""
Web Search Tool - External knowledge retrieval via n8n

This tool uses n8n workflows to search the web when internal
documents don't have sufficient information.
"""

import logging
import requests
from typing import Dict, Any, List
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for searching external web sources via n8n webhooks"""

    name = "web_search"
    description = "Search external web sources for information not found in internal documents (e.g., current events, external facts, recent data)"

    def __init__(self, llm_handler=None, qa_chain=None):
        """
        Initialize web search tool

        Args:
            llm_handler: Optional OllamaHandler for LLM-generated answers
            qa_chain: Optional AdaptiveQAChain for answer generation
        """
        super().__init__()

        # Get n8n base URL from environment/config
        try:
            from config.settings import N8N_BASE_URL
            self.n8n_base_url = N8N_BASE_URL
        except:
            self.n8n_base_url = "http://n8n:5678"

        self.webhook_url = f"{self.n8n_base_url}/webhook/web-search"
        self.timeout = 30  # seconds

        # LLM components for synthesizing answers
        self.llm_handler = llm_handler
        self.qa_chain = qa_chain

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if web search is appropriate

        Args:
            query: User query
            context: Additional context including:
                - 'internal_confidence': Confidence of internal search results
                - 'internal_results_count': Number of internal results found

        Returns:
            Confidence score (0-1)
        """
        query_lower = query.lower()

        # Check if internal results have low confidence
        internal_confidence = context.get('internal_confidence', 1.0)
        internal_results = context.get('internal_results_count', 1)

        # Very high confidence if no internal results
        if internal_results == 0:
            return 0.85

        # High confidence if internal results have low confidence
        if internal_confidence < 0.5:
            return 0.8

        # Keywords suggesting external/current information needed
        external_keywords = [
            'current', 'latest', 'recent', 'today', 'now',
            'this year', '2024', '2025', '2026',
            'news', 'update', 'breaking',
            'what is the current', 'as of'
        ]

        for keyword in external_keywords:
            if keyword in query_lower:
                return 0.75

        # Questions about entities not likely in internal docs
        external_entities = [
            'weather', 'stock price', 'exchange rate',
            'population', 'distance', 'time zone',
            'wikipedia', 'google', 'website'
        ]

        for entity in external_entities:
            if entity in query_lower:
                return 0.7

        # Medium confidence if internal results are moderate
        if internal_confidence < 0.7:
            return 0.5

        # Low confidence - internal results should be sufficient
        return 0.3

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute web search via n8n webhook

        Args:
            query: User query
            context: May contain internal search results to synthesize

        Returns:
            ToolResult with web search results
        """
        try:
            # Check if n8n is available
            if not self._is_n8n_available():
                logger.warning("n8n service not available, web search unavailable")
                return ToolResult(
                    success=False,
                    error="Web search service (n8n) is not available. Please ensure n8n is running.",
                    metadata={
                        'tool': self.name,
                        'n8n_url': self.webhook_url
                    }
                )

            # Call n8n webhook
            logger.info(f"Calling n8n web search for: {query[:50]}...")
            response = requests.post(
                self.webhook_url,
                json={
                    'query': query,
                    'max_results': 5
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"n8n webhook failed: {response.status_code}")
                return ToolResult(
                    success=False,
                    error=f"Web search failed with status {response.status_code}",
                    metadata={'tool': self.name}
                )

            # Parse response
            data = response.json()
            search_results = data.get('results', [])  # Also try 'results' key
            if not search_results:
                search_results = data.get('search_results', [])

            # Check for helpful error message from n8n
            help_message = data.get('help_message', '')

            if not search_results:
                logger.warning("Web search returned no results")

                # Build user-friendly error message
                error_msg = 'No external search results found.'
                if help_message:
                    error_msg = help_message
                else:
                    error_msg += ' The web search API works best for well-known topics. Try rephrasing your question to be more specific.'

                return ToolResult(
                    success=False,  # Mark as failed when no results
                    error=error_msg,
                    metadata={
                        'tool': self.name,
                        'message': error_msg,
                        'suggestion': 'Try rephrasing with more specific terms (e.g., "Python programming language" instead of "what is python?")'
                    },
                    citations=[]
                )

            # Convert search results to citations
            citations = self._convert_search_results(search_results)

            # Format answer from search results
            answer = self._format_answer(query, search_results)

            logger.info(f"Web search found {len(citations)} results")

            return ToolResult(
                success=True,
                data={
                    'answer': answer,
                    'search_results': search_results,
                    'query_type': 'web_search'
                },
                metadata={
                    'tool': self.name,
                    'query': query,
                    'num_results': len(search_results),
                    'source': 'external_web'
                },
                citations=citations
            )

        except requests.exceptions.Timeout:
            logger.error(f"n8n webhook timeout after {self.timeout}s")
            return ToolResult(
                success=False,
                error=f"Web search timed out after {self.timeout} seconds",
                metadata={'tool': self.name}
            )

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to n8n service")
            return ToolResult(
                success=False,
                error="Cannot connect to n8n service. Please ensure n8n is running.",
                metadata={'tool': self.name, 'n8n_url': self.webhook_url}
            )

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )

    def _is_n8n_available(self) -> bool:
        """
        Check if n8n service is available

        Returns:
            True if n8n is reachable
        """
        try:
            # Try to reach n8n healthcheck or base URL
            response = requests.get(
                self.n8n_base_url,
                timeout=2
            )
            return response.status_code in [200, 401, 403]  # Any response means it's up
        except:
            return False

    def _convert_search_results(
        self,
        search_results: List[Dict[str, Any]]
    ) -> List[EnhancedCitation]:
        """
        Convert web search results to EnhancedCitation objects

        Args:
            search_results: List of search result dictionaries

        Returns:
            List of EnhancedCitation objects
        """
        citations = []

        for idx, result in enumerate(search_results):
            title = result.get('title', f'Web Result {idx+1}')
            url = result.get('url', '')
            snippet = result.get('snippet', result.get('description', ''))

            citation = EnhancedCitation(
                document=f"{title} (External Source)",
                page_number=0,  # Web results don't have pages
                excerpt=snippet[:200] if snippet else "",
                content=snippet,
                rank_position=idx + 1,
                metadata={
                    'source': 'external_web',
                    'url': url,
                    'title': title
                }
            )

            citations.append(citation)

        return citations

    def _format_answer(
        self,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Format answer from search results using LLM synthesis

        Args:
            query: User query
            search_results: List of search results

        Returns:
            Formatted answer string (LLM-synthesized if available, else formatted list)
        """
        if not search_results:
            return "No external information found for this query."

        # If LLM is available, synthesize answer from search results
        if self.llm_handler:
            return self._synthesize_answer_with_llm(query, search_results)

        # Fallback: Format as list (original behavior)
        return self._format_answer_as_list(query, search_results)

    def _synthesize_answer_with_llm(
        self,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Use LLM to synthesize a coherent answer from search results

        Args:
            query: User query
            search_results: List of search results

        Returns:
            LLM-synthesized answer
        """
        # Take top 5 results for context
        top_results = search_results[:5]

        # Build context from search results
        context_parts = []
        for idx, result in enumerate(top_results, 1):
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', result.get('description', ''))
            url = result.get('url', '')

            if snippet:
                context_parts.append(f"Source {idx} - {title}:\n{snippet}\nURL: {url}\n")

        context = "\n".join(context_parts)

        # Create prompt for LLM
        prompt = f"""Based on the following external web search results, provide a comprehensive and accurate answer to the question. Synthesize information from multiple sources when relevant.

Question: {query}

Web Search Results:
{context}

Instructions:
- Provide a clear, direct answer to the question
- Synthesize information from the search results
- Be factual and objective
- If multiple sources provide conflicting information, mention this
- Keep the answer concise (2-4 paragraphs maximum)
- Do not add information not present in the search results

Answer:"""

        try:
            # Generate answer using LLM
            answer = self.llm_handler.generate(
                prompt,
                temperature=0.3,  # Lower temperature for factual accuracy
                max_tokens=400
            )

            # Add source attribution note
            answer += "\n\n---\n*Source: External web search. Information synthesized from multiple sources.*"

            logger.info("LLM successfully synthesized answer from web search results")
            return answer

        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}, falling back to list format")
            return self._format_answer_as_list(query, search_results)

    def _format_answer_as_list(
        self,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        Format answer as a list of search results (fallback method)

        Args:
            query: User query
            search_results: List of search results

        Returns:
            Formatted list of results
        """
        # Take top 3 results
        top_results = search_results[:3]

        answer_parts = []

        for idx, result in enumerate(top_results, 1):
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', result.get('description', ''))

            if snippet:
                answer_parts.append(f"**{idx}. {title}**")
                answer_parts.append(f"{snippet}")
                answer_parts.append("")

        # Add source verification note
        answer_parts.append("---")
        answer_parts.append("*Source: External web search. Please verify for accuracy.*")

        return "\n".join(answer_parts)
