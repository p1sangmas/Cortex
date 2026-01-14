# Cortex User Guide

## Introduction

Welcome to Cortex, an AI-powered document assistant that helps you extract insights from your PDF documents. This guide will walk you through setting up and using Cortex, with no advanced technical knowledge required.

## What is Cortex?

Cortex is a privacy-focused tool that allows you to:
- Upload PDF documents
- Ask questions about those documents in plain English
- Get accurate answers with citations to the source documents
- All without sending your data to external services or APIs

## Quick Setup Guide

### Option 1: Using Docker (Recommended)

Docker is a tool that makes it easy to run applications in isolated containers. This is the simplest way to get Cortex running on any computer.

1. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
   - Follow the installation instructions for your operating system
   - Start Docker Desktop after installation

2. **Download Cortex**
   - Download the Cortex project as a ZIP file or clone it using Git
   - Extract to a folder of your choice

3. **Run the helper script**
   - Open a terminal/command prompt in the Cortex folder
   - Run: `chmod +x run_docker.sh` (to make the script executable)
   - Run: `./run_docker.sh` (on macOS/Linux) or `bash run_docker.sh` (on Windows)
   - Select option 1 from the menu to start Cortex

4. **Access the application**
   - Open your web browser
   - Go to: http://localhost:8080

### Option 2: Manual Setup (For Python Users)

If you're comfortable with Python, you can run Cortex directly:

1. Install Python 3.9 or newer
2. Install dependencies: `pip install -r requirements.txt`
3. Install OCR dependencies (optional):
   - macOS: `brew install tesseract poppler`
   - Windows: Download and install Tesseract and Poppler (see OCR_SETUP.md)
4. Run: `python api.py` or `streamlit run app.py`

## Using Cortex

### Step 1: Add Documents

There are two ways to add documents:

#### Method A: Direct Upload in the Web Interface
1. Go to http://localhost:8080
2. Click the "Upload" button in the sidebar
3. Select PDF files from your computer
4. Wait for the processing to complete (you'll see a success message)

#### Method B: Add Files to the Documents Folder
1. Navigate to the `data/documents` folder in your Cortex installation
2. Copy your PDF files into this folder
3. Restart Cortex or use the "Reload Documents" option in the interface

### Step 2: Ask Questions

Now that your documents are loaded, you can start asking questions:

1. Type your question in the input field
2. Click "Ask" or press Enter
3. Wait for the response (usually takes 5-15 seconds)

**Example Questions:**
- "What is the main focus of the annual report?"
- "Summarize the key findings from the technical document."
- "What are the key statistics mentioned in the quarterly report?"
- "Explain the methodology described in the research paper."

### Step 3: Interpret Results

The system will return:

- **The Answer**: A comprehensive response to your question
- **Source Citations**: References to the specific documents where information was found (e.g., [Source: Annual Report 2023])
- **Confidence Score**: An indicator of how confident the system is about the answer

## Features

### 1. Document Preparation

Cortex can help you prepare for interviews by extracting key information:

- Upload job descriptions and candidate resumes
- Ask questions like:
  - "What skills from the job description does the candidate have?"
  - "Summarize the candidate's experience relevant to this role."
  - "What qualifications from the job description are not mentioned in the resume?"

### 2. Research and Analysis

Use Cortex to research companies or industries:

- Upload company annual reports, press releases, or industry research
- Ask questions like:
  - "What are the company's main revenue streams?"
  - "What challenges is the industry facing according to the report?"
  - "Summarize the growth strategy mentioned in the annual report."

### 3. Interview Preparation

Prepare for interviews efficiently:

- Upload candidate materials and job specifications
- Ask questions like:
  - "Generate 5 technical questions based on the required skills in the job description."
  - "What achievements in the candidate's resume should I ask for more details about?"
  - "Suggest topics for discussion based on the candidate's previous projects."

## Advanced Features

### Switching to a Faster Model

If you find the responses are taking too long:

1. Run `./run_docker.sh`
2. Select option 5 (Switch to a faster model)
3. Choose option 2 (phi3:mini) or another lightweight model
4. Confirm the restart when prompted

### OCR Support

Cortex can process scanned documents or PDFs with embedded images:

1. Ensure OCR dependencies are installed (see OCR_SETUP.md)
2. Upload your document normally - the system will automatically use OCR when needed

## Troubleshooting

### Common Issues

#### The system is slow to respond
- Try switching to a smaller model (phi3:mini) using option 5 in run_docker.sh
- Consider using a computer with more RAM or a GPU

#### Upload fails or documents aren't processed correctly
- Check if your PDF is scanned or has special formatting
- Try using the diagnostic tool: `python tests/check_pdf.py path/to/document.pdf`

#### Docker isn't starting correctly
- Make sure Docker Desktop is running
- Check if you have enough disk space and memory
- Try restarting Docker Desktop

## Getting Help

If you encounter issues:

1. Check the logs: 
   - Run `./run_docker.sh` and select option 3 (View logs)
   - Look for error messages that may indicate what's wrong

2. Restart the system:
   - Run `./run_docker.sh` and select option 2 (Stop Cortex)
   - Then select option 1 to start it again

3. Reset and rebuild (last resort):
   - Run `./run_docker.sh` and select option 6 (Reset and rebuild)
   - This will recreate all containers from scratch

## Privacy and Data Security

Cortex processes all data locally on your computer:
- Your documents never leave your machine
- No data is sent to external APIs or servers
- The AI models run entirely on your local computer

This ensures complete confidentiality of your sensitive recruitment documents and candidate information.

## Next Steps

As you become more familiar with Cortex, you might want to:

- Explore the configuration options in `config/settings.py`
- Try the Streamlit interface by running `streamlit run app.py`
- Experiment with different question formats to get the most useful information

## System Requirements

- **Minimum**: 4GB RAM, dual-core CPU, 10GB free disk space
- **Recommended**: 8GB RAM, quad-core CPU, 20GB free disk space
- **For best performance**: NVIDIA GPU with 4GB+ VRAM

---

We hope you find Cortex useful for your recruitment workflows! If you have questions or feedback, please reach out to the development team.
