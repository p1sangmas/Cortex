# Setting Up OCR Support for Cortex

Cortex now includes OCR (Optical Character Recognition) support for handling PDFs that don't parse correctly with conventional methods. This is particularly useful for PDFs saved from websites or scanned documents.

## Dependencies

To enable OCR functionality, you need to install both Python packages and system dependencies:

### 1. Python Packages

```bash
pip install pytesseract pdf2image pillow
```

### 2. System Dependencies

#### macOS

Install Tesseract OCR and Poppler using Homebrew:

```bash
# Install Homebrew if you don't have it
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract OCR
brew install tesseract

# Install Poppler (required for pdf2image)
brew install poppler
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y poppler-utils
```

#### Windows

1. Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Add Tesseract to your PATH
3. Install poppler for Windows (needed for pdf2image): https://github.com/oschwartz10612/poppler-windows

## Enabling OCR in Cortex

Once dependencies are installed, OCR will automatically be enabled when the application starts. The system will detect when a PDF needs OCR processing and apply it automatically as a fallback.

## Verifying Installation

You can verify that OCR is properly installed by running:

```python
from src.document_processor import OCR_AVAILABLE
print(f"OCR Support: {'Available' if OCR_AVAILABLE else 'Not Available'}")
```

## When OCR is Used

OCR will be used as a fallback in the following scenarios:

1. When conventional PDF text extraction methods produce little or no text
2. When extracted text contains a high percentage of unusual characters (encoding issues)
3. When the text appears to contain PDF-to-web conversion artifacts
4. When text extraction fails validation checks

## Performance Considerations

OCR processing is significantly slower than standard text extraction methods. For large documents, expect longer processing times.
