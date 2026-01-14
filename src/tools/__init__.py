"""
Tool Base Classes for Agentic RAG System

This module defines the base classes and data structures for the tool-based
agentic architecture. All tools inherit from BaseTool and return ToolResult objects.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class EnhancedCitation:
    """Enhanced citation with page numbers, excerpts, and confidence scores"""
    document: str  # Document name/title
    page_number: int = 0  # Page number (0 if not available)
    excerpt: str = ""  # Text excerpt (50-200 chars)
    confidence_score: float = 0.0  # Composite confidence (0-1)

    # Component scores
    similarity_score: float = 0.0  # Semantic similarity
    cross_encoder_score: float = 0.0  # Cross-encoder reranking score
    rank_position: int = 0  # Position in results (1-indexed)

    # Raw data
    content: str = ""  # Full chunk content
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'document': self.document,
            'page_number': self.page_number,
            'excerpt': self.excerpt,
            'confidence_score': round(self.confidence_score, 3),
            'similarity_score': round(self.similarity_score, 3),
            'cross_encoder_score': round(self.cross_encoder_score, 3),
            'rank_position': self.rank_position,
            'metadata': self.metadata
        }


@dataclass
class ToolResult:
    """Standard result format from all tools"""
    success: bool  # Whether tool execution succeeded
    data: Any = None  # Main result data
    error: Optional[str] = None  # Error message if failed
    metadata: Dict[str, Any] = field(default_factory=dict)  # Execution metadata
    citations: List[EnhancedCitation] = field(default_factory=list)  # Source citations

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'citations': [c.to_dict() for c in self.citations]
        }


class BaseTool(ABC):
    """Abstract base class for all tools"""

    # Subclasses must define these
    name: str = "base_tool"
    description: str = "Base tool class"

    def __init__(self):
        """Initialize tool"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if this tool can handle the query

        Args:
            query: User query string
            context: Additional context (conversation history, etc.)

        Returns:
            Confidence score (0.0 to 1.0) that this tool can handle the query
            - 0.0: Cannot handle at all
            - 0.5: Might be useful
            - 1.0: Perfect match
        """
        pass

    @abstractmethod
    def execute(self, query: str, context: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with the given query

        Args:
            query: User query string
            context: Additional context including:
                - retriever: HybridRetriever instance
                - qa_chain: AdaptiveQAChain instance
                - conversation_history: List of previous messages
                - session_id: Session identifier

        Returns:
            ToolResult with success status, data, and citations
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        """Initialize empty tool registry"""
        self.tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger(f"{__name__}.ToolRegistry")

    def register(self, tool: BaseTool) -> None:
        """
        Register a new tool

        Args:
            tool: Tool instance to register
        """
        if tool.name in self.tools:
            self.logger.warning(f"Tool '{tool.name}' already registered, overwriting")

        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def get_all(self) -> List[BaseTool]:
        """
        Get all registered tools

        Returns:
            List of all tool instances
        """
        return list(self.tools.values())

    def get_suitable_tools(
        self,
        query: str,
        context: Dict[str, Any],
        min_confidence: float = 0.3
    ) -> List[tuple[BaseTool, float]]:
        """
        Get tools suitable for handling the query

        Args:
            query: User query
            context: Additional context
            min_confidence: Minimum confidence threshold

        Returns:
            List of (tool, confidence) tuples, sorted by confidence (descending)
        """
        suitable_tools = []

        for tool in self.tools.values():
            try:
                confidence = tool.can_handle(query, context)
                if confidence >= min_confidence:
                    suitable_tools.append((tool, confidence))
            except Exception as e:
                self.logger.error(f"Error checking {tool.name}: {e}")

        # Sort by confidence (descending)
        suitable_tools.sort(key=lambda x: x[1], reverse=True)

        return suitable_tools

    def get_tools_by_name(
        self,
        tool_names: List[str],
        default_confidence: float = 0.8
    ) -> List[tuple[BaseTool, float]]:
        """
        Get tools by their names

        Args:
            tool_names: List of tool names to retrieve
            default_confidence: Default confidence for retrieved tools

        Returns:
            List of (tool, confidence) tuples
        """
        tools = []

        for name in tool_names:
            tool = self.tools.get(name)
            if tool:
                tools.append((tool, default_confidence))
            else:
                self.logger.warning(f"Tool '{name}' not found in registry")

        return tools

    def get_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all tools

        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {name: tool.description for name, tool in self.tools.items()}

    def __len__(self) -> int:
        return len(self.tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={list(self.tools.keys())})"


# Export main classes
__all__ = [
    'BaseTool',
    'ToolResult',
    'EnhancedCitation',
    'ToolRegistry'
]
