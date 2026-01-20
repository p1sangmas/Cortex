"""
Agentic Orchestrator - Main orchestrator with tool selection

This is the brain of the agentic RAG system. It:
1. Analyzes queries to determine complexity and intent
2. Selects appropriate tools using hybrid approach (rules + LLM)
3. Creates execution plans
4. Executes tools via ExecutionEngine
5. Synthesizes final responses with reasoning traces
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from src.agent.query_analyzer import QueryAnalyzer
from src.agent.execution_engine import ExecutionEngine, ExecutionPlan, ExecutionStrategy
from src.tools import ToolRegistry, BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


@dataclass
class AgenticResponse:
    """Response from agentic orchestrator"""
    answer: str
    sources: List[EnhancedCitation] = field(default_factory=list)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    mode: str = "agentic"


class AgenticOrchestrator:
    """Main orchestrator for agentic RAG system"""

    def __init__(
        self,
        retriever=None,
        qa_chain=None,
        llm_handler=None,
        use_llm_fallback: bool = True
    ):
        """
        Initialize agentic orchestrator

        Args:
            retriever: HybridRetriever instance for document retrieval
            qa_chain: AdaptiveQAChain instance for answer generation
            llm_handler: OllamaHandler instance for LLM calls
            use_llm_fallback: Whether to use LLM for ambiguous tool selection
        """
        self.logger = logging.getLogger(f"{__name__}.AgenticOrchestrator")

        # External dependencies (store first for tool initialization)
        self.retriever = retriever
        self.qa_chain = qa_chain
        self.llm_handler = llm_handler

        # Core components (query_analyzer needs llm_handler)
        self.query_analyzer = QueryAnalyzer(llm_handler=llm_handler)
        self.execution_engine = ExecutionEngine(max_parallel_workers=3)
        self.tool_registry = ToolRegistry()

        # Configuration
        self.use_llm_fallback = use_llm_fallback
        self.min_tool_confidence = 0.3

        # Reasoning trace
        self.reasoning_trace = []

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all available tools"""
        try:
            # Import tools
            from src.tools.semantic_search_tool import SemanticSearchTool
            from src.tools.keyword_search_tool import KeywordSearchTool
            from src.tools.summarization_tool import SummarizationTool
            from src.tools.comparison_tool import DocumentComparisonTool
            from src.tools.calculator_tool import CalculatorTool
            from src.tools.web_search_tool import WebSearchTool
            from src.tools.url_ingestion_tool import URLIngestionTool

            # Register basic tools
            if self.retriever:
                self.tool_registry.register(SemanticSearchTool(self.retriever))
                self.tool_registry.register(KeywordSearchTool(self.retriever))
                self.logger.info("Registered search tools")

            if self.qa_chain:
                self.tool_registry.register(SummarizationTool(self.qa_chain))
                self.logger.info("Registered summarization tool")

            # Register advanced tools
            if self.retriever and self.llm_handler and self.qa_chain:
                self.tool_registry.register(
                    DocumentComparisonTool(self.retriever, self.llm_handler, self.qa_chain)
                )
                self.logger.info("Registered comparison tool")

            self.tool_registry.register(CalculatorTool())
            # Pass llm_handler to web search for answer synthesis
            self.tool_registry.register(
                WebSearchTool(llm_handler=self.llm_handler, qa_chain=self.qa_chain)
            )
            self.tool_registry.register(URLIngestionTool())
            self.logger.info("Registered calculator, web search, and URL ingestion tools")

            self.logger.info(
                f"Tool registry initialized with {len(self.tool_registry.tools)} tools"
            )

        except ImportError as e:
            self.logger.warning(f"Could not register some tools: {e}")

    def process_query(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> AgenticResponse:
        """
        Process query with agentic approach

        Args:
            query: User query
            session_context: Optional session context (chat history, user prefs)

        Returns:
            AgenticResponse with answer, citations, and reasoning trace
        """
        self.logger.info(f"Processing query: {query[:50]}...")

        # Clear reasoning trace
        self.reasoning_trace = []

        try:
            # Step 1: Analyze query
            analysis = self.query_analyzer.analyze(query)
            self.reasoning_trace.append({
                'step': 'query_analysis',
                'complexity': analysis['complexity'],
                'intent': analysis['intent'],
                'requires_multiple_tools': analysis['requires_multiple_tools']
            })

            self.logger.info(
                f"Query analysis: complexity={analysis['complexity']}, "
                f"intent={analysis['intent']}"
            )

            # Handle conversational queries (no tools needed)
            if analysis['intent'] == 'conversational':
                return self._handle_conversational(query)

            # Step 2: Select tools
            selected_tools = self._select_tools(query, analysis, session_context or {})

            if not selected_tools:
                return self._fallback_response(
                    query,
                    "No suitable tools found for this query"
                )

            self.reasoning_trace.append({
                'step': 'tool_selection',
                'tools': [{'name': t.name, 'confidence': c} for t, c in selected_tools],
                'selection_method': 'hybrid'
            })

            self.logger.info(
                f"Selected {len(selected_tools)} tools: "
                f"{[t.name for t, _ in selected_tools]}"
            )

            # Step 3: Create execution plan
            plan = self._create_execution_plan(selected_tools, analysis)

            self.reasoning_trace.append({
                'step': 'execution_plan',
                'strategy': plan.strategy.value,
                'tool_count': len(plan.tools)
            })

            # Step 4: Execute tools
            context = self._build_execution_context(query, analysis, session_context)
            results = self.execution_engine.execute(plan, query, context)

            # Add execution trace
            self.reasoning_trace.extend(self.execution_engine.get_execution_trace())

            # Step 5: Synthesize response
            response = self._synthesize_response(query, results, analysis)

            # Add reasoning trace to response
            response.reasoning_trace = self.reasoning_trace

            self.logger.info(f"Query processed successfully with {len(results)} tool results")

            return response

        except Exception as e:
            self.logger.error(f"Query processing failed: {e}", exc_info=True)
            return self._error_response(query, str(e))

    def _select_tools(
        self,
        query: str,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Tuple[BaseTool, float]]:
        """
        Select tools using hybrid approach (rules + LLM fallback)

        Args:
            query: User query
            analysis: Query analysis results
            context: Execution context

        Returns:
            List of (tool, confidence) tuples
        """
        complexity = analysis['complexity']
        intent = analysis['intent']
        query_lower = query.lower()

        # Rule-Based Selection (Primary - Fast Path)

        # Priority 1: URL Ingestion (check first - highest priority)
        import re
        has_url = bool(re.search(r'https?://[^\s]+', query))
        ingestion_keywords = ['ingest', 'add', 'load', 'upload', 'import', 'fetch', 'download', 'index', 'process']
        has_ingestion_intent = any(kw in query_lower for kw in ingestion_keywords)

        if has_url and has_ingestion_intent:
            tools = self.tool_registry.get_tools_by_name(['url_ingestion'])
            if tools:
                self.logger.info(f"URL ingestion detected: URL={has_url}, intent={has_ingestion_intent}")
                return tools

        # Intent: Comparison
        if intent == 'comparison' or any(kw in query_lower for kw in ['compare', 'versus', ' vs ', 'difference']):
            tools = self.tool_registry.get_tools_by_name(['comparison', 'semantic_search'])
            if tools:
                return tools

        # Intent: Calculation
        if intent == 'calculation' or any(kw in query_lower for kw in ['calculate', 'compute', '%']):
            tools = self.tool_registry.get_tools_by_name(['calculator', 'semantic_search'])
            if tools:
                return tools

        # Intent: Summarization (needs documents first!)
        if intent == 'summarization' or any(kw in query_lower for kw in ['summarize', 'summary', 'overview']):
            # Get both semantic_search (to retrieve docs) and summarization (to summarize them)
            tools = self.tool_registry.get_tools_by_name(['semantic_search', 'summarization'])
            if tools:
                self.logger.info(f"Summarization query detected - using retrieval + summarization")
                return tools

        # Intent: External (current events, external facts)
        if intent == 'external' or any(kw in query_lower for kw in ['current', 'latest', 'today']):
            # Try internal search first, then web search as fallback
            tools = self.tool_registry.get_tools_by_name(['semantic_search', 'web_search'])
            if tools:
                return tools

        # Simple queries: Use semantic search
        if complexity == 'simple':
            tools = self.tool_registry.get_tools_by_name(['semantic_search'])
            if tools:
                return tools

        # Complex queries: Use multiple tools in parallel
        if complexity == 'complex' or analysis.get('requires_multiple_tools'):
            tools = self.tool_registry.get_tools_by_name(['semantic_search', 'keyword_search'])
            if tools:
                return tools

        # Moderate complexity: Use hybrid search
        if complexity == 'moderate':
            tools = self.tool_registry.get_tools_by_name(['semantic_search', 'keyword_search'])
            if tools:
                return tools

        # Fallback: Use confidence-based selection
        selected = self.tool_registry.get_suitable_tools(
            query,
            context,
            min_confidence=self.min_tool_confidence
        )

        if selected:
            return selected

        # LLM Fallback (for ambiguous queries)
        if self.use_llm_fallback and self.llm_handler:
            return self._llm_tool_selection(query, analysis)

        # Final fallback: semantic search
        tools = self.tool_registry.get_tools_by_name(['semantic_search'])
        return tools if tools else []

    def _llm_tool_selection(
        self,
        query: str,
        analysis: Dict[str, Any]
    ) -> List[Tuple[BaseTool, float]]:
        """
        Use LLM to select tools for ambiguous queries

        Args:
            query: User query
            analysis: Query analysis

        Returns:
            List of (tool, confidence) tuples
        """
        try:
            # Get tool descriptions
            tool_descriptions = []
            for tool in self.tool_registry.tools:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

            tools_text = "\n".join(tool_descriptions)

            # Prompt for LLM
            prompt = f"""Given this query and available tools, select the most appropriate tools to use.

Query: "{query}"

Query Analysis:
- Complexity: {analysis['complexity']}
- Intent: {analysis['intent']}

Available Tools:
{tools_text}

Return a JSON list of tool names in order of preference. Example: ["semantic_search", "calculator"]

Selected tools (JSON only):"""

            # Call LLM with low temperature for deterministic selection
            response = self.llm_handler.generate(
                prompt,
                temperature=0.1,
                max_tokens=100
            )

            # Parse JSON response
            response_text = response.strip()

            # Extract JSON array
            if '[' in response_text and ']' in response_text:
                start = response_text.index('[')
                end = response_text.rindex(']') + 1
                json_text = response_text[start:end]

                tool_names = json.loads(json_text)

                # Get tools by name
                selected = self.tool_registry.get_tools_by_name(tool_names)

                if selected:
                    self.logger.info(f"LLM selected tools: {tool_names}")
                    self.reasoning_trace.append({
                        'step': 'llm_tool_selection',
                        'selected_tools': tool_names
                    })
                    return selected

        except Exception as e:
            self.logger.warning(f"LLM tool selection failed: {e}")

        return []

    def _create_execution_plan(
        self,
        tools: List[Tuple[BaseTool, float]],
        analysis: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create execution plan based on tools and query analysis

        Args:
            tools: Selected tools with confidence scores
            analysis: Query analysis

        Returns:
            ExecutionPlan
        """
        complexity = analysis['complexity']
        intent = analysis['intent']

        # Determine execution strategy

        # Sequential: For multi-step reasoning or when order matters
        if complexity == 'complex' and intent in ['comparison', 'calculation']:
            return ExecutionPlan(
                strategy=ExecutionStrategy.SEQUENTIAL,
                tools=tools
            )

        # Sequential: For summarization (need to retrieve docs first, then summarize)
        # Check both intent AND if summarization tool is present (keyword-based detection)
        tool_names = [t.name for t, _ in tools]
        if intent == 'summarization' or 'summarization' in tool_names:
            return ExecutionPlan(
                strategy=ExecutionStrategy.SEQUENTIAL,
                tools=tools
            )

        # Parallel: For independent queries or hybrid search (factual only)
        if len(tools) > 1 and intent in ['factual']:
            return ExecutionPlan(
                strategy=ExecutionStrategy.PARALLEL,
                tools=tools
            )

        # For external queries: Try KB first, web search as fallback
        if intent == 'external':
            # Always check KB first - it might have the answer
            # Only use web search if KB results are insufficient
            conditions = {}

            if len(tools) > 1 and tools[1][0].name == 'web_search':
                # web_search runs only if KB confidence is low
                # Use max_confidence to check if KB results are insufficient
                conditions['web_search'] = {
                    'max_confidence': 0.5       # Only if KB confidence < 0.5 (low relevance)
                    # Note: min_confidence removed - it would block negative confidence scores
                }

            return ExecutionPlan(
                strategy=ExecutionStrategy.CONDITIONAL,
                tools=tools,
                conditions=conditions
            )

        # Conditional: When fallback is needed (for other multi-tool scenarios)
        if analysis.get('requires_multiple_tools'):
            # Use conditional: Try internal search, then web search if low confidence
            conditions = {}

            if len(tools) > 1:
                # Second tool executes only if first has low confidence or few relevant results
                conditions[tools[1][0].name] = {
                    'min_confidence': 0.0,  # Always allow second tool
                    'max_citations': 3  # Only if first tool has few results
                }

            return ExecutionPlan(
                strategy=ExecutionStrategy.CONDITIONAL,
                tools=tools,
                conditions=conditions
            )

        # Default: Sequential
        return ExecutionPlan(
            strategy=ExecutionStrategy.SEQUENTIAL,
            tools=tools
        )

    def _build_execution_context(
        self,
        query: str,
        analysis: Dict[str, Any],
        session_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build execution context for tools

        Args:
            query: User query
            analysis: Query analysis
            session_context: Session context

        Returns:
            Execution context dictionary
        """
        context = {
            'query': query,
            'complexity': analysis['complexity'],
            'intent': analysis['intent'],
            'entities': analysis.get('entities', []),
            'keywords': analysis.get('keywords', {}),
        }

        # Add session context
        if session_context:
            context.update(session_context)

        # Add retriever and qa_chain for tools that need them
        if self.retriever:
            context['retriever'] = self.retriever

        if self.qa_chain:
            context['qa_chain'] = self.qa_chain

        if self.llm_handler:
            context['llm_handler'] = self.llm_handler

        return context

    def _synthesize_response(
        self,
        query: str,
        results: List[ToolResult],
        analysis: Dict[str, Any]
    ) -> AgenticResponse:
        """
        Synthesize final response from tool results

        Args:
            query: User query
            results: Tool execution results
            analysis: Query analysis

        Returns:
            AgenticResponse
        """
        # Track attempted vs successful tools
        attempted_tools = [r.metadata.get('tool', 'unknown') for r in results]
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if not successful:
            # All tools failed
            error_messages = [r.error for r in results if r.error]
            return AgenticResponse(
                answer=f"I couldn't find an answer to your query. Errors: {'; '.join(error_messages)}",
                sources=[],
                metadata={'all_tools_failed': True, 'attempted_tools': attempted_tools}
            )

        # Merge successful results
        merged = self.execution_engine.merge_results(successful)

        # Extract KB confidence if semantic_search was used
        kb_confidence = 0.0
        for result in successful:
            if result.metadata.get('tool') in ['semantic_search', 'keyword_search']:
                kb_confidence = result.metadata.get('confidence', 0.0)
                break

        # Add KB confidence to merged metadata
        if kb_confidence != 0.0:
            merged.metadata['kb_confidence'] = kb_confidence

        # Extract answer with context about failed tools
        answer = self._extract_answer(merged, query, analysis, failed_tools=failed)

        # Get citations
        citations = merged.citations

        # Build metadata
        metadata = {
            'tools_used': merged.metadata.get('tools_used', []),
            'attempted_tools': attempted_tools,
            'failed_tools': [r.metadata.get('tool') for r in failed],
            'result_count': len(successful),
            'complexity': analysis['complexity'],
            'intent': analysis['intent'],
            'kb_confidence': kb_confidence if kb_confidence != 0.0 else None
        }

        return AgenticResponse(
            answer=answer,
            sources=citations,
            metadata=metadata
        )

    def _extract_answer(
        self,
        result: ToolResult,
        query: str,
        analysis: Dict[str, Any],
        failed_tools: List[ToolResult] = None
    ) -> str:
        """
        Extract answer from tool result

        Args:
            result: Merged tool result
            query: User query
            analysis: Query analysis
            failed_tools: List of failed tool results (optional)

        Returns:
            Answer string
        """
        # Check if web_search failed for external query
        web_search_failed = False
        # Check for failed web search and get helpful message
        web_search_help_msg = None
        if failed_tools:
            for failed in failed_tools:
                if failed.metadata.get('tool') == 'web_search':
                    web_search_failed = True
                    # Get the helpful message from the tool
                    web_search_help_msg = failed.metadata.get('message', failed.error)
                    break

        # If data has 'answer' key, use it
        if isinstance(result.data, dict):
            if 'answer' in result.data:
                answer = result.data['answer']

                # Note: Web search error messages are already shown in reasoning trace
                # No need to duplicate them in the answer

                return answer

            # If multiple answers, concatenate them
            if 'answers' in result.data:
                answers = result.data['answers']

                # Check which tools contributed
                tools_used = result.metadata.get('tools_used', [])
                has_kb = 'semantic_search' in tools_used or 'keyword_search' in tools_used
                has_web = 'web_search' in tools_used

                # Add source attribution context
                if has_web and has_kb:
                    # Both internal and external sources used
                    kb_confidence = result.metadata.get('kb_confidence', 0.0)

                    # Check if KB had relevant results (confidence > 0.3)
                    if kb_confidence > 0.3:
                        header = "**Answer synthesized from internal documents and external sources:**\n\n"
                    else:
                        header = "**Answer from external sources** (internal documents had low relevance):\n\n"

                    combined = header + "\n\n".join(answers)
                elif has_web:
                    # Only external sources
                    combined = "**Answer from external sources:**\n\n" + "\n\n".join(answers)
                else:
                    # Only internal sources
                    combined = "\n\n".join(answers)

                # Note: Web search error messages are already shown in reasoning trace

                return combined

        # If we have data or citations but no answer, generate one using QA chain
        if (result.data or result.citations) and self.qa_chain:
            try:
                # Use result.data if available (contains full document content)
                # Otherwise fall back to building from citations
                if result.data:
                    # result.data already contains the full retrieved documents
                    context_documents = result.data if isinstance(result.data, list) else [result.data]
                else:
                    # Fallback: Convert citations to context documents
                    context_documents = []
                    for citation in result.citations:
                        context_documents.append({
                            'content': citation.content,
                            'metadata': citation.metadata or {}
                        })

                # Use QA chain to generate answer from retrieved documents
                # Pass empty conversation history for now
                response = self.qa_chain.process_query(query, context_documents, [])
                if response and response.get('answer'):
                    answer = response['answer']

                    # Note: Web search error messages are already shown in reasoning trace

                    return answer

            except Exception as e:
                self.logger.warning(f"Failed to generate answer from documents: {e}")

        # If no data and no citations, return message
        if not result.data and not result.citations:
            return "No answer available."

        # Otherwise, convert data to string
        if result.data:
            return str(result.data)

        return "No answer available."

    def _handle_conversational(self, query: str) -> AgenticResponse:
        """Handle conversational queries (greetings, acknowledgments, farewells)"""
        query_lower = query.lower().strip()

        # Map queries to responses
        if any(word in query_lower for word in ['hi', 'hello', 'hey']):
            answer = "Hello! I'm Cortex. How can I help you today? You can ask me questions about your documents."
        elif any(word in query_lower for word in ['thanks', 'thank you']):
            answer = "You're welcome! Feel free to ask if you need anything else."
        elif any(word in query_lower for word in ['bye', 'goodbye']):
            answer = "Goodbye! Come back anytime you need help with your documents."
        elif any(word in query_lower for word in ['ok', 'okay', 'got it', 'understood', 'sure']):
            answer = "Great! Let me know if you have any questions."
        else:
            answer = "I'm here to help! You can ask me about your documents or tell me your preferences."

        self.reasoning_trace.append({
            'step': 'conversational_response',
            'type': 'greeting/acknowledgment',
            'no_tools_used': True
        })

        return AgenticResponse(
            answer=answer,
            sources=[],
            metadata={'intent': 'conversational', 'response_time_ms': 0}
        )

    def _fallback_response(self, query: str, reason: str) -> AgenticResponse:
        """Create fallback response when no tools available"""
        return AgenticResponse(
            answer=f"I apologize, but I cannot process this query. Reason: {reason}",
            sources=[],
            metadata={'fallback': True, 'reason': reason}
        )

    def _error_response(self, query: str, error: str) -> AgenticResponse:
        """Create error response"""
        return AgenticResponse(
            answer=f"An error occurred while processing your query: {error}",
            sources=[],
            metadata={'error': True, 'error_message': error}
        )
