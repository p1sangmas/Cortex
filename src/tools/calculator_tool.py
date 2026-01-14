"""
Calculator Tool - Safe mathematical expression evaluation

This tool handles mathematical queries and can extract numbers from
document context for calculations.
"""

import logging
import re
import ast
import operator
from typing import Dict, Any, List, Optional, Tuple
from src.tools import BaseTool, ToolResult, EnhancedCitation

logger = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations"""

    name = "calculator"
    description = "Perform mathematical calculations (e.g., 'Calculate 15% of 1000', 'What's the sum of X and Y?')"

    # Safe operators for calculation
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
    }

    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if this is a calculation query

        Args:
            query: User query
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        query_lower = query.lower()

        # Very high confidence keywords
        high_confidence_keywords = [
            'calculate', 'computation', 'compute',
            'what is', 'what\'s', "what's"
        ]

        # Mathematical operations
        math_operations = [
            'sum', 'total', 'add', 'subtract', 'multiply',
            'divide', 'percentage', 'percent', '%',
            'average', 'mean', 'difference'
        ]

        # Check for high confidence calculation keywords
        for keyword in high_confidence_keywords:
            if keyword in query_lower:
                # Check if there are numbers in the query
                if re.search(r'\d+', query):
                    return 0.95

        # Check for math operations with numbers
        for operation in math_operations:
            if operation in query_lower and re.search(r'\d+', query):
                return 0.85

        # Check for mathematical operators
        if any(op in query for op in ['+', '-', '*', '/', '^', '%']):
            if re.search(r'\d+', query):
                return 0.9

        # Check for number-heavy queries
        numbers = re.findall(r'\d+\.?\d*', query)
        if len(numbers) >= 2:
            return 0.7

        return 0.2

    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute calculation

        Args:
            query: User query
            context: May contain:
                - 'retriever': For extracting numbers from documents
                - 'context_documents': Pre-retrieved documents

        Returns:
            ToolResult with calculation result
        """
        try:
            # Try to extract and evaluate mathematical expression
            result, expression = self._evaluate_query(query)

            if result is not None:
                # Direct calculation successful
                answer = self._format_answer(query, expression, result)

                logger.info(f"Calculation: {expression} = {result}")

                return ToolResult(
                    success=True,
                    data={
                        'answer': answer,
                        'expression': expression,
                        'result': result,
                        'query_type': 'calculation'
                    },
                    metadata={
                        'tool': self.name,
                        'query': query,
                        'calculation': f"{expression} = {result}"
                    },
                    citations=[]
                )

            # If direct calculation failed, try to extract numbers from documents
            retriever = context.get('retriever')
            context_documents = context.get('context_documents', [])

            if not context_documents and retriever:
                # Retrieve documents related to the query
                context_documents = retriever.retrieve(query, 3)

            if context_documents:
                # Try to extract numbers and calculate
                result, expression, citations = self._calculate_from_documents(
                    query, context_documents
                )

                if result is not None:
                    answer = self._format_answer(query, expression, result)

                    return ToolResult(
                        success=True,
                        data={
                            'answer': answer,
                            'expression': expression,
                            'result': result,
                            'query_type': 'calculation'
                        },
                        metadata={
                            'tool': self.name,
                            'query': query,
                            'calculation': f"{expression} = {result}",
                            'source': 'documents'
                        },
                        citations=citations
                    )

            # Could not perform calculation
            return ToolResult(
                success=False,
                error="Could not extract numbers or evaluate expression",
                metadata={'tool': self.name}
            )

        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={'tool': self.name}
            )

    def _evaluate_query(self, query: str) -> Tuple[Optional[float], str]:
        """
        Try to extract and evaluate a mathematical expression from query

        Args:
            query: User query

        Returns:
            (result, expression) or (None, "") if failed
        """
        # Try to find percentage calculations
        percentage_match = re.search(
            r'(\d+\.?\d*)\s*%\s*(?:of|from)?\s*(\d+\.?\d*)',
            query,
            re.IGNORECASE
        )
        if percentage_match:
            percent = float(percentage_match.group(1))
            value = float(percentage_match.group(2))
            result = (percent / 100) * value
            expression = f"{percent}% of {value}"
            return result, expression

        # Try to find basic arithmetic expressions
        # Pattern: number operator number
        arithmetic_match = re.search(
            r'(\d+\.?\d*)\s*([\+\-\*\/])\s*(\d+\.?\d*)',
            query
        )
        if arithmetic_match:
            try:
                num1 = float(arithmetic_match.group(1))
                op = arithmetic_match.group(2)
                num2 = float(arithmetic_match.group(3))

                if op == '+':
                    result = num1 + num2
                elif op == '-':
                    result = num1 - num2
                elif op == '*':
                    result = num1 * num2
                elif op == '/':
                    result = num1 / num2 if num2 != 0 else None

                if result is not None:
                    expression = f"{num1} {op} {num2}"
                    return result, expression
            except:
                pass

        # Try to evaluate simple mathematical expressions using AST
        # Extract potential expression
        expr_match = re.search(r'[\d\s\+\-\*\/\(\)\.]+', query)
        if expr_match:
            expr_str = expr_match.group(0).strip()
            try:
                result = self._safe_eval(expr_str)
                if result is not None:
                    return result, expr_str
            except:
                pass

        return None, ""

    def _safe_eval(self, expr: str) -> Optional[float]:
        """
        Safely evaluate a mathematical expression using AST

        Args:
            expr: Expression string (e.g., "2 + 3 * 4")

        Returns:
            Result or None if invalid
        """
        try:
            # Parse expression into AST
            node = ast.parse(expr, mode='eval').body

            # Evaluate the AST
            return self._eval_node(node)
        except:
            return None

    def _eval_node(self, node) -> float:
        """
        Recursively evaluate AST node

        Args:
            node: AST node

        Returns:
            Evaluated value
        """
        if isinstance(node, ast.Num):
            # Number literal
            return node.n
        elif isinstance(node, ast.BinOp):
            # Binary operation
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type in self.OPERATORS:
                return self.OPERATORS[op_type](left, right)
            else:
                raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            # Unary operation (e.g., -5)
            operand = self._eval_node(node.operand)
            op_type = type(node.op)

            if op_type in self.OPERATORS:
                return self.OPERATORS[op_type](operand)
            else:
                raise ValueError(f"Unsupported operator: {op_type}")
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

    def _calculate_from_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> Tuple[Optional[float], str, List[EnhancedCitation]]:
        """
        Extract numbers from documents and perform calculation

        Args:
            query: User query
            documents: Retrieved documents

        Returns:
            (result, expression, citations)
        """
        # Extract all numbers from documents
        all_numbers = []
        citations = []

        for idx, doc in enumerate(documents):
            content = doc.get('content', '')
            numbers = re.findall(r'\d+\.?\d*', content)

            if numbers:
                metadata = doc.get('metadata', {})
                doc_name = (
                    metadata.get('title') or
                    metadata.get('original_filename') or
                    doc.get('id', f'document_{idx}')
                )

                all_numbers.extend([float(n) for n in numbers[:5]])  # Limit per doc

                # Create citation
                citation = EnhancedCitation(
                    document=doc_name,
                    page_number=metadata.get('page_number', metadata.get('page', 0)),
                    content=content[:200],
                    rank_position=idx + 1,
                    metadata=metadata
                )
                citations.append(citation)

        if len(all_numbers) >= 2:
            # Try to infer operation from query
            query_lower = query.lower()

            if any(kw in query_lower for kw in ['sum', 'total', 'add', 'plus']):
                result = sum(all_numbers)
                expression = f"sum({', '.join(map(str, all_numbers))})"
                return result, expression, citations

            elif 'average' in query_lower or 'mean' in query_lower:
                result = sum(all_numbers) / len(all_numbers)
                expression = f"average({', '.join(map(str, all_numbers))})"
                return result, expression, citations

            elif 'difference' in query_lower or 'subtract' in query_lower:
                result = all_numbers[0] - all_numbers[1]
                expression = f"{all_numbers[0]} - {all_numbers[1]}"
                return result, expression, citations[:2]

        return None, "", []

    def _format_answer(self, query: str, expression: str, result: float) -> str:
        """
        Format the calculation answer

        Args:
            query: Original query
            expression: Mathematical expression
            result: Calculation result

        Returns:
            Formatted answer string
        """
        # Round to 2 decimal places for display
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.2f}"

        return f"The result of {expression} is {result_str}."
