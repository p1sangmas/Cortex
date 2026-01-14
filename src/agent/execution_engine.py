"""
Execution Engine - Executes tools with different strategies

This component handles tool execution with three strategies:
- Sequential: Tool outputs feed into next tools
- Parallel: Multiple tools run simultaneously, results merged
- Conditional: Tools execute based on conditions
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.tools import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Tool execution strategies"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class ExecutionPlan:
    """Represents a plan for executing tools"""

    def __init__(
        self,
        strategy: ExecutionStrategy,
        tools: List[Tuple[BaseTool, float]],  # (tool, confidence)
        conditions: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize execution plan

        Args:
            strategy: Execution strategy
            tools: List of (tool, confidence) tuples
            conditions: Conditions for conditional execution
        """
        self.strategy = strategy
        self.tools = tools
        self.conditions = conditions or {}


class ExecutionEngine:
    """Executes tools according to different strategies"""

    def __init__(self, max_parallel_workers: int = 3):
        """
        Initialize execution engine

        Args:
            max_parallel_workers: Max threads for parallel execution
        """
        self.logger = logging.getLogger(f"{__name__}.ExecutionEngine")
        self.max_parallel_workers = max_parallel_workers
        self.execution_trace = []

    def execute(
        self,
        plan: ExecutionPlan,
        query: str,
        context: Dict[str, Any]
    ) -> List[ToolResult]:
        """
        Execute tools according to plan

        Args:
            plan: Execution plan
            query: User query
            context: Execution context

        Returns:
            List of ToolResult objects
        """
        self.logger.info(
            f"Executing {len(plan.tools)} tools with {plan.strategy.value} strategy"
        )

        # Clear trace for this execution
        self.execution_trace = []

        if plan.strategy == ExecutionStrategy.SEQUENTIAL:
            return self._execute_sequential(plan, query, context)
        elif plan.strategy == ExecutionStrategy.PARALLEL:
            return self._execute_parallel(plan, query, context)
        elif plan.strategy == ExecutionStrategy.CONDITIONAL:
            return self._execute_conditional(plan, query, context)
        else:
            raise ValueError(f"Unknown strategy: {plan.strategy}")

    def _execute_sequential(
        self,
        plan: ExecutionPlan,
        query: str,
        context: Dict[str, Any]
    ) -> List[ToolResult]:
        """
        Execute tools sequentially (Tool A output → Tool B input)

        Args:
            plan: Execution plan
            query: User query
            context: Execution context

        Returns:
            List of ToolResult objects
        """
        results = []
        current_context = context.copy()

        for tool, confidence in plan.tools:
            self.logger.info(f"Executing tool: {tool.name} (confidence: {confidence:.2f})")

            # Log execution step
            self.execution_trace.append({
                'step': 'execute_tool',
                'tool': tool.name,
                'confidence': confidence,
                'strategy': 'sequential'
            })

            try:
                # Execute tool with current context
                result = tool.execute(query, current_context)
                results.append(result)

                # Update context with result for next tool
                if result.success:
                    current_context['previous_result'] = result.data
                    current_context['previous_citations'] = result.citations

                    self.execution_trace.append({
                        'step': 'tool_success',
                        'tool': tool.name,
                        'citations_count': len(result.citations)
                    })
                else:
                    self.logger.warning(f"Tool {tool.name} failed: {result.error}")
                    self.execution_trace.append({
                        'step': 'tool_failure',
                        'tool': tool.name,
                        'error': result.error
                    })

            except Exception as e:
                self.logger.error(f"Tool {tool.name} execution error: {e}")
                results.append(ToolResult(
                    success=False,
                    error=str(e),
                    metadata={'tool': tool.name}
                ))

                self.execution_trace.append({
                    'step': 'tool_error',
                    'tool': tool.name,
                    'error': str(e)
                })

        return results

    def _execute_parallel(
        self,
        plan: ExecutionPlan,
        query: str,
        context: Dict[str, Any]
    ) -> List[ToolResult]:
        """
        Execute tools in parallel and merge results

        Args:
            plan: Execution plan
            query: User query
            context: Execution context

        Returns:
            List of ToolResult objects (merged)
        """
        results = []

        self.logger.info(f"Executing {len(plan.tools)} tools in parallel")

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_parallel_workers) as executor:
            # Submit all tool executions
            future_to_tool = {}

            for tool, confidence in plan.tools:
                self.logger.info(f"Submitting tool: {tool.name} (confidence: {confidence:.2f})")

                self.execution_trace.append({
                    'step': 'submit_tool',
                    'tool': tool.name,
                    'confidence': confidence,
                    'strategy': 'parallel'
                })

                future = executor.submit(tool.execute, query, context)
                future_to_tool[future] = (tool, confidence)

            # Collect results as they complete
            for future in as_completed(future_to_tool):
                tool, confidence = future_to_tool[future]

                try:
                    result = future.result()
                    results.append(result)

                    if result.success:
                        self.execution_trace.append({
                            'step': 'tool_complete',
                            'tool': tool.name,
                            'citations_count': len(result.citations)
                        })
                    else:
                        self.logger.warning(f"Tool {tool.name} failed: {result.error}")
                        self.execution_trace.append({
                            'step': 'tool_failure',
                            'tool': tool.name,
                            'error': result.error
                        })

                except Exception as e:
                    self.logger.error(f"Tool {tool.name} execution error: {e}")
                    results.append(ToolResult(
                        success=False,
                        error=str(e),
                        metadata={'tool': tool.name}
                    ))

                    self.execution_trace.append({
                        'step': 'tool_error',
                        'tool': tool.name,
                        'error': str(e)
                    })

        return results

    def _execute_conditional(
        self,
        plan: ExecutionPlan,
        query: str,
        context: Dict[str, Any]
    ) -> List[ToolResult]:
        """
        Execute tools conditionally based on previous results

        Args:
            plan: Execution plan with conditions
            query: User query
            context: Execution context

        Returns:
            List of ToolResult objects
        """
        results = []
        current_context = context.copy()

        for tool, confidence in plan.tools:
            # Check if tool should execute based on conditions
            should_execute = self._check_conditions(
                tool,
                plan.conditions,
                results,
                current_context
            )

            if not should_execute:
                # Get skip reason from context
                skip_reason = current_context.get('skip_reason', 'condition_not_met')
                self.logger.info(f"Skipping tool {tool.name} ({skip_reason})")
                self.execution_trace.append({
                    'step': 'skip_tool',
                    'tool': tool.name,
                    'reason': skip_reason
                })
                continue

            self.logger.info(f"Executing tool: {tool.name} (confidence: {confidence:.2f})")

            self.execution_trace.append({
                'step': 'execute_tool',
                'tool': tool.name,
                'confidence': confidence,
                'strategy': 'conditional'
            })

            try:
                result = tool.execute(query, current_context)
                results.append(result)

                # Update context
                if result.success:
                    current_context['previous_result'] = result.data
                    current_context['previous_citations'] = result.citations

                    self.execution_trace.append({
                        'step': 'tool_success',
                        'tool': tool.name,
                        'citations_count': len(result.citations)
                    })
                else:
                    self.execution_trace.append({
                        'step': 'tool_failure',
                        'tool': tool.name,
                        'error': result.error
                    })

            except Exception as e:
                self.logger.error(f"Tool {tool.name} execution error: {e}")
                results.append(ToolResult(
                    success=False,
                    error=str(e),
                    metadata={'tool': tool.name}
                ))

                self.execution_trace.append({
                    'step': 'tool_error',
                    'tool': tool.name,
                    'error': str(e)
                })

        return results

    def _check_conditions(
        self,
        tool: BaseTool,
        conditions: Dict[str, Any],
        previous_results: List[ToolResult],
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if conditions are met for tool execution

        Args:
            tool: Tool to check
            conditions: Condition definitions
            previous_results: Results from previous tools
            context: Execution context

        Returns:
            True if tool should execute
        """
        # Get conditions for this tool
        tool_conditions = conditions.get(tool.name, {})

        self.logger.info(f"Checking conditions for {tool.name}: {tool_conditions}, prev_results: {len(previous_results)}")

        if not tool_conditions:
            # No conditions = always execute
            self.logger.info(f"No conditions for {tool.name}, executing")
            return True

        # Check "requires" condition (requires previous tool success)
        requires = tool_conditions.get('requires')
        if requires:
            # Find result from required tool
            required_result = None
            for result in previous_results:
                if result.metadata.get('tool') == requires:
                    required_result = result
                    break

            if not required_result or not required_result.success:
                return False

        # Check "min_confidence" condition
        # Tool only runs if previous result confidence >= min_confidence
        min_confidence = tool_conditions.get('min_confidence')
        if min_confidence is not None:
            if previous_results:
                last_result = previous_results[-1]
                result_confidence = last_result.metadata.get('confidence', 1.0)

                if result_confidence < min_confidence:
                    return False

        # Check "max_confidence" condition
        # Tool only runs if previous result confidence < max_confidence (i.e., low confidence)
        max_confidence = tool_conditions.get('max_confidence')
        if max_confidence is not None:
            self.logger.info(f"Checking max_confidence condition: {max_confidence}, has prev_results: {len(previous_results) > 0}")
            if previous_results:
                last_result = previous_results[-1]
                result_confidence = last_result.metadata.get('confidence', 1.0)
                self.logger.info(f"KB confidence: {result_confidence:.3f}, threshold: {max_confidence}, should_skip: {result_confidence >= max_confidence}")

                # Skip tool if previous result had HIGH confidence
                if result_confidence >= max_confidence:
                    context['skip_reason'] = f'confidence {result_confidence:.3f} >= {max_confidence}'
                    self.logger.info(f"Skipping {tool.name}: KB confidence {result_confidence:.3f} >= threshold {max_confidence}")
                    return False
                else:
                    self.logger.info(f"Executing {tool.name}: KB confidence {result_confidence:.3f} < threshold {max_confidence}")

        # Check "max_citations" condition (execute only if previous results have few citations)
        max_citations = tool_conditions.get('max_citations')
        if max_citations is not None:
            if previous_results:
                last_result = previous_results[-1]
                num_citations = len(last_result.citations)
                if num_citations >= max_citations:
                    context['skip_reason'] = f'citations {num_citations} >= {max_citations}'
                    self.logger.info(f"Skipping {tool.name}: KB has {num_citations} citations >= threshold {max_citations}")
                    return False

        # Check "context_key" condition
        context_key = tool_conditions.get('context_key')
        if context_key:
            if context_key not in context:
                return False

        return True

    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """
        Get execution trace for transparency

        Returns:
            List of execution steps
        """
        return self.execution_trace.copy()

    def merge_results(self, results: List[ToolResult]) -> ToolResult:
        """
        Merge multiple tool results into one

        Args:
            results: List of ToolResult objects

        Returns:
            Merged ToolResult
        """
        if not results:
            return ToolResult(
                success=False,
                error="No results to merge"
            )

        # Filter successful results
        successful_results = [r for r in results if r.success]

        if not successful_results:
            # All failed - return first error
            return results[0]

        # Merge data
        merged_data = {}
        all_citations = []
        merged_metadata = {
            'tools_used': [],
            'merge_count': len(successful_results)
        }

        for result in successful_results:
            # Merge data dictionaries (combine instead of overwrite)
            if isinstance(result.data, dict):
                for key, value in result.data.items():
                    if key == 'answer':
                        # Collect multiple answers
                        if 'answers' not in merged_data:
                            merged_data['answers'] = []
                        merged_data['answers'].append(value)
                    elif key in merged_data:
                        # For other keys, keep as list if multiple values
                        if not isinstance(merged_data[key], list):
                            merged_data[key] = [merged_data[key]]
                        merged_data[key].append(value)
                    else:
                        merged_data[key] = value

            # Collect all citations
            all_citations.extend(result.citations)

            # Track tools used
            tool_name = result.metadata.get('tool', 'unknown')
            merged_metadata['tools_used'].append(tool_name)

        # Remove duplicate citations (same document + page)
        unique_citations = []
        seen = set()

        for citation in all_citations:
            key = (citation.document, citation.page_number)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)

        # Sort by confidence (highest first)
        unique_citations.sort(
            key=lambda c: c.confidence_score,
            reverse=True
        )

        return ToolResult(
            success=True,
            data=merged_data,
            metadata=merged_metadata,
            citations=unique_citations
        )
