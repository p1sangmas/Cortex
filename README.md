# 🧠 Cortex - AI-Powered Knowledge Base Assistant

<div align="center">
  <img src="assets/logo.png" alt="Cortex Logo" width="200">
  <br>
  <img src="https://img.shields.io/badge/version-1.1.0-green?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Docker-blue?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/LLM-Llama%203.2%203B-orange?style=flat-square" alt="LLM">
</div>

## 🚀 Overview

Cortex is a privacy-focused, self-hosted AI assistant that helps you extract insights from your PDF documents using local LLMs through Ollama. Ask questions about your documents in natural language and receive accurate answers with source citations - all without sending your data to external services.

<div align="center">
  <h3>📄 Upload Documents → 🔍 Ask Questions → 🤖 Get AI Answers</h3>
</div>

## ✨ Key Features

- **🔒 Privacy First**: All processing happens locally - no external API calls
- **📄 Multi-format PDF Processing**: Robust text extraction with OCR support
- **🔍 Hybrid Retrieval System**: Combines semantic and keyword search for accuracy
- **🤖 Agentic RAG System**: Intelligent tool selection and multi-step reasoning
- **🔗 n8n Workflow Integration**: Low-code automation with web search and Telegram bot
- **🌐 External Knowledge**: Augments internal docs with web search when needed
- **💬 Conversation Memory**: Maintains context across multiple questions
- **📊 Enhanced Citations**: Page numbers, excerpts, and confidence scores
- **🔄 Automatic Document Loading**: Auto-loads PDFs from the documents directory
- **🌐 Multiple Interfaces**: Web UI, Streamlit, and Telegram bot
- **⚡ Docker Ready**: Simple setup with Docker and GPU acceleration support

## 🚀 Quick Start with Docker (Recommended)

The easiest way to get started is using the included Docker helper script:

```bash
# Make the script executable (if needed)
chmod +x run_docker.sh

# Run the script and follow the menu options
./run_docker.sh
```

Select option 1 from the menu to start Cortex, then:
- **Web UI**: http://localhost:8080
- **API Endpoint**: http://localhost:8000/api

### 🔗 With n8n Automation (Optional)

To enable advanced workflows like web search and Telegram bot:

```bash
./run_docker.sh
# Select option 2: "Start Cortex with n8n (automation workflows)"
```

This will start Cortex with n8n:
- **Web UI**: http://localhost:8080
- **n8n Workflows**: http://localhost:5678
- **Telegram Bot**: Configure via @BotFather on Telegram

See [n8n Integration Guide](documentation/N8N_INTEGRATION.md) for setup instructions.

## 💻 Manual Setup (Alternative)

If you prefer to run without Docker:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Ollama**
   ```bash
   # Follow Ollama installation instructions from https://ollama.ai/
   # Run the Ollama service
   ollama serve
   ```

3. **Install OCR Dependencies (Optional)**
   ```bash
   pip install pytesseract pdf2image pillow
   brew install tesseract poppler  # For macOS
   # See documentation/OCR_SETUP.md for other OS instructions
   ```

3. **Add Documents**
   - Place PDF files in the `data/documents` directory

4. **Run the Application**
   ```bash
   # Start the Web Interface
   python api.py
   
   # OR start the Streamlit Interface
   streamlit run app.py
   ```

## 🔧 System Architecture

```
Cortex/
├── app.py                     # Main Streamlit application
├── api.py                     # Alternative web interface (HTML/CSS/JavaScript)
├── docker-entrypoint.sh       # Docker container startup script
├── docker-compose.yml         # Container orchestration configuration
├── docker-compose.gpu.yml     # GPU support configuration
├── docker-compose.n8n.yml     # n8n automation service (optional)
├── Dockerfile                 # Container definition
├── run_docker.sh              # Docker helper script
├── src/
│   ├── document_processor.py  # PDF processing and extraction with OCR
│   ├── chunking.py            # Semantic text chunking
│   ├── retriever.py           # Hybrid retrieval system
│   ├── llm_handler.py         # LLM integration and prompts
│   ├── evaluator.py           # Evaluation framework
│   ├── preload_models.py      # Model preloading script
│   ├── utils.py               # Utility functions
│   ├── agent/                 # Agentic RAG components
│   │   ├── orchestrator.py    # Main agentic orchestrator
│   │   ├── query_analyzer.py  # Query analysis
│   │   └── execution_engine.py # Tool execution engine
│   ├── tools/                 # RAG tools
│   │   ├── semantic_search_tool.py
│   │   ├── keyword_search_tool.py
│   │   ├── comparison_tool.py
│   │   ├── summarization_tool.py
│   │   ├── calculator_tool.py
│   │   └── web_search_tool.py # n8n-powered web search
│   └── citation_enhancer.py   # Enhanced citations with page numbers
├── data/
│   ├── documents/             # PDF documents for auto-loading
│   ├── vectorstore/           # Chroma vector database
│   ├── models_cache/          # Hugging Face model cache
│   └── chroma_cache/          # ChromaDB ONNX model cache
├── config/
│   └── settings.py            # Configuration settings
├── documentation/             # Detailed documentation files
│   ├── N8N_INTEGRATION.md     # n8n setup and usage guide
│   └── ...
├── n8n-workflows/             # Pre-built n8n workflows
│   ├── 01-web-search-tool.json
│   ├── 02-telegram-bot.json
│   └── README.md
├── tests/                     # Testing and diagnostic tools
└── web/                       # Web UI assets (HTML/CSS/JS)
```

## 📊 Performance Optimization

### Embedding Model Caching

Cortex pre-downloads and caches embedding models to improve startup and query time:

- Models are stored in `./data/models_cache/`
- ONNX optimized versions are kept in `./data/chroma_cache/onnx_models/`

### LLM Selection

Choose the right LLM based on your hardware:
- **High-end systems**: Use larger models like `llama3.2:3b` (default)
- **Low-resource systems**: Switch to `phi3:mini` for faster responses (option 5 in the run_docker.sh menu)

## 🔍 Advanced Features

### Agentic RAG System
- **Intelligent Tool Selection**: Automatically chooses the best tools for each query
- **Multi-Step Reasoning**: Chains multiple tools for complex queries
- **Enhanced Citations**: Page numbers, excerpts, and confidence scores
- **Reasoning Traces**: See which tools were used and why

Switch between modes in the Web UI:
- **Traditional RAG**: Linear pipeline (retrieve → generate)
- **Agentic RAG**: Dynamic tool selection with reasoning

### n8n Workflow Automation
- **Web Search Integration**: Augments internal docs with external knowledge
- **Telegram Bot**: Chat with Cortex via Telegram
- **Low-Code Extensibility**: Create custom workflows without coding
- See [n8n Integration Guide](documentation/N8N_INTEGRATION.md) for setup

### Auto-Loading Documents
- Documents placed in the `data/documents` directory are automatically loaded when the app starts
- Configure auto-loading behavior in `config/settings.py`:
  ```python
  AUTO_LOAD_DOCUMENTS = True  # Enable/disable auto-loading
  AUTO_LOAD_SKIP_EXISTING = True  # Skip already processed documents
  ```

### OCR Support for Problematic PDFs
- OCR (Optical Character Recognition) processing for difficult PDFs
- Automatically detects when a PDF needs OCR and applies it
- Perfect for PDFs saved from websites that have selectable text but don't parse correctly
- See [OCR Setup Guide](documentation/OCR_SETUP.md) for detailed setup instructions

### PDF Diagnostic Tool
- Use `tests/check_pdf.py` to diagnose problematic PDFs:
  ```bash
  python tests/check_pdf.py path/to/document.pdf
  ```
- Identifies which extraction method works best for each document
- Determines if OCR processing is recommended

## 🛠️ Troubleshooting Common Issues

### 1. Timeout Error During Query Processing

**Symptom**: Requests timeout with error: "Error generating response: Read timed out."

**Solution**:
- Switch to a smaller LLM model through option 5 in the run_docker.sh script
- Restart the containers to apply changes

### 2. Document Loading Issues

**Symptom**: Documents fail to load or extract properly

**Solution**:
- Check the format of your PDF
- Run diagnostic tool: `python tests/check_pdf.py path/to/document.pdf`
- Enable OCR for problematic documents

### 3. Ollama Connection Issues

**Symptom**: Error connecting to Ollama service

**Solution**:
- For Docker: Ensure the Ollama container is running (`docker ps`)
- For manual setup: Make sure Ollama is running (`ollama serve`)
- See [Environment Setup Guide](documentation/ENVIRONMENT_SETUP.md) for details on connection configuration

For more troubleshooting tips, see the [Full Documentation](documentation/DOCUMENTATION.md#troubleshooting).

## 📚 Documentation

Comprehensive documentation is available in the `documentation` folder:

- [Complete System Documentation](documentation/SYSTEM_DOCUMENTATION.md)
- [Complete User Guide](documentation/USER_GUIDE.md)
- [Docker Setup Guide](documentation/DOCKER.md)
- [n8n Integration Guide](documentation/N8N_INTEGRATION.md)
- [Environment Setup Guide](documentation/ENVIRONMENT_SETUP.md)
- [OCR Setup Instructions](documentation/OCR_SETUP.md)
- [Full Technical Documentation](documentation/DOCUMENTATION.md)

## 📋 Technology Stack

- **Document Processing**: PyPDF2, PyMuPDF, pdfplumber, Tesseract OCR
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB
- **LLM**: Ollama (Llama 3.2 3B)
- **Agentic System**: Custom tool orchestration with reasoning
- **Automation**: n8n (workflow automation platform)
- **Frontend**: Streamlit, HTML/CSS/JavaScript
- **Backend**: Python FastAPI
- **Containers**: Docker, Docker Compose
- **External APIs**: DuckDuckGo (web search), Telegram Bot API

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Developed with ❤️ by Fakhrul Fauzi.
