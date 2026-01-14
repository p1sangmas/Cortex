# 🧠 Cortex - Agentic AI-Powered Knowledge Base Assistant

<div align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Docker-blue?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/LLM-Llama%203.2%203B-orange?style=flat-square" alt="LLM">
  <img src="https://img.shields.io/badge/RAG-Agentic-purple?style=flat-square" alt="Agentic RAG">
</div>

<div align="center">
  <h3>🤖 Autonomous Intelligence • 🧩 Tool-Based Architecture • 🔍 Multi-Step Reasoning</h3>
</div>

---

## 🚀 What is Cortex?

**Cortex** is an advanced AI knowledge assistant that doesn't just retrieve information—it **thinks**. Unlike traditional RAG systems that follow fixed pipelines, Cortex uses **agentic AI** to autonomously select specialized tools, orchestrate multi-step reasoning, and provide transparent decision traces.

### Why Agentic?

Traditional RAG systems are rigid: they always retrieve, then generate, regardless of the query. Cortex is different:

| Traditional RAG | Cortex (Agentic RAG) |
|----------------|----------------------|
| Fixed pipeline | **Autonomous tool selection** |
| Single retrieval strategy | **7 specialized tools** (semantic, keyword, comparison, calculator, web search, etc.) |
| One-size-fits-all | **Query-adaptive strategies** (sequential, parallel, conditional) |
| Basic citations | **Enhanced citations** (page numbers, excerpts, confidence scores) |
| Black box | **Transparent reasoning traces** |
| Internal knowledge only | **External knowledge** via web search when needed |

### 🎯 Core Capabilities

- **🤖 Autonomous Decision-Making**: Analyzes queries to determine intent and complexity, then selects appropriate tools
- **🧩 Tool-Based Architecture**: 7 specialized tools working in concert (not just retrieval!)
- **🔗 Multi-Step Reasoning**: Chains tools together for complex queries requiring multiple operations
- **📊 Enhanced Citations**: Every answer includes page numbers, relevant excerpts, and confidence scores
- **🔍 Hybrid Retrieval**: Combines semantic similarity and keyword matching for optimal results
- **🌐 External Knowledge Integration**: Augments internal documents with web search via n8n automation
- **💡 Transparent Reasoning**: See exactly which tools were used and why for every answer
- **🔒 Privacy-First**: Runs entirely locally using Ollama—no external APIs required (except optional web search)

---

## ⚡ Quick Start

### Docker Setup (Recommended)

Get started in under 2 minutes:

```bash
# Clone the repository
git clone https://github.com/p1sangmas/Cortex.git
cd Cortex

# Run the management script
chmod +x run_docker.sh
./run_docker.sh

# Select option 1: "Start Cortex"
```

**Access Points:**
- 🌐 **Web UI**: http://localhost:8080
- 🔌 **API**: http://localhost:8000/api
- 📊 **Status**: http://localhost:8080/api/status

### With n8n Automation (Optional)

Enable advanced workflows (web search, document auto-ingestion):

```bash
./run_docker.sh
# Select option 2: "Start Cortex with n8n (automation workflows)"
```

**Additional Access:**
- 🔗 **n8n Workflows**: http://localhost:5678

📖 **See:** [n8n Integration Guide](documentation/N8N_INTEGRATION.md) for setup

---

## 🧩 The 7 Specialized Tools

Cortex's agentic system leverages specialized tools that work together:

| Tool | Purpose | When Used | Example |
|------|---------|-----------|---------|
| **🔍 Semantic Search** | Dense vector similarity search | Conceptual queries | "What are the benefits of remote work?" |
| **🔤 Keyword Search** | BM25 lexical matching | Specific terms, acronyms | "Find ISO 27001 compliance sections" |
| **⚖️ Comparison** | Structured side-by-side analysis | Queries with "compare", "difference" | "Compare Policy A vs Policy B" |
| **📝 Summarization** | Condense documents or sections | "Summarize", "key points" | "Summarize Q3 earnings report" |
| **🔢 Calculator** | Mathematical computations | Calculations with context | "What's 15% of the budget in Report X?" |
| **🌐 Web Search** | External knowledge retrieval | Current events, external facts | "Latest Tesla stock price" |
| **📥 URL Ingestion** | Dynamic document loading | URLs in query | "Load https://example.com/doc.pdf and summarize" |

### Tool Orchestration Strategies

- **Sequential**: Tool B receives Tool A's output (for dependent operations)
- **Parallel**: Multiple tools run simultaneously (for independent searches)
- **Conditional**: Tool B only runs if Tool A meets criteria (for fallback logic)

---

## 🎨 Web UI: Dual-Mode Interface

Cortex features a modern web interface with **side-by-side comparison**:

### Traditional RAG Mode
- Fixed retrieval → generation pipeline
- Basic citations (filename only)
- Fast, straightforward

### Agentic RAG Mode ⭐
- Autonomous tool selection
- Multi-step reasoning
- **Reasoning Trace Display**: See exactly which tools were used and why
- **Enhanced Citations**: Page numbers, excerpts, confidence scores
- **Evaluation Metrics**: Answer relevancy, faithfulness, context precision

**Switch modes instantly** to compare results!

---

## 📊 Enhanced Citations

Every answer includes rich, actionable citations:

```
[1] technical_manual.pdf (Page 42) ⭐⭐⭐⭐⭐
    "The system implements a three-tier architecture..."
    Confidence: 0.92 | Similarity: 0.89 | Rank: #1

[2] design_spec.pdf (Page 8) ⭐⭐⭐⭐☆
    "Authentication uses JWT tokens with 24-hour expiry..."
    Confidence: 0.85 | Similarity: 0.82 | Rank: #2
```

---

## 🔗 n8n Integration: Low-Code Automation

Cortex integrates with **n8n** for powerful, no-code automation:

### Pre-Built Workflows

1. **Web Search Tool** (`01-web-search-tool.json`)
   - Augments internal knowledge with external sources
   - Uses DuckDuckGo API (no API key required)
   - Triggered automatically when internal docs lack information

2. **URL Document Ingestion** (`03-url-document-ingestion.json`)
   - Auto-ingest PDFs from URLs
   - Webhook-triggered from queries like "load https://..."

**Create custom workflows** visually—no coding required!

📖 **See:** [n8n Integration Guide](documentation/N8N_INTEGRATION.md)

---

## 🏗️ Architecture

**Key Components:**
- **Agentic Orchestrator**: Brain of the system—analyzes, decides, executes
- **Tool Registry**: 7 specialized tools with confidence-based selection
- **Execution Engine**: Orchestrates tool execution (sequential/parallel/conditional)
- **Citation Enhancer**: Adds page numbers, excerpts, confidence scores
- **ChromaDB**: Vector database for semantic search
- **Ollama**: Local LLM inference (Llama 3.2 3B)
- **n8n**: Automation platform for workflows and external integrations

---

## 📖 Documentation

Comprehensive guides for every use case:

| Document | Description |
|----------|-------------|
| **[System Documentation](documentation/SYSTEM_DOCUMENTATION.md)** | Complete technical reference (73KB, 1,600+ lines) |
| **[User Guide](documentation/USER_GUIDE.md)** | End-user instructions and tutorials |
| **[n8n Integration](documentation/N8N_INTEGRATION.md)** | Workflow automation setup and examples |
| **[Docker Guide](documentation/DOCKER.md)** | Deployment and container management |
| **[Environment Setup](documentation/ENVIRONMENT_SETUP.md)** | Configuration and environment variables |
| **[OCR Setup](documentation/OCR_SETUP.md)** | Optical character recognition for scanned PDFs |
| **[Full Documentation](documentation/DOCUMENTATION.md)** | Complete user-facing guide |

---

## 🛠️ Technology Stack

**Core AI:**
- **Agentic System**: Custom tool orchestration with autonomous decision-making
- **LLM**: Ollama (Llama 3.2 3B, local inference)
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB with ONNX optimization

**Retrieval & Processing:**
- **Hybrid Search**: Semantic (dense vectors) + Keyword (BM25)
- **PDF Processing**: PyPDF2, PyMuPDF, pdfplumber, Tesseract OCR
- **Chunking**: Semantic text segmentation with overlap
- **Reranking**: Cross-encoder for result refinement

**Infrastructure:**
- **Backend**: Python FastAPI (async API)
- **Frontend**: HTML/CSS/JavaScript (modern UI) + Streamlit (alternative)
- **Automation**: n8n (workflow orchestration)
- **Containers**: Docker + Docker Compose
- **GPU Support**: NVIDIA Container Toolkit (optional)

**Evaluation:**
- RAGAS-inspired metrics (answer relevancy, faithfulness, context precision/recall)

---

## ⚙️ Configuration

### Model Selection

Switch LLM models based on your hardware:

```bash
./run_docker.sh
# Select option 6: "Switch to a faster model"

Options:
1. llama3.2:3b (default, best quality)
2. phi3:mini (faster, lower resource)
3. Custom model (specify any Ollama model)
```

### Performance Tuning

Edit `config/settings.py`:

```python
# Retrieval Settings
TOP_K_DOCUMENTS = 5          # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.3   # Minimum similarity score

# Reranking
USE_CROSS_ENCODER = True     # Enable reranking (better quality)
TOP_K_RERANK = 3            # Top results after reranking

# LLM Settings
OLLAMA_TIMEOUT = 120        # Timeout in seconds
OLLAMA_MODEL = "llama3.2:3b"  # Model name

# Agentic Settings
ENABLE_TOOL_SELECTION = True  # Enable agentic mode
TOOL_SELECTION_METHOD = "hybrid"  # "hybrid", "rule_based", or "llm"
```

---

## 🔒 Privacy & Security

**Cortex is privacy-first by design:**

✅ **100% Local Processing**
- All document processing happens on your machine
- Embeddings generated locally (Sentence-Transformers)
- LLM inference via local Ollama server
- Vector database stored locally (ChromaDB)

✅ **No External API Calls** (except optional features)
- Web search via n8n is **optional** and **explicit**
- No telemetry, tracking, or data collection

✅ **Your Data Stays Yours**
- Documents never leave your infrastructure
- No cloud storage, no remote servers
- Perfect for sensitive documents (legal, medical, financial)

---

## 🐛 Troubleshooting

### Common Issues

**Q: Queries are timing out**
```bash
# Switch to a faster model
./run_docker.sh
# Select option 6, choose phi3:mini
```

**Q: Web search isn't working**
```bash
# Ensure n8n is running
./run_docker.sh
# Select option 2 (start with n8n)

# Import web search workflow
# 1. Open http://localhost:5678
# 2. Workflows → Import from File
# 3. Select n8n-workflows/01-web-search-tool.json
```

**Q: Documents won't load**
```bash
# Diagnose PDF issues
python tests/check_pdf.py path/to/document.pdf

# Enable OCR if needed
# Edit config/settings.py: OCR_ENABLED = True
```

📖 **See:** [Full Troubleshooting Guide](documentation/DOCUMENTATION.md#troubleshooting)

---

## 🤝 Contributing

Contributions are welcome! Here are ways to help:

- **Add new tools**: Extend the tool registry with specialized capabilities
- **Improve query analysis**: Enhance intent detection and complexity classification
- **Create n8n workflows**: Build new automation workflows
- **Documentation**: Improve guides, add examples, fix typos
- **Bug reports**: Open issues for bugs or feature requests

**Development Setup:**
```bash
git clone https://github.com/p1sangmas/Cortex.git
cd Cortex
pip install -r requirements.txt
# Make your changes
# Run tests: pytest tests/
# Submit PR
```

---


## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

---

## 🙏 Acknowledgments

Built with these amazing open-source projects:
- [Ollama](https://ollama.ai/) - Local LLM inference
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence-Transformers](https://www.sbert.net/) - Embeddings
- [n8n](https://n8n.io/) - Workflow automation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python API framework

---

Built with ❤️ by Fakhrul Fauzi
