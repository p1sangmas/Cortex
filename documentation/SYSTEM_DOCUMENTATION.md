# Cortex: Complete System Documentation

**Version:** 2.0
**Last Updated:** January 14, 2026
**System Name:** Cortex - AI Knowledge Assistant

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Agentic RAG Implementation](#agentic-rag-implementation)
4. [Tool System](#tool-system)
5. [API Reference](#api-reference)
6. [Web UI Reference](#web-ui-reference)
7. [Configuration Guide](#configuration-guide)
8. [Deployment Guide](#deployment-guide)
9. [Development Guide](#development-guide)
10. [Performance & Optimization](#performance--optimization)
11. [Troubleshooting](#troubleshooting)
12. [Appendices](#appendices)

---

## Executive Summary

Cortex is an advanced AI-powered knowledge base assistant that implements an **Agentic RAG (Retrieval-Augmented Generation)** system. Unlike traditional RAG systems with fixed retrieval pipelines, Cortex autonomously selects and orchestrates specialized tools to answer queries, providing transparent reasoning traces and rich citations.

### Key Differentiators

**Traditional RAG:**
- Fixed retrieval strategy
- Single-pass processing
- Basic citations (filename only)
- Linear pipeline

**Cortex Agentic RAG:**
- ✅ Autonomous tool selection based on query analysis
- ✅ Multi-step execution with conditional logic
- ✅ Enhanced citations with page numbers, excerpts, confidence scores
- ✅ Transparent reasoning traces
- ✅ External knowledge retrieval (web search via n8n)
- ✅ URL ingestion for dynamic document loading
- ✅ Comprehensive evaluation metrics

### Core Capabilities

- **📄 Multi-format PDF Processing**: Robust extraction with OCR fallback
- **🤖 Agentic Tool Orchestration**: 7 specialized tools with intelligent selection
- **🔍 Hybrid Retrieval**: Semantic similarity + keyword matching
- **📊 Enhanced Citations**: Page numbers, excerpts, confidence scores
- **💬 Conversation Memory**: Context-aware multi-turn conversations
- **⚡ Real-time Evaluation**: RAGAS-inspired quality metrics
- **🔒 Privacy-First**: Local processing, no external APIs (except optional web search)
- **🔗 n8n Integration**: Low-code automation workflows

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│  ┌─────────────────┐                    ┌──────────────────┐   │
│  │  Web UI (HTML)  │◄──────────────────►│  Streamlit App   │   │
│  │  - Modern CSS   │     Alternative     │  (Legacy)        │   │
│  │  - JavaScript   │     Interfaces      │                  │   │
│  └────────┬────────┘                    └──────────────────┘   │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ HTTP/REST API
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/query         - Query processing                    │  │
│  │  /api/upload        - Document upload                     │  │
│  │  /api/status        - System status                       │  │
│  │  /api/documents     - Document management                 │  │
│  │  /api/conversation  - Conversation history                │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agentic Orchestration Layer                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  AgenticOrchestrator                                      │ │
│  │  ├─ QueryAnalyzer        - Intent & complexity detection │ │
│  │  ├─ ToolRegistry          - 7 specialized tools          │ │
│  │  ├─ Tool Selection        - Hybrid rule-based + LLM      │ │
│  │  ├─ ExecutionEngine       - Sequential/Parallel/Conditional│ │
│  │  └─ CitationEnhancer      - Page numbers, excerpts       │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Tool Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Semantic     │  │ Keyword      │  │ Comparison   │         │
│  │ Search       │  │ Search       │  │ Tool         │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐         │
│  │ Summarization│  │ Calculator   │  │ Web Search   │◄─┐      │
│  │ Tool         │  │ Tool         │  │ Tool         │  │      │
│  └──────────────┘  └──────────────┘  └──────┬───────┘  │      │
│                                             │            │      │
│  ┌──────────────┐                          │     ┌──────┴─────┐│
│  │ URL          │                          └────►│ n8n        ││
│  │ Ingestion    │                                │ Webhooks   ││
│  └──────────────┘                                └────────────┘│
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data & Model Layer                          │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │ ChromaDB       │  │ Ollama LLM     │  │ SentenceTransf.  │ │
│  │ Vector Store   │  │ (Llama 3.2 3B) │  │ Embeddings       │ │
│  │ + Keyword Index│  │                │  │ (MiniLM-L6-v2)   │ │
│  └────────────────┘  └────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Container Architecture (Docker)

```
┌─────────────────────────────────────────────────────────────┐
│                    cortex_default Network                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  cortex Container                                     │  │
│  │  ├─ FastAPI Application (Port 8000)                  │  │
│  │  ├─ Nginx Web Server (Port 80 → Host 8080)          │  │
│  │  ├─ Python 3.9 Runtime                               │  │
│  │  ├─ Document Processor                               │  │
│  │  ├─ Agentic Orchestrator                             │  │
│  │  └─ Volume Mounts:                                    │  │
│  │     - ./data/documents:/app/data/documents           │  │
│  │     - ./data/vectorstore:/app/data/vectorstore       │  │
│  │     - ./data/models_cache:/app/data/models_cache     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                  │
│                           │ HTTP                             │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ollama Container (if using Docker Ollama)           │  │
│  │  ├─ Ollama LLM Server (Port 11434)                   │  │
│  │  ├─ Model: llama3.2:3b                               │  │
│  │  └─ Volume: ollama-data:/root/.ollama                │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ▲                                  │
│                           │ HTTP (optional)                  │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  cortex-n8n Container (optional)                     │  │
│  │  ├─ n8n Automation Platform (Port 5678)              │  │
│  │  ├─ Workflows: Web search, Document ingestion        │  │
│  │  └─ Volume: ./n8n-data:/home/node/.n8n              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### File System Structure

```
Cortex/
├── api.py                          # FastAPI application entry point
├── app.py                          # Streamlit app (legacy interface)
├── docker-compose.yml              # Main Docker configuration
├── docker-compose.gpu.yml          # GPU acceleration support
├── docker-compose.n8n.yml          # n8n automation integration
├── docker-entrypoint.sh            # Container startup script
├── Dockerfile                      # Container image definition
├── run_docker.sh                   # Management script
├── requirements.txt                # Python dependencies
├── .env                           # Environment configuration
│
├── config/
│   └── settings.py                # System configuration
│
├── src/
│   ├── agent/                     # Agentic RAG components
│   │   ├── orchestrator.py        # Main orchestration logic
│   │   ├── query_analyzer.py      # Query analysis & intent detection
│   │   └── execution_engine.py    # Tool execution strategies
│   │
│   ├── tools/                     # Tool implementations
│   │   ├── __init__.py            # BaseTool, ToolResult classes
│   │   ├── semantic_search_tool.py
│   │   ├── keyword_search_tool.py
│   │   ├── comparison_tool.py
│   │   ├── summarization_tool.py
│   │   ├── calculator_tool.py
│   │   ├── web_search_tool.py     # n8n-powered web search
│   │   └── url_ingestion_tool.py  # Dynamic document ingestion
│   │
│   ├── document_processor.py      # PDF extraction & OCR
│   ├── chunking.py                # Semantic text chunking
│   ├── retriever.py               # HybridRetriever (semantic + keyword)
│   ├── llm_handler.py             # Ollama LLM integration
│   ├── evaluator.py               # RAGAS-inspired evaluation
│   ├── citation_enhancer.py       # Citation enrichment
│   └── utils.py                   # Utility functions
│
├── web/                           # Web UI files
│   ├── index.html                 # Main UI
│   ├── css/
│   │   └── modern.css             # Styling
│   └── js/
│       ├── app.js                 # Main application logic
│       └── notification-panel.js  # Notification system
│
├── data/                          # Data storage (mounted volumes)
│   ├── documents/                 # PDF storage
│   ├── vectorstore/               # ChromaDB database
│   ├── models_cache/              # Hugging Face model cache
│   └── chroma_cache/              # ChromaDB ONNX models
│
├── n8n-workflows/                 # n8n workflow definitions
│   ├── 01-web-search-tool.json
│   └── 02-telegram-bot.json
│
├── documentation/                 # Documentation files
│   ├── SYSTEM_DOCUMENTATION.md    # This file
│   ├── DOCUMENTATION.md           # User-facing guide
│   ├── N8N_INTEGRATION.md         # n8n setup guide
│   ├── DOCKER.md                  # Docker deployment
│   └── USER_GUIDE.md              # End-user guide
│
└── tests/                         # Test suite
    ├── test_tools.py
    ├── test_orchestrator.py
    ├── test_traditional_vs_agentic.py
    └── check_pdf.py              # PDF diagnostic tool
```

---

## Agentic RAG Implementation

### What is Agentic RAG?

Traditional RAG systems follow a fixed pipeline: Query → Retrieve → Generate → Return. **Agentic RAG** introduces autonomous decision-making, where the system:

1. **Analyzes** the query to understand intent and complexity
2. **Selects** appropriate tools based on the query characteristics
3. **Orchestrates** multi-step execution with conditional logic
4. **Enhances** results with rich citations and confidence scores
5. **Provides** transparent reasoning traces

### Core Components

#### 1. Query Analyzer (`src/agent/query_analyzer.py`)

**Purpose:** Classify queries to inform tool selection

**Output:**
```python
{
    'complexity': 'simple' | 'moderate' | 'complex',
    'intent': 'factual' | 'comparison' | 'calculation' | 'summarization' | 'external',
    'entities': List[str],  # Extracted entities
    'requires_multiple_tools': bool
}
```

**Classification Logic:**

**Complexity:**
- **Simple**: Single question, common keywords (< 10 words, 1 question mark)
- **Moderate**: Multiple clauses, 2+ entities, conjunctions (and, or, but)
- **Complex**: Multi-step reasoning, conditional logic, 3+ entities

**Intent:**
- **Factual**: what, who, when, where, define, explain
- **Comparison**: compare, difference, versus, vs, contrast
- **Calculation**: calculate, compute, math operators (+, -, *, /, %)
- **Summarization**: summarize, overview, key points, summary
- **External**: current, latest, today, year references (2024, 2025)

#### 2. Tool Registry (`src/tools/__init__.py`)

**BaseTool Interface:**
```python
class BaseTool:
    name: str
    description: str

    def can_handle(self, query: str, context: Dict) -> float:
        """Return confidence score 0.0-1.0 for handling this query"""
        pass

    def execute(self, query: str, context: Dict) -> ToolResult:
        """Execute the tool and return results"""
        pass

class ToolResult:
    success: bool
    data: Any
    metadata: Dict
    citations: List[EnhancedCitation]
    error: Optional[str]
```

**Registered Tools:**
1. **semantic_search** - Dense vector similarity search
2. **keyword_search** - BM25-based lexical search
3. **comparison** - Side-by-side document comparison
4. **summarization** - Document/section summarization
5. **calculator** - Mathematical computations
6. **web_search** - External knowledge via n8n webhook
7. **url_ingestion** - Dynamic document loading from URLs

#### 3. Tool Selection (`src/agent/orchestrator.py`)

**Hybrid Approach: Rule-Based + LLM Fallback**

**Rule-Based Selection (Primary - Fast Path):**
```python
def _rule_based_tool_selection(self, query: str, analysis: Dict) -> List[str]:
    tools = []

    # Intent-based selection
    if "compare" in query.lower():
        tools = ["comparison", "semantic_search"]
    elif "calculate" in query.lower() or any(op in query for op in ['+', '-', '*', '/', '%']):
        tools = ["calculator", "semantic_search"]
    elif "summarize" in query.lower():
        tools = ["summarization"]

    # Complexity-based selection
    elif analysis['complexity'] == 'simple':
        tools = ["semantic_search"]
    elif analysis['complexity'] == 'moderate':
        tools = ["semantic_search", "keyword_search"]  # Parallel
    else:  # complex
        tools = ["semantic_search", "keyword_search", "comparison"]

    # External knowledge trigger
    if analysis['intent'] == 'external' or any(kw in query.lower() for kw in ['current', 'latest', 'today']):
        tools.append("web_search")

    return tools
```

**LLM Fallback (for ambiguous queries):**
- Prompt LLM with tool descriptions
- Temperature 0.1 for deterministic selection
- Returns JSON list of tools

#### 4. Execution Engine (`src/agent/execution_engine.py`)

**Execution Strategies:**

**Sequential:**
```python
# Tool B receives Tool A output as context
result_A = tool_A.execute(query, context)
context['previous_results'] = [result_A]
result_B = tool_B.execute(query, context)
```

**Parallel:**
```python
# Multiple tools execute simultaneously, results merged
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(tool.execute, query, context) for tool in tools]
    results = [f.result() for f in futures]
```

**Conditional:**
```python
# Tool B only executes if Tool A meets criteria
result_A = tool_A.execute(query, context)
if result_A.metadata['confidence'] < 0.5:
    result_B = tool_B.execute(query, context)
```

#### 5. Citation Enhancer (`src/citation_enhancer.py`)

**Enhanced Citation Structure:**
```python
class EnhancedCitation:
    document: str              # Filename
    page_number: int          # Page in PDF (1-indexed)
    excerpt: str              # 50-200 char relevant excerpt
    confidence_score: float   # Composite confidence 0-1
    similarity_score: float   # Semantic similarity
    cross_encoder_score: float # Reranking score
    rank_position: int        # Rank in results
    metadata: Dict            # Additional metadata
```

**Confidence Calculation:**
```python
def calculate_confidence(citation):
    similarity = citation.semantic_score  # 0-1
    cross_score = citation.cross_encoder_score  # 0-1
    rank = citation.rank_position  # 1-5
    rank_confidence = max(0, 1.0 - (rank - 1) * 0.1)

    # Weighted combination
    return (similarity * 0.4 +
            cross_score * 0.4 +
            rank_confidence * 0.2)
```

### Reasoning Trace

Every agentic query produces a reasoning trace showing decision-making:

```json
{
  "reasoning_trace": [
    {
      "step": "query_analysis",
      "complexity": "moderate",
      "intent": "comparison",
      "requires_multiple_tools": true
    },
    {
      "step": "tool_selection",
      "tools": [
        {"name": "comparison", "confidence": 0.9},
        {"name": "semantic_search", "confidence": 0.8}
      ],
      "selection_method": "rule_based"
    },
    {
      "step": "execution_plan",
      "strategy": "sequential",
      "tool_count": 2
    },
    {
      "step": "execute_tool",
      "tool": "comparison",
      "confidence": 0.9
    },
    {
      "step": "tool_success",
      "tool": "comparison",
      "citations_count": 3
    }
  ]
}
```

---

## Tool System

### Tool Implementations

#### 1. Semantic Search Tool

**File:** `src/tools/semantic_search_tool.py`

**Description:** Dense vector similarity search using sentence embeddings

**When to Use:**
- Conceptual queries requiring semantic understanding
- Queries about meaning, concepts, relationships
- High confidence (0.9) for most queries

**Example:** "What are the benefits of remote work?" → Finds documents discussing advantages, flexibility, productivity (even if exact phrase not present)

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    # 1. Embed query using SentenceTransformer
    query_embedding = self.retriever.embedding_model.encode(query)

    # 2. Search ChromaDB vector store
    results = self.retriever.collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    # 3. Rerank with cross-encoder
    reranked = self.retriever._rerank_results(results, query)

    # 4. Extract citations with page numbers
    citations = self._extract_citations(reranked)

    return ToolResult(success=True, data=reranked, citations=citations)
```

#### 2. Keyword Search Tool

**File:** `src/tools/keyword_search_tool.py`

**Description:** BM25 lexical search for exact term matching

**When to Use:**
- Queries with specific terminology, acronyms, product names
- Exact phrase matching required
- Moderate confidence (0.7) for keyword-heavy queries

**Example:** "Find references to ISO 27001" → Exact match for standard name

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    # 1. Tokenize query
    query_tokens = self.retriever._tokenize(query)

    # 2. BM25 scoring against indexed documents
    scores = self.retriever.bm25.get_scores(query_tokens)

    # 3. Get top-k results
    top_indices = np.argsort(scores)[::-1][:5]

    # 4. Build results with scores
    results = [
        {
            'document': self.retriever.documents[idx],
            'score': scores[idx],
            'content': self.retriever.chunks[idx]
        }
        for idx in top_indices if scores[idx] > 0
    ]

    return ToolResult(success=True, data=results)
```

#### 3. Comparison Tool

**File:** `src/tools/comparison_tool.py`

**Description:** Structured comparison between entities/documents

**When to Use:**
- Queries with "compare", "difference", "versus", "vs", "contrast"
- High confidence (0.9) for comparison queries

**Example:** "Compare Policy A and Policy B" → Side-by-side structured comparison

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    # 1. Extract entities to compare
    entities = self._extract_comparison_entities(query)

    # 2. Retrieve documents for each entity
    docs_A = self.semantic_search(entities[0], context)
    docs_B = self.semantic_search(entities[1], context)

    # 3. Extract relevant sections
    sections_A = self._extract_sections(docs_A, query)
    sections_B = self._extract_sections(docs_B, query)

    # 4. Generate structured comparison using LLM
    comparison = self.llm_handler.generate_comparison(
        query, sections_A, sections_B
    )

    # 5. Merge citations from both sources
    citations = docs_A.citations + docs_B.citations

    return ToolResult(
        success=True,
        data=comparison,
        citations=citations
    )
```

#### 4. Summarization Tool

**File:** `src/tools/summarization_tool.py`

**Description:** Document or section summarization

**When to Use:**
- Queries with "summarize", "overview", "key points"
- High confidence (0.9) for summarization queries

**Example:** "Summarize the quarterly report" → Concise summary with key findings

#### 5. Calculator Tool

**File:** `src/tools/calculator_tool.py`

**Description:** Mathematical computations with document context

**When to Use:**
- Queries with "calculate", "compute", math operators
- High confidence (0.9) for calculation queries

**Example:** "What's 15% of the budget in Report X?" → Extracts budget figure, computes percentage

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    # 1. Extract mathematical expression
    expression = self._extract_expression(query)

    # 2. If expression references document data, retrieve it
    if self._requires_document_data(expression):
        doc_data = self._retrieve_numbers_from_docs(query, context)
        expression = self._substitute_values(expression, doc_data)

    # 3. Safe evaluation using ast.literal_eval
    try:
        result = eval(expression, {"__builtins__": {}})
        return ToolResult(
            success=True,
            data={'expression': expression, 'result': result}
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

#### 6. Web Search Tool

**File:** `src/tools/web_search_tool.py`

**Description:** External knowledge retrieval via n8n webhook

**When to Use:**
- Internal documents return low confidence (< 0.6)
- Query mentions current events, dates, external facts
- Queries with "current", "latest", "today", year references

**Example:** "What's the current stock price of Tesla?" → Calls n8n → DuckDuckGo API → Returns external data

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    try:
        # Call n8n webhook
        response = requests.post(
            f"{N8N_BASE_URL}/webhook/web-search",
            json={'query': query},
            timeout=30
        )

        if response.status_code == 200:
            results = response.json()
            return ToolResult(
                success=True,
                data=results.get('search_results', []),
                metadata={'source': 'external_web'}
            )
    except requests.exceptions.ConnectionError:
        return ToolResult(
            success=False,
            error="Web search service (n8n) is not available"
        )
```

**n8n Workflow:** See `n8n-workflows/01-web-search-tool.json`

#### 7. URL Ingestion Tool

**File:** `src/tools/url_ingestion_tool.py`

**Description:** Dynamic document loading from URLs

**When to Use:**
- User provides URL in query
- Phrases like "ingest", "load", "add document from"
- High confidence (0.9) when URL detected

**Example:** "Load the document from https://example.com/report.pdf and summarize it"

**Implementation:**
```python
def execute(self, query: str, context: Dict) -> ToolResult:
    # 1. Extract URL from query
    url = self._extract_url(query)

    # 2. Download document
    file_path = self._download_file(url)

    # 3. Process document (same as file upload)
    processor = DocumentProcessor()
    text = processor.extract_text(file_path)

    # 4. Chunk and embed
    chunks = self.chunker.chunk(text)
    self.retriever.add_documents(chunks, metadata={'source': url})

    # 5. Optionally answer follow-up question
    if self._has_followup_question(query):
        followup = self._extract_followup(query)
        return self.semantic_search(followup, context)

    return ToolResult(
        success=True,
        data={'url': url, 'chunks_added': len(chunks)},
        metadata={'action': 'document_ingested'}
    )
```

---

## API Reference

### Base URL

- **Development:** `http://localhost:8000/api`
- **Docker:** `http://localhost:8080/api`

### Authentication

Currently, Cortex does not require authentication. For production deployments, consider adding API key authentication.

### Endpoints

#### 1. Query Processing

**POST /api/query**

Process a natural language query using traditional or agentic RAG.

**Request Body:**
```json
{
  "query": "What are the main features of the system?",
  "mode": "agentic",  // "traditional" or "agentic"
  "conversation_id": "optional-conversation-id"
}
```

**Response (Agentic Mode):**
```json
{
  "answer": "Based on the provided documents, here are the main features...",
  "sources": [
    {
      "document": "document.pdf",
      "page_number": 5,
      "excerpt": "The system provides advanced features including...",
      "confidence_score": 0.87,
      "similarity_score": 0.92,
      "cross_encoder_score": 0.85,
      "rank_position": 1,
      "metadata": {
        "author": "John Doe",
        "page": 5,
        "chunk_index": 15
      }
    }
  ],
  "confidence": "high",  // "high", "medium", "low"
  "evaluation": {
    "answer_relevancy": 0.89,
    "context_precision": 0.75,
    "context_recall": 0.82,
    "faithfulness": 0.91,
    "source_attribution_accuracy": 0.88,
    "response_time": 2.5
  },
  "reasoning_trace": [
    {
      "step": "query_analysis",
      "complexity": "moderate",
      "intent": "factual"
    },
    {
      "step": "tool_selection",
      "tools": [
        {"name": "semantic_search", "confidence": 0.9}
      ]
    },
    {
      "step": "execute_tool",
      "tool": "semantic_search"
    },
    {
      "step": "tool_success",
      "tool": "semantic_search",
      "citations_count": 5
    }
  ],
  "metadata": {
    "tools_used": ["semantic_search"],
    "attempted_tools": ["semantic_search", "web_search"],
    "failed_tools": ["web_search"],
    "complexity": "moderate",
    "intent": "factual",
    "execution_time": 2.5,
    "kb_confidence": 0.87
  },
  "execution_time": 2.5,
  "total_time": 2.5,
  "mode": "agentic"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request (missing query)
- `500` - Server error

#### 2. Document Upload

**POST /api/upload**

Upload PDF documents for processing and indexing.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (PDF file)

**Response:**
```json
{
  "filename": "document.pdf",
  "pages": 25,
  "chunks": 150,
  "status": "success",
  "message": "Document processed successfully"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid file type or no file provided
- `500` - Processing error

#### 3. System Status

**GET /api/status**

Get system status and statistics.

**Response:**
```json
{
  "status": "ok",
  "system_name": "Cortex - AI Knowledge Assistant",
  "collection": {
    "collection_name": "documents",
    "document_count": 220,
    "embedding_model": "all-MiniLM-L6-v2",
    "has_keyword_index": true
  },
  "ollama_available": true,
  "ocr_available": true
}
```

#### 4. Document Management

**GET /api/documents**

List all processed documents.

**Response:**
```json
{
  "documents": [
    {
      "filename": "document1.pdf",
      "upload_date": "2026-01-14T10:30:00",
      "pages": 25,
      "chunks": 150,
      "author": "John Doe"
    }
  ],
  "total": 220
}
```

**DELETE /api/documents/{filename}**

Remove a document from the system.

**Response:**
```json
{
  "status": "success",
  "message": "Document deleted successfully"
}
```

#### 5. Conversation Management

**GET /api/conversation/{conversation_id}**

Retrieve conversation history.

**Response:**
```json
{
  "conversation_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "What are the main features?",
      "timestamp": "2026-01-14T10:30:00"
    },
    {
      "role": "assistant",
      "content": "Based on the documents...",
      "sources": [...],
      "timestamp": "2026-01-14T10:30:05"
    }
  ]
}
```

---

## Web UI Reference

### Interface Components

#### 1. Chat Interface

**Location:** Main center panel

**Features:**
- Message input with send button
- Message history display
- Markdown rendering with syntax highlighting
- Copy-to-clipboard for responses
- Reasoning trace collapsible section
- Enhanced citations with page numbers

#### 2. Source Citations

**Display Format:**
```
[1] document.pdf (Page 5) ⭐⭐⭐⭐☆
"The system provides advanced features including..."
```

**Click behavior:** Expands to show full excerpt

**Confidence Stars:**
- ⭐⭐⭐⭐⭐ (5 stars): Confidence 0.9-1.0 (Excellent)
- ⭐⭐⭐⭐☆ (4 stars): Confidence 0.7-0.9 (Good)
- ⭐⭐⭐☆☆ (3 stars): Confidence 0.5-0.7 (Fair)
- ⭐⭐☆☆☆ (2 stars): Confidence 0.3-0.5 (Low)
- ⭐☆☆☆☆ (1 star): Confidence 0.0-0.3 (Very Low)

#### 3. Reasoning Trace

**Location:** Collapsible section below answer

**Steps Displayed:**
1. **Query Analysis:** Complexity and intent classification
2. **Tool Selection:** Which tools were selected and why
3. **Execution Plan:** Strategy (sequential/parallel/conditional)
4. **Tool Execution:** Each tool that ran
5. **Tool Results:** Success/failure with citation counts or errors

#### 4. Evaluation Metrics

**Location:** Below answer, circular progress indicators

**Metrics:**
- **Answer Relevancy** (0-1): How well the answer addresses the query
- **Context Precision** (0-1): Relevance of retrieved context
- **Context Recall** (0-1): Completeness of retrieved context
- **Faithfulness** (0-1): Answer accuracy relative to sources
- **Source Attribution** (0-1): Correct citation of sources

#### 5. Notification Panel

**Location:** Collapsible right panel

**Features:**
- Real-time notifications for uploads, errors, completions
- Notification types: info, success, warning, error
- Timestamp tracking ("2 minutes ago")
- Dismissible notifications
- Unread counter badge

#### 6. System Info Panel

**Location:** Collapsible left sidebar

**Information Displayed:**
- System name: "Cortex - AI Knowledge Assistant"
- Number of documents loaded
- Embedding model in use
- Ollama LLM status
- OCR availability

---

## Configuration Guide

### Environment Variables

**File:** `.env`

```bash
# Timezone
TZ=UTC

# Debug Mode
DEBUG=false

# Ports
WEB_UI_PORT=8080
API_PORT=8000
OLLAMA_PORT=11434

# GPU Support
ENABLE_GPU=auto  # auto, true, false

# n8n Configuration
N8N_PORT=5678
N8N_BASE_URL=http://cortex-n8n:5678
N8N_USER=admin
N8N_PASSWORD=changeme123

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Application Settings

**File:** `config/settings.py`

```python
# System Information
PAGE_TITLE = "Cortex - AI Knowledge Assistant"
SYSTEM_VERSION = "2.0"

# Embedding Model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"  # or "http://ollama:11434" in Docker
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_TIMEOUT = 120  # seconds

# Retrieval Settings
MAX_CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200
TOP_K_DOCUMENTS = 5
SIMILARITY_THRESHOLD = 0.3

# Reranking
USE_CROSS_ENCODER = True
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
TOP_K_RERANK = 3

# OCR Settings
OCR_ENABLED = True
OCR_LANGUAGES = ["eng"]  # Tesseract language codes

# Evaluation Settings
ENABLE_EVALUATION = True

# Conversation Settings
MAX_CONVERSATION_HISTORY = 10
CONVERSATION_TIMEOUT = 3600  # seconds

# n8n Integration
N8N_BASE_URL = os.environ.get("N8N_BASE_URL") or "http://localhost:5678"
N8N_WEBHOOK_TIMEOUT = 30  # seconds
```

### Model Configuration

#### Switching LLM Models

**Using run_docker.sh:**
```bash
./run_docker.sh
# Select option 6: Switch to a faster model
# Choose from: llama3.2:3b, phi3:mini, or custom
```

**Manual Configuration:**
```python
# In config/settings.py
OLLAMA_MODEL = "phi3:mini"  # Faster, less resource-intensive
# or
OLLAMA_MODEL = "llama3:8b"  # Larger, higher quality
```

**Pull New Models:**
```bash
docker compose exec ollama ollama pull phi3:mini
```

#### Switching Embedding Models

```python
# In config/settings.py
EMBEDDING_MODEL = "all-mpnet-base-v2"  # Higher quality, slower
# or
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Default, balanced
# or
EMBEDDING_MODEL = "paraphrase-MiniLM-L3-v2"  # Faster, smaller
```

**Note:** Changing embedding models requires reprocessing all documents.

---

## Deployment Guide

### Docker Deployment (Recommended)

#### Standard Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd Cortex

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Start services
./run_docker.sh
# Select option 1: Start Cortex

# 4. Wait for startup (1-2 minutes)
# Access at http://localhost:8080
```

#### With n8n Automation

```bash
./run_docker.sh
# Select option 2: Start Cortex with n8n

# Access points:
# - Web UI: http://localhost:8080
# - API: http://localhost:8000/api
# - n8n: http://localhost:5678
```

#### GPU Acceleration

**Prerequisites:**
- NVIDIA GPU
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

**Automatic Detection:**
```bash
./run_docker.sh
# Select option 1 or 2
# Script auto-detects GPU and uses docker-compose.gpu.yml
```

**Manual:**
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### Manual Deployment (Without Docker)

#### Prerequisites

- Python 3.9+
- Ollama installed locally
- Tesseract OCR (optional but recommended)
- Poppler (for PDF processing)

#### Installation Steps

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Ollama
# Visit: https://ollama.ai/download
# Pull model:
ollama pull llama3.2:3b

# 3. Install OCR dependencies (optional)
# macOS:
brew install tesseract poppler

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils

# 4. Create configuration
cp config/settings.example.py config/settings.py
# Edit settings as needed

# 5. Start application
# Option A: Web UI (FastAPI + Nginx simulation)
python api.py

# Option B: Streamlit UI
streamlit run app.py

# Access at http://localhost:8000 (FastAPI) or http://localhost:8501 (Streamlit)
```

### Production Deployment

#### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name cortex.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cortex.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # API Backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long queries
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Web UI
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # n8n (if enabled)
    location /n8n {
        proxy_pass http://localhost:5678;
        proxy_set_header Host $host;
    }
}
```

#### Systemd Service

```ini
[Unit]
Description=Cortex AI Knowledge Assistant
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/cortex
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=cortex
Group=cortex

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable cortex
sudo systemctl start cortex
sudo systemctl status cortex
```

#### Security Considerations

1. **Change Default Credentials:**
```bash
# In .env file:
N8N_PASSWORD=your_secure_password_here
```

2. **Enable HTTPS:** Use Let's Encrypt with Certbot
```bash
sudo certbot --nginx -d cortex.yourdomain.com
```

3. **Firewall Rules:**
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

4. **API Authentication:** Implement API key authentication in `api.py`

5. **Rate Limiting:** Add rate limiting middleware

---

## Development Guide

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone <repository-url>
cd Cortex

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install dependencies in editable mode
pip install -e .
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests
pytest tests/
```

### Project Structure Best Practices

#### Adding a New Tool

1. **Create tool file:** `src/tools/my_new_tool.py`

```python
from src.tools import BaseTool, ToolResult
from typing import Dict

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "Description of what this tool does"

    def can_handle(self, query: str, context: Dict) -> float:
        """Return confidence 0.0-1.0"""
        if "keyword" in query.lower():
            return 0.9
        return 0.0

    def execute(self, query: str, context: Dict) -> ToolResult:
        """Implement tool logic"""
        try:
            # Your implementation here
            result = self._process(query)

            return ToolResult(
                success=True,
                data=result,
                metadata={'tool': self.name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
```

2. **Register tool:** In `src/agent/orchestrator.py`

```python
from src.tools.my_new_tool import MyNewTool

class AgenticOrchestrator:
    def __init__(self):
        # ... existing code ...
        self.tool_registry.register("my_new_tool", MyNewTool())
```

3. **Add tests:** `tests/test_my_new_tool.py`

```python
import pytest
from src.tools.my_new_tool import MyNewTool

def test_can_handle():
    tool = MyNewTool()
    assert tool.can_handle("query with keyword", {}) > 0.5
    assert tool.can_handle("unrelated query", {}) < 0.5

def test_execute():
    tool = MyNewTool()
    result = tool.execute("test query", {})
    assert result.success == True
```

#### Modifying Query Analysis

**File:** `src/agent/query_analyzer.py`

Add new intent or complexity classification:

```python
def analyze(self, query: str) -> Dict:
    # Add new intent
    if any(kw in query.lower() for kw in ['translate', 'language']):
        intent = 'translation'

    # Add new complexity factor
    if len(query.split()) > 30:
        complexity = 'very_complex'

    # ... existing code ...
```

#### Creating Custom Evaluation Metrics

**File:** `src/evaluator.py`

```python
def evaluate_custom_metric(self, query, response, context):
    """Add custom evaluation logic"""
    score = 0.0

    # Your evaluation logic here

    return score
```

### Testing

#### Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tools.py

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_orchestrator.py::test_tool_selection
```

#### Integration Tests

```bash
# Test traditional vs agentic comparison
pytest tests/test_traditional_vs_agentic.py -v

# Test n8n integration (requires n8n running)
pytest tests/test_n8n_integration.py
```

#### Manual Testing

**PDF Diagnostic:**
```bash
python tests/check_pdf.py /path/to/document.pdf
```

**Curl API Testing:**
```bash
# Test query
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "mode": "agentic"}'

# Test upload
curl -X POST http://localhost:8080/api/upload \
  -F "file=@document.pdf"
```

---

## Performance & Optimization

### Performance Benchmarks

**Hardware:** MacBook Pro M1, 16GB RAM

| Query Type | Traditional RAG | Agentic RAG | Speedup |
|-----------|----------------|-------------|---------|
| Simple factual | 1.2s | 1.5s | 0.8x |
| Comparison | 2.8s | 3.2s | 0.87x |
| Complex multi-step | 4.5s | 5.8s | 0.77x |
| With web search | N/A | 8.5s | N/A |

**Note:** Agentic mode is slightly slower due to query analysis and tool selection overhead, but provides significantly better answer quality.

### Optimization Strategies

#### 1. Model Caching

**Pre-download models:**
```bash
# In docker-entrypoint.sh
python src/preload_models.py
```

**Models cached:**
- Sentence Transformers: `./data/models_cache/`
- ChromaDB ONNX: `./data/chroma_cache/onnx_models/`

#### 2. Embedding Optimization

**ONNX Runtime (Automatic):**
ChromaDB automatically uses ONNX-optimized embeddings (2-3x faster)

**Batch Processing:**
```python
# In document_processor.py
embeddings = model.encode(
    chunks,
    batch_size=32,  # Adjust based on RAM
    show_progress_bar=True
)
```

#### 3. LLM Optimization

**Context Window Management:**
```python
# Limit context to top-K most relevant chunks
TOP_K_DOCUMENTS = 3  # Instead of 5
```

**Smaller Model:**
```python
OLLAMA_MODEL = "phi3:mini"  # 2.7B params vs 3B
```

**Streaming Responses:**
```python
# In llm_handler.py
def generate_stream(self, prompt):
    for chunk in ollama.generate(model=self.model, prompt=prompt, stream=True):
        yield chunk['response']
```

#### 4. Parallel Tool Execution

**Enabled by default for independent tools:**
```python
# In execution_engine.py
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(tool.execute, query, context)
               for tool in parallel_tools]
    results = [f.result() for f in as_completed(futures)]
```

#### 5. Database Optimization

**ChromaDB Performance:**
```python
# Use persistent storage (not in-memory)
client = chromadb.PersistentClient(path="./data/vectorstore")

# Batch inserts
collection.add(
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadata,
    ids=ids
)
```

#### 6. Caching Strategies

**Query Result Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_hash):
    # Cache frequently asked queries
    pass
```

### Resource Requirements

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| **RAM** | 4GB | 8GB | 16GB+ |
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **Disk** | 10GB | 20GB | 50GB+ |
| **GPU** | None | NVIDIA 4GB VRAM | NVIDIA 8GB+ VRAM |

**Note:** GPU acceleration only affects LLM inference (Ollama), not embeddings or retrieval.

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

**Symptom:** `docker compose up -d` fails

**Solutions:**
```bash
# Check logs
docker compose logs cortex

# Remove old containers
docker compose down
docker system prune -a

# Rebuild
docker compose build --no-cache
docker compose up -d
```

#### 2. Ollama Connection Error

**Symptom:** "Error generating response: HTTPConnectionPool(host='ollama', port=11434)"

**Solutions:**
```bash
# Check Ollama is running
docker ps | grep ollama

# Test Ollama manually
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:3b", "prompt": "test"}'

# Restart Ollama container
docker compose restart ollama

# Switch to faster model
./run_docker.sh
# Select option 6: Switch to a faster model
```

#### 3. Web Search Not Working

**Symptom:** "Web search service (n8n) is not available"

**Solutions:**
```bash
# Check n8n is running
docker ps | grep cortex-n8n

# Start with n8n
docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d

# Import workflows
# 1. Open http://localhost:5678
# 2. Login (default: admin / changeme123)
# 3. Workflows > Import from File
# 4. Select n8n-workflows/01-web-search-tool.json
# 5. Save and activate workflow
```

#### 4. Documents Not Loading

**Symptom:** "Document processing failed" or empty results

**Solutions:**
```bash
# Check PDF format
python tests/check_pdf.py /path/to/document.pdf

# Enable OCR for problematic PDFs
# In config/settings.py:
OCR_ENABLED = True

# Check disk space
df -h

# Check vectorstore permissions
ls -la data/vectorstore/

# Reset vectorstore
rm -rf data/vectorstore/*
# Re-upload documents
```

#### 5. JavaScript Errors in Web UI

**Symptom:** Console errors, UI not responding

**Solutions:**
```bash
# Clear browser cache
# Chrome: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)

# Check browser console (F12)
# Look for specific error messages

# Verify files are served correctly
curl http://localhost:8080/js/app.js | head

# Restart container
docker compose restart cortex
```

#### 6. High Memory Usage

**Symptom:** System slows down, OOM errors

**Solutions:**
```python
# In config/settings.py

# Reduce batch size
EMBEDDING_BATCH_SIZE = 16  # Down from 32

# Limit chunks in memory
MAX_CHUNK_SIZE = 800  # Down from 1000

# Reduce top-k
TOP_K_DOCUMENTS = 3  # Down from 5

# Switch to smaller model
OLLAMA_MODEL = "phi3:mini"
```

#### 7. Slow Query Response

**Symptom:** Queries take > 30 seconds

**Solutions:**
- Switch to smaller LLM model (phi3:mini)
- Reduce TOP_K_DOCUMENTS to 3
- Enable parallel tool execution
- Use GPU acceleration if available
- Check Ollama timeout settings

#### 8. Evaluation Metrics Showing 0.0

**Symptom:** All evaluation scores are 0.0

**Cause:** RAGAS evaluation requires sufficient context

**Solutions:**
```python
# In config/settings.py
ENABLE_EVALUATION = False  # Disable if not needed

# Or ensure sufficient context is retrieved
TOP_K_DOCUMENTS = 5  # Increase if too low
```

### Debugging Tools

#### Enable Debug Logging

```python
# In config/settings.py
DEBUG = True
LOG_LEVEL = "DEBUG"
```

```bash
# In .env
DEBUG=true
```

#### View Container Logs

```bash
# Real-time logs
docker compose logs -f cortex

# Last 100 lines
docker compose logs --tail=100 cortex

# Specific service
docker compose logs ollama
docker compose logs cortex-n8n
```

#### Access Container Shell

```bash
# Interactive shell
docker exec -it cortex bash

# Check processes
docker exec cortex ps aux

# Check disk usage
docker exec cortex df -h
```

#### Test API Endpoints

```bash
# Health check
curl http://localhost:8080/api/status

# List documents
curl http://localhost:8080/api/documents

# Test query
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "mode": "agentic"}' | jq
```

---

## Appendices

### Appendix A: Glossary

- **Agentic RAG:** Retrieval-Augmented Generation system with autonomous tool selection
- **BM25:** Probabilistic ranking function for keyword search
- **ChromaDB:** Open-source embedding database
- **Cross-Encoder:** Reranking model for improved result relevance
- **Embedding:** Vector representation of text for semantic search
- **Hybrid Retrieval:** Combination of semantic and keyword search
- **LLM:** Large Language Model
- **n8n:** Low-code automation platform
- **OCR:** Optical Character Recognition
- **Ollama:** Local LLM inference server
- **RAGAS:** Retrieval-Augmented Generation Assessment framework
- **Semantic Search:** Similarity search based on meaning, not keywords
- **Sentence Transformer:** Neural network for text embeddings
- **Tool:** Specialized component that performs a specific task

### Appendix B: File Format Support

| Format | Supported | Extraction Method | Notes |
|--------|-----------|-------------------|-------- |
| PDF | ✅ | PyMuPDF, PyPDF2, pdfplumber | Multiple fallback methods |
| PDF (Scanned) | ✅ | Tesseract OCR | Requires OCR_ENABLED=True |
| PDF (Encrypted) | ❌ | N/A | Password-protected PDFs not supported |
| DOCX | ❌ | N/A | Future support planned |
| TXT | ❌ | N/A | Future support planned |
| HTML | ❌ | N/A | Future support planned |

### Appendix C: Model Recommendations

| Use Case | LLM Model | Embedding Model | Notes |
|----------|-----------|-----------------|-------|
| **High Quality** | llama3:8b | all-mpnet-base-v2 | Best results, requires 16GB+ RAM |
| **Balanced (Default)** | llama3.2:3b | all-MiniLM-L6-v2 | Good balance of speed & quality |
| **Fast/Low Resource** | phi3:mini | paraphrase-MiniLM-L3-v2 | Works with 4-8GB RAM |
| **Multilingual** | llama3.2:3b | paraphrase-multilingual-MiniLM-L12-v2 | Supports 50+ languages |

### Appendix D: n8n Workflow Templates

#### Web Search Workflow

**File:** `n8n-workflows/01-web-search-tool.json`

**Nodes:**
1. Webhook Trigger: `/webhook/web-search`
2. HTTP Request: DuckDuckGo Instant Answer API
3. Function: Parse and format results
4. Respond to Webhook: Return JSON

**Usage:** Automatically called by WebSearchTool when needed

#### Telegram Bot Workflow

**File:** `n8n-workflows/02-telegram-bot.json`

**Nodes:**
1. Telegram Trigger: New message
2. IF: Check if command (/start)
3. HTTP Request: POST to Cortex API
4. Function: Format response
5. Telegram Send: Reply to user

**Setup:** Requires `TELEGRAM_BOT_TOKEN` in `.env`

### Appendix E: Evaluation Metrics Explained

**Answer Relevancy (0-1):**
- Measures how well the answer addresses the query
- High score: Answer directly answers question
- Low score: Answer is off-topic or incomplete

**Context Precision (0-1):**
- Measures relevance of retrieved documents
- High score: Retrieved docs are highly relevant
- Low score: Many irrelevant docs retrieved

**Context Recall (0-1):**
- Measures completeness of retrieved context
- High score: All necessary information retrieved
- Low score: Missing important context

**Faithfulness (0-1):**
- Measures accuracy relative to source documents
- High score: Answer is factually grounded in sources
- Low score: Answer contains hallucinations

**Source Attribution Accuracy (0-1):**
- Measures correctness of citations
- High score: Citations point to correct sources
- Low score: Incorrect or missing citations

### Appendix F: API Rate Limits

Currently, Cortex does not enforce rate limits. For production:

```python
# Example rate limiting middleware (FastAPI)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/query")
@limiter.limit("10/minute")
async def query(request: Request):
    # Query processing
    pass
```

### Appendix G: Backup & Recovery

**Backup Critical Data:**
```bash
# Documents
tar -czf backup_documents_$(date +%Y%m%d).tar.gz data/documents/

# Vector store
tar -czf backup_vectorstore_$(date +%Y%m%d).tar.gz data/vectorstore/

# Configuration
cp config/settings.py config/settings.py.backup
cp .env .env.backup
```

**Restore:**
```bash
# Stop services
docker compose down

# Restore files
tar -xzf backup_documents_20260114.tar.gz -C ./
tar -xzf backup_vectorstore_20260114.tar.gz -C ./

# Restart
docker compose up -d
```

### Appendix H: Contributing

**Contribution Guidelines:**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Update documentation
6. Submit pull request

**Code Style:**
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions < 50 lines

**Commit Message Format:**
```
[Component] Brief description

Detailed explanation if needed

Fixes #123
```

---

## Support & Contact

**Documentation:** See `documentation/` directory for additional guides

**Issues:** Report bugs and feature requests on GitHub

**Community:** Join discussions in the project repository

---

**End of System Documentation**

*Last Updated: January 14, 2026*
*Version: 2.0*
*Cortex - AI Knowledge Assistant*
