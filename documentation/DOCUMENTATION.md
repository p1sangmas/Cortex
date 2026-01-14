# Cortex: Comprehensive Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Technical Stack](#technical-stack)
5. [Getting Started](#getting-started)
   - [Docker Setup](#docker-setup)
   - [Manual Setup](#manual-setup)
6. [User Guide](#user-guide)
   - [Adding Documents](#adding-documents)
   - [Asking Questions](#asking-questions)
   - [Understanding Responses](#understanding-responses)
   - [Advanced Features](#advanced-features)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)
9. [Development Notes](#development-notes)
10. [Future Roadmap](#future-roadmap)
11. [Appendix](#appendix)

## Project Overview

Cortex is an AI-powered knowledge base assistant that allows users to upload PDF documents and ask natural language questions about their content. The system uses state-of-the-art language models and document retrieval techniques to provide accurate, contextual answers with source citations. Cortex is designed to run entirely locally, ensuring privacy and data security.

The system is built as a containerized application with Docker, making it easy to deploy across different operating systems and environments. It features two interfaces: a Streamlit-based UI and a more traditional HTML/CSS/JavaScript web interface.

## Features

- **📄 Multi-format PDF Processing**: Robust text extraction with fallback mechanisms and OCR support
- **📁 Automatic Document Loading**: Ability to auto-load PDFs from the documents directory
- **🔍 Hybrid Retrieval System**: Combines semantic similarity with keyword matching
- **🤖 Local AI Integration**: Uses Ollama (Llama 3.2 3B) for privacy-preserving responses
- **💬 Conversation Memory**: Maintains context across multiple questions
- **📊 Source Attribution**: Always shows which documents informed each answer
- **⚡ Real-time Evaluation**: Built-in quality metrics inspired by RAGAS
- **🎯 Adaptive Query Processing**: Routes different query types to specialized chains
- **📈 Analytics Dashboard**: Performance metrics and user feedback analysis
- **🔒 Privacy-First**: All processing happens locally - no external APIs

## System Architecture

Cortex follows a containerized architecture with two main components:

1. **Cortex Container**: Handles document processing, embedding generation, vector storage, and hosts both the API and web interface.
2. **Ollama Container**: Provides the LLM (Large Language Model) capabilities.

The system uses a hybrid vector + keyword retrieval system to find relevant document chunks, which are then fed to the LLM to generate accurate responses.

### Component Workflow

1. **Document Ingestion**:
   - PDFs are processed using multiple extraction methods (PyPDF2, PyMuPDF, pdfplumber)
   - OCR fallback for problematic PDFs (using Tesseract)
   - Text is chunked semantically for optimal retrieval

2. **Vector Storage**:
   - Document chunks are embedded using Sentence Transformers
   - Embeddings are stored in a local ChromaDB vector database

3. **Query Processing**:
   - User questions are embedded using the same model
   - Hybrid retrieval combines semantic similarity and keyword matching
   - Retrieved chunks are ranked and filtered

4. **Answer Generation**:
   - Top document chunks are formatted into a prompt
   - Ollama LLM generates a response with source citations
   - Response is evaluated for quality metrics

## Technical Stack

- **Document Processing**: PyPDF2, PyMuPDF, pdfplumber, Tesseract OCR
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB
- **LLM**: Ollama (Llama 3.2 3B)
- **Frontend**: HTML/CSS/JavaScript, Streamlit
- **Orchestration**: Docker, Docker Compose
- **Evaluation**: RAGAS-inspired framework
- **Backend**: Python FastAPI

## Getting Started

### Docker Setup (Recommended)

The easiest way to get started with Cortex is through Docker. This approach works on any operating system and handles all dependencies.

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- At least 4GB of free RAM (8GB+ recommended)
- At least 10GB of free disk space

#### Quick Start

1. **Clone or download the project**

2. **Run the setup script**:
   ```bash
   chmod +x run_docker.sh
   ./run_docker.sh
   ```

3. **Select option 1** from the menu to start Cortex

4. **Access the interfaces**:
   - Web UI: http://localhost:8080
   - API: http://localhost:8000/api

#### GPU Support

For systems with NVIDIA GPUs, Cortex can leverage GPU acceleration:

1. The `run_docker.sh` script will automatically detect compatible NVIDIA GPUs
2. Ensure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed

### Manual Setup

If you prefer not to use Docker, you can set up Cortex manually:

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install OCR dependencies** (optional but recommended):
   - See [OCR Setup](#ocr-setup) for platform-specific instructions

3. **Start the application**:
   - For Streamlit interface: `streamlit run app.py`
   - For web interface: `python api.py`

## User Guide

### Adding Documents

There are two ways to add documents to Cortex:

#### Method 1: Auto-loading from Directory

1. Place PDF files in the `data/documents` directory
2. Start or restart Cortex
3. The system will automatically detect and process new documents

#### Method 2: Upload via Web Interface

1. Navigate to the web interface (http://localhost:8080)
2. Click the "Upload" button in the sidebar
3. Select one or more PDF files from your computer
4. Wait for processing to complete (progress will be displayed)

### Asking Questions

Once you have documents loaded, you can ask questions in natural language:

1. Type your question in the input box
2. Click "Ask" or press Enter
3. The system will retrieve relevant information and generate an answer
4. Sources will be cited alongside the answer

**Example Questions:**
- "What is the main focus of the project described in the technical report?"
- "Summarize the key findings from the quarterly report."
- "Compare the investment strategies mentioned in documents A and B."

### Understanding Responses

Cortex responses include:

1. **Answer Text**: The main response to your query
2. **Source Citations**: References to specific documents where information was found
3. **Confidence Score**: An indicator of the system's confidence in the answer
4. **Reasoning Path**: (Advanced view) How the system arrived at its conclusion

### Advanced Features

#### PDF Diagnostics

If you're having issues with specific PDFs, use the diagnostic tool:

```bash
python tests/check_pdf.py path/to/your/document.pdf
```

This will analyze the PDF and recommend the best extraction approach.

#### Switching LLM Models

To use a different Ollama model:

1. Run `./run_docker.sh`
2. Select option 5 to switch models
3. Choose from the available options or specify a custom model

#### OCR Setup

For documents requiring OCR processing:

1. Install Tesseract OCR and Poppler:
   - **macOS**: `brew install tesseract poppler`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr poppler-utils`
   - **Windows**: Install from the official repositories (see OCR_SETUP.md)
   
2. Install Python packages:
   ```bash
   pip install pytesseract pdf2image pillow
   ```

## Performance Optimization

### Embedding Model Caching

Cortex pre-downloads and caches embedding models to improve startup and query time:

- Models are stored in `./data/models_cache/`
- ONNX optimized versions are kept in `./data/chroma_cache/onnx_models/`

### LLM Selection

Choose the right LLM based on your hardware:
- **High-end systems**: Use larger models like `llama3.2:3b` (default)
- **Low-resource systems**: Switch to `phi3:mini` for faster responses

### Resource Allocation

Adjust Docker resource limits based on your system:
- Minimum: 4GB RAM
- Recommended: 8GB RAM
- For GPU systems: Enable GPU acceleration

## Troubleshooting

### Common Issues

#### 1. Timeout Error During Query Processing

**Symptom**: Requests timeout with error: "Error generating response: HTTPConnectionPool(host='ollama', port=11434): Read timed out. (read timeout=60)"

**Solution**:
- Switch to a smaller LLM model through option 5 in the run_docker.sh script
- Restart the containers to apply changes

#### 2. Document Loading Issues

**Symptom**: Documents fail to load or extract properly

**Solution**:
- Check the format of your PDF
- Run diagnostic tool: `python tests/check_pdf.py path/to/document.pdf`
- Enable OCR for problematic documents

#### 3. Web Interface Not Accessible

**Symptom**: Cannot access the web interface at http://localhost:8080

**Solution**:
- Verify containers are running: `docker compose ps`
- Check logs: `docker compose logs cortex`
- Ensure ports aren't in use by other applications

## Development Notes

### Project Structure

```
Cortex/
├── app.py                     # Main Streamlit application
├── api.py                     # Alternative web interface API
├── docker-entrypoint.sh       # Docker container startup script
├── Dockerfile                 # Main container definition
├── docker-compose.yml         # Container orchestration
├── docker-compose.gpu.yml     # GPU support configuration
├── run_docker.sh              # Helper script for Docker management
├── src/
│   ├── document_processor.py  # PDF processing and extraction with OCR
│   ├── chunking.py            # Semantic text chunking
│   ├── retriever.py           # Hybrid retrieval system
│   ├── llm_handler.py         # LLM integration and prompts
│   ├── evaluator.py           # Evaluation framework
│   ├── preload_models.py      # Model preloading script
│   └── utils.py               # Utility functions
├── data/
│   ├── documents/             # PDF document storage
│   ├── vectorstore/           # Chroma vector database
│   ├── models_cache/          # Hugging Face model cache
│   └── chroma_cache/          # ChromaDB ONNX model cache
├── config/
│   └── settings.py            # Configuration settings
├── web/                       # Web UI files (HTML, CSS, JS)
└── tests/                     # Testing and diagnostic tools
```

## Future Roadmap

Planned enhancements for future versions:

1. **Multilingual Support**: Processing documents in multiple languages
2. **Document Update Detection**: Automatically detecting and processing updated documents
3. **Enhanced Visualization**: Adding charts and diagrams for data-heavy responses
4. **Multi-User Support**: Account-based access with personalized collections

## Appendix

### System Requirements

#### Minimum Requirements:
- 4GB RAM
- Dual-core CPU
- 10GB free disk space

#### Recommended Requirements:
- 8GB RAM
- Quad-core CPU
- 20GB free disk space
- NVIDIA GPU with 4GB+ VRAM (for GPU acceleration)

### Configuration Options

Edit `config/settings.py` to customize:

- `EMBEDDING_MODEL`: The model used for document embeddings
- `OLLAMA_MODEL`: The LLM model used for responses
- `MAX_CHUNK_SIZE`: Maximum token size for document chunks
- `TOP_K_DOCUMENTS`: Number of document chunks to retrieve
- `OCR_ENABLED`: Enable/disable OCR processing
