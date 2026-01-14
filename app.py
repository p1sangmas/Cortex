"""
Cortex - AI-Powered Knowledge Base Assistant
Main Streamlit Application
"""

import streamlit as st
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import os

# Import our modules
from src.document_processor import DocumentProcessor, MetadataEnhancer
from src.chunking import SemanticChunker
from src.retriever import HybridRetriever
from src.llm_handler import AdaptiveQAChain
from src.evaluator import RAGEvaluator, FeedbackProcessor
from src.utils import (
    setup_logging, timing_decorator, generate_session_id,
    StreamlitUtils, ValidationUtils, safe_execute
)
from config.settings import PAGE_TITLE, PAGE_ICON

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class CortexApp:
    """Main application class for Cortex Knowledge Base Assistant"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.metadata_enhancer = MetadataEnhancer()
        self.chunker = SemanticChunker()
        self.retriever = HybridRetriever()
        self.qa_chain = AdaptiveQAChain()
        self.evaluator = RAGEvaluator()
        self.feedback_processor = FeedbackProcessor()
        
        # Initialize session state
        self._init_session_state()
        
        # Auto-load documents from the documents directory
        try:
            from config.settings import AUTO_LOAD_DOCUMENTS
            if AUTO_LOAD_DOCUMENTS:
                self._auto_load_documents()
        except ImportError:
            logger.warning("Auto-load documents setting not found. Skipping auto-load.")
            pass
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = generate_session_id()
        
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        if 'documents_processed' not in st.session_state:
            st.session_state.documents_processed = False
        
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        
        if 'last_response' not in st.session_state:
            st.session_state.last_response = None
            
        if 'processed_file_info' not in st.session_state:
            st.session_state.processed_file_info = []
            
        # UI state variables to prevent reruns
        if 'show_metrics' not in st.session_state:
            st.session_state.show_metrics = False
            
        if 'feedback_rating' not in st.session_state:
            st.session_state.feedback_rating = 3
            
        if 'feedback_text' not in st.session_state:
            st.session_state.feedback_text = ""
    
    def run(self):
        """Main application entry point"""
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main header
        st.title("🧠 Cortex")
        st.subheader("AI-Powered Knowledge Base Assistant")
        
        # Sidebar
        self._render_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Analytics", "⚙️ Settings", "ℹ️ About"])
        
        with tab1:
            self._render_chat_interface()
        
        with tab2:
            self._render_analytics_dashboard()
        
        with tab3:
            self._render_settings()
        
        with tab4:
            self._render_about()
    
    def _render_sidebar(self):
        """Render the sidebar with document management"""
        st.sidebar.header("📁 Document Management")
        
        # Upload documents
        uploaded_files = st.sidebar.file_uploader(
            "Upload PDF Documents",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload PDF documents to add to your knowledge base"
        )
        
        if uploaded_files:
            if st.sidebar.button("Process Documents", type="primary"):
                self._process_uploaded_documents(uploaded_files)
        
        # Display current collection info
        collection_info = self.retriever.get_collection_info()
        if collection_info:
            st.sidebar.subheader("📚 Knowledge Base Status")
            st.sidebar.metric("Documents Indexed", collection_info.get('document_count', 0))
            st.sidebar.metric("Embedding Model", collection_info.get('embedding_model', 'Unknown'))
        
        # Display uploaded documents
        if st.session_state.processed_file_info:
            st.sidebar.subheader("📄 Processed Documents")
            
            for i, file_info in enumerate(st.session_state.processed_file_info):
                # Add indicator for auto-loaded documents
                auto_loaded = file_info.get('auto_loaded', False)
                icon = "🔄" if auto_loaded else "📄"
                
                with st.sidebar.expander(f"{icon} {file_info['filename']}"):
                    st.write(f"**Size:** {file_info['size'] / 1024:.1f} KB")
                    st.write(f"**Chunks:** {file_info['chunks']}")
                    st.write(f"**Extraction:** {file_info['extraction_method']}")
                    st.write(f"**Processed:** {file_info['timestamp']}")
                    if auto_loaded:
                        st.write("**Source:** Auto-loaded from documents directory")
                    
                    if st.button(f"Remove this document", key=f"remove_{i}"):
                        if st.session_state.processed_file_info:
                            # We can't selectively remove documents from the vector DB easily
                            # So we'll warn the user about this limitation
                            st.warning("Individual document removal requires reprocessing. Please use 'Clear Knowledge Base' instead.")
        
        # Collection management
        st.sidebar.subheader("🗂️ Collection Management")
        
        if st.sidebar.button("Clear Knowledge Base", type="secondary"):
            if st.sidebar.checkbox("I understand this will delete all documents"):
                self._clear_knowledge_base()
        
        # System status
        st.sidebar.subheader("🔧 System Status")
        
        # Check Ollama status
        ollama_status = self.qa_chain.ollama.is_available()
        status_color = "🟢" if ollama_status else "🔴"
        status_text = "Available" if ollama_status else "Unavailable"
        st.sidebar.write(f"{status_color} Ollama: {status_text}")
        
        # Check OCR status
        from src.document_processor import OCR_AVAILABLE
        ocr_status_color = "🟢" if OCR_AVAILABLE else "🔴"
        ocr_status_text = "Available" if OCR_AVAILABLE else "Unavailable"
        st.sidebar.write(f"{ocr_status_color} OCR Support: {ocr_status_text}")
        
        if not OCR_AVAILABLE:
            if st.sidebar.button("How to enable OCR"):
                st.sidebar.info("See documentation/OCR_SETUP.md for instructions on enabling OCR support for better PDF processing.")
        
        if not ollama_status:
            st.sidebar.warning("⚠️ Ollama is not running. Please start Ollama with the llama3.1:8b model.")
            if st.sidebar.button("How to install Ollama"):
                st.sidebar.info("""
                1. Visit https://ollama.ai
                2. Download and install Ollama
                3. Run: `ollama pull llama3.1:8b`
                4. The service should start automatically
                """)
    
    def _render_chat_interface(self):
        """Render the main chat interface"""
        # Check if documents are available
        collection_info = self.retriever.get_collection_info()
        if collection_info.get('document_count', 0) == 0:
            st.warning("📄 No documents in knowledge base. Please upload some documents in the sidebar to get started.")
            return
        
        # Chat history display
        st.subheader("💬 Conversation")
        
        # Display conversation history
        if st.session_state.conversation_history:
            for i, message in enumerate(st.session_state.conversation_history):
                if message['role'] == 'user':
                    st.chat_message("user").write(message['content'])
                else:
                    st.chat_message("assistant").write(message['content'])
        
        # Query input
        query = st.chat_input("Ask a question about your documents...")
        
        if query:
            # Validate query
            is_valid, validation_message = ValidationUtils.validate_query(query)
            if not is_valid:
                st.error(validation_message)
                return
            
            # Display user message
            st.chat_message("user").write(query)
            st.session_state.conversation_history.append({
                'role': 'user',
                'content': query
            })
            
            # Process query and generate response
            with st.chat_message("assistant"):
                self._process_query(query)
    
    @timing_decorator
    def _process_query(self, query: str):
        """Process user query and generate response"""
        try:
            # Show processing status
            with st.status("Processing your query...", expanded=True) as status:
                st.write("🔍 Searching documents...")
                
                # Retrieve relevant documents
                start_time = time.time()
                context_documents = self.retriever.retrieve(query)
                retrieval_time = time.time() - start_time
                
                if not context_documents:
                    st.error("No relevant documents found for your query.")
                    return
                
                st.write(f"✅ Found {len(context_documents)} relevant documents")
                st.write("💭 Generating response...")
                
                # Generate response
                start_time = time.time()
                response = self.qa_chain.process_query(
                    query, 
                    context_documents, 
                    st.session_state.conversation_history[-10:]  # Last 10 messages
                )
                generation_time = time.time() - start_time
                
                status.update(label="✅ Response generated!", state="complete")
            
            # Display response
            if response.get('error'):
                StreamlitUtils.display_error_message(response['error'])
                return
            
            answer = response.get('answer', 'No answer generated.')
            st.write(answer)
            
            # Store response in conversation history
            st.session_state.conversation_history.append({
                'role': 'assistant',
                'content': answer
            })
            st.session_state.last_response = response
            
            # Add visual divider
            st.divider()
            
            # Create 3 columns for better layout
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display confidence in its own container with clear styling
                StreamlitUtils.display_confidence_indicator(response.get('confidence', 'unknown'))
                
                # Evaluation metrics toggle using session state to prevent reruns
                def toggle_metrics():
                    st.session_state.show_metrics = not st.session_state.show_metrics
                
                st.button(
                    "Toggle Evaluation Metrics", 
                    on_click=toggle_metrics,
                    key="toggle_metrics_button"
                )
                if st.session_state.show_metrics:
                    st.write("✅ Evaluation metrics enabled")
                else:
                    st.write("❌ Evaluation metrics disabled")
            
            with col2:
                # Display sources in its own container with clear styling
                StreamlitUtils.display_sources(response.get('sources', []))
            
            # Evaluation metrics (if enabled) - placed below the confidence/sources for better layout
            if st.session_state.show_metrics:
                st.divider()
                total_time = retrieval_time + generation_time
                evaluation_results = self.evaluator.evaluate_response(
                    query, response, context_documents, response_time=total_time
                )
                StreamlitUtils.display_metrics(evaluation_results, "Response Quality Metrics")
            
            # Add visual divider before feedback section
            st.divider()
            
            # Feedback collection
            self._render_feedback_section(query, answer)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            st.error("An error occurred while processing your query. Please try again.")
    
    def _render_feedback_section(self, query: str, answer: str):
        """Render feedback collection section"""
        st.subheader("📝 Feedback")
        
        with st.container():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Update the rating without causing a rerun
                def update_rating(val):
                    st.session_state.feedback_rating = val
                
                # Show stars corresponding to current rating
                stars = "⭐" * st.session_state.feedback_rating
                st.markdown(f"### {stars}")
                
                # Use buttons for rating selection instead of slider
                rating_cols = st.columns(5)
                for i, col in enumerate(rating_cols, 1):
                    with col:
                        if st.button(f"{i}", key=f"rate_{i}", 
                                    help=f"Rate {i} stars", 
                                    on_click=update_rating, args=(i,)):
                            pass
            
            with col2:
                # Update the feedback text without causing a rerun
                def update_feedback(val):
                    st.session_state.feedback_text = val
                    
                # Display the current feedback text
                st.text_area(
                    "Any corrections or suggestions?",
                    value=st.session_state.feedback_text,
                    placeholder="Optional: Provide feedback to help improve responses...",
                    key="feedback_text_area",
                    on_change=update_feedback,
                    args=(st.session_state.feedback_text,)
                )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            def submit_feedback():
                self.feedback_processor.process_user_feedback(
                    query, answer, st.session_state.feedback_rating, st.session_state.feedback_text, 
                    st.session_state.session_id
                )
                st.session_state.feedback_submitted = True
                
            if 'feedback_submitted' not in st.session_state:
                st.session_state.feedback_submitted = False
                
            if st.button("Submit Feedback", type="primary", on_click=submit_feedback):
                pass
                
            if st.session_state.feedback_submitted:
                st.success("Thank you for your feedback!")
                # Reset the submitted state after displaying the message
                st.session_state.feedback_submitted = False
    
    def _process_uploaded_documents(self, uploaded_files: List[Any]):
        """Process uploaded PDF documents"""
        if not uploaded_files:
            return
        
        # Check OCR availability and inform users
        from src.document_processor import OCR_AVAILABLE
        if not OCR_AVAILABLE:
            st.info("📌 Advanced PDF processing (OCR) is not enabled. Some PDFs might not be processed correctly. "
                   "To enable OCR support, install additional dependencies: `pip install pytesseract pdf2image pillow`\n\n"
                   "Note: You'll also need to install Tesseract OCR on your system.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        processed_documents = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Validate file
                is_valid, validation_message = ValidationUtils.validate_pdf_file(uploaded_file)
                if not is_valid:
                    st.error(f"❌ {uploaded_file.name}: {validation_message}")
                    continue
                
                # Update progress
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Extract text
                    text, method, metadata = self.document_processor.extract_with_fallback(tmp_file_path)
                    
                    # Update metadata with file info - original filename is critical for citations
                    filename = uploaded_file.name
                    # Remove any suffix for cleaner display
                    display_name = filename
                    if display_name.lower().endswith('.pdf'):
                        display_name = display_name[:-4]
                    
                    metadata.update({
                        'original_filename': filename,
                        'display_name': display_name,
                        'file_size': uploaded_file.size,
                        'extraction_method': method,
                        'title': display_name
                    })
                    
                    # Chunk text
                    chunks = self.chunker.chunk_by_semantic_similarity(text)
                    
                    # Enhance with metadata
                    enhanced_chunks = self.metadata_enhancer.enhance_chunks(chunks, metadata)
                    
                    processed_documents.extend(enhanced_chunks)
                    
                    # Save file info to session state
                    file_info = {
                        'filename': uploaded_file.name,
                        'size': uploaded_file.size,
                        'chunks': len(chunks),
                        'extraction_method': method,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.processed_file_info.append(file_info)
                    
                    st.success(f"✅ Processed {uploaded_file.name} ({len(chunks)} chunks)")
                    
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_file_path)
                    
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}")
                st.error(f"❌ Failed to process {uploaded_file.name}: {str(e)}")
        
        # Add documents to retrieval system
        if processed_documents:
            try:
                status_text.text("Adding documents to knowledge base...")
                self.retriever.add_documents(processed_documents)
                st.session_state.documents_processed = True
                st.success(f"🎉 Successfully added {len(processed_documents)} document chunks to knowledge base!")
                
            except Exception as e:
                logger.error(f"Error adding documents to knowledge base: {e}")
                st.error("Failed to add documents to knowledge base. Please try again.")
        
        progress_bar.empty()
        status_text.empty()
    
    def _clear_knowledge_base(self):
        """Clear all documents from the knowledge base"""
        try:
            # First clear the collection
            self.retriever.clear_collection()
            
            # Reset session state
            st.session_state.documents_processed = False
            st.session_state.conversation_history = []
            st.session_state.processed_file_info = []
            
            # Verify the collection is actually empty
            collection_info = self.retriever.get_collection_info()
            doc_count = collection_info.get('document_count', 0)
            
            if doc_count > 0:
                logger.warning(f"After clearing, collection still has {doc_count} documents. Trying hard reset.")
                # If documents still exist, try a more forceful approach
                from reset_chroma import reset_chromadb
                reset_chromadb()
                
                # Reinitialize the retriever to ensure a fresh start
                # This recreates the ChromaDB client and collection
                self.retriever = HybridRetriever()
            
            # Force a full reload of the page to reset all counters and state
            st.success("🗑️ Knowledge base cleared successfully!")
            st.rerun()  # This will cause the Streamlit app to fully reload
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
            st.error("Failed to clear knowledge base. Please try again.")
    
    def _render_analytics_dashboard(self):
        """Render analytics and metrics dashboard"""
        st.header("📊 Analytics Dashboard")
        
        # System metrics
        col1, col2, col3 = st.columns(3)
        
        collection_info = self.retriever.get_collection_info()
        
        with col1:
            st.metric("Documents", collection_info.get('document_count', 0))
        
        with col2:
            conversation_count = len(st.session_state.conversation_history) // 2
            st.metric("Conversations", conversation_count)
        
        with col3:
            st.metric("Session ID", st.session_state.session_id)
        
        # Feedback analysis
        st.subheader("📝 Recent Feedback Analysis")
        feedback_analysis = self.feedback_processor.get_feedback_analysis()
        
        if 'error' not in feedback_analysis and feedback_analysis.get('total_feedback', 0) > 0:
            StreamlitUtils.display_metrics(feedback_analysis, "Feedback Metrics")
        else:
            st.info("No feedback data available yet. Users can provide feedback after receiving responses.")
        
        # System information
        st.subheader("🖥️ System Information")
        
        with st.expander("View System Details"):
            from src.utils import get_system_info
            system_info = get_system_info()
            st.json(system_info)
    
    def _render_settings(self):
        """Render settings and configuration"""
        st.header("⚙️ Settings")
        
        # Model settings
        st.subheader("🤖 Model Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Embedding Model", value="all-MiniLM-L6-v2", disabled=True)
            st.text_input("LLM Model", value="llama3.1:8b", disabled=True)
        
        with col2:
            st.slider("Semantic Weight", 0.0, 1.0, 0.7, disabled=True)
            st.slider("Keyword Weight", 0.0, 1.0, 0.3, disabled=True)
        
        # Chunking settings
        st.subheader("✂️ Text Chunking")
        st.slider("Max Chunk Size", 500, 2000, 1000, disabled=True)
        st.slider("Chunk Overlap", 50, 500, 200, disabled=True)
        
        # Advanced settings
        st.subheader("🔧 Advanced Settings")
        
        # Auto-loading settings
        from config.settings import AUTO_LOAD_DOCUMENTS, AUTO_LOAD_SKIP_EXISTING
        
        st.checkbox("Auto-load documents from data/documents directory", 
                   value=AUTO_LOAD_DOCUMENTS, 
                   disabled=True, 
                   help="Enable/disable in settings.py")
        
        st.checkbox("Skip existing documents when auto-loading", 
                   value=AUTO_LOAD_SKIP_EXISTING, 
                   disabled=True,
                   help="Enable/disable in settings.py")
        
        st.info("To change auto-loading settings, edit the settings.py file and restart the application.")
        
        st.divider()
        
        if st.button("Export Conversation History"):
            if st.session_state.conversation_history:
                import json
                conversation_json = json.dumps(st.session_state.conversation_history, indent=2)
                st.download_button(
                    "Download Conversation",
                    conversation_json,
                    file_name=f"conversation_{st.session_state.session_id}.json",
                    mime="application/json"
                )
            else:
                st.info("No conversation history to export.")
        
        if st.button("Clear Conversation History"):
            st.session_state.conversation_history = []
            self.qa_chain.clear_conversation_history()
            st.success("Conversation history cleared!")
    
    def _render_about(self):
        """Render about and help information"""
        st.header("ℹ️ About Cortex")
        
        st.markdown("""
        **Cortex** is an AI-powered knowledge base assistant that transforms your static PDF documents 
        into an interactive, searchable knowledge base. Ask questions in natural language and get 
        contextual answers backed by your organizational documents.
        
        ### 🌟 Key Features
        
        - **Multi-format PDF Processing**: Robust text extraction with fallback mechanisms
        - **Semantic Search**: Intelligent document retrieval using state-of-the-art embeddings
        - **Hybrid Retrieval**: Combines semantic similarity with keyword matching
        - **Local AI**: Uses Ollama for privacy-preserving, local AI inference
        - **Conversation Memory**: Maintains context across multiple questions
        - **Source Attribution**: Always shows which documents informed the answer
        - **Quality Evaluation**: Built-in metrics to assess response quality
        
        ### 🛠️ Technology Stack
        
        - **Document Processing**: PyPDF2, PyMuPDF, pdfplumber
        - **OCR Support** (optional): pytesseract, pdf2image for handling problematic PDFs
        - **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
        - **Vector Database**: ChromaDB
        - **LLM**: Ollama (Llama 3.1 8B)
        - **Frontend**: Streamlit
        - **Evaluation**: Custom RAGAS-inspired framework
        
        ### 🚀 Getting Started
        
        1. **Setup**: Ensure Ollama is running with the `llama3.1:8b` model
        2. **Documents**: Either place PDFs in the `data/documents` folder for auto-loading, or upload via the sidebar
        3. **Process**: For uploaded documents, click "Process Documents" to build your knowledge base
        4. **Query**: Start asking questions about your documents!
        
        ### 💡 Tips for Best Results
        
        - Upload documents with clear, well-formatted text
        - Ask specific questions rather than very broad ones
        - Use the feedback system to help improve response quality
        - Check the confidence indicator to gauge answer reliability
        
        ### 📞 Support
        
        For technical issues or questions, check the system status in the sidebar or 
        review the logs for detailed error information.
        """)
        
        # Quick setup guide
        with st.expander("🔧 Ollama Setup Guide"):
            st.markdown("""
            #### Installing Ollama
            
            1. **Download**: Visit [ollama.ai](https://ollama.ai) and download for your OS
            2. **Install**: Follow the installation instructions
            3. **Pull Model**: Run `ollama pull llama3.1:8b` in your terminal
            4. **Verify**: The model should start automatically
            
            #### Troubleshooting
            
            - **Service not running**: Try `ollama serve` in terminal
            - **Model not found**: Ensure you've pulled the correct model
            - **Memory issues**: The 8B model requires ~8GB RAM
            - **Performance**: Consider using a GPU for faster responses
            """)

    def _auto_load_documents(self):
        """Automatically load documents from the data/documents directory"""
        from config.settings import DOCUMENTS_DIR, AUTO_LOAD_SKIP_EXISTING
        
        # Check if directory exists
        documents_dir = Path(DOCUMENTS_DIR)
        if not documents_dir.exists():
            logger.warning(f"Documents directory {documents_dir} does not exist. Skipping auto-load.")
            return
            
        # Get all PDF files
        pdf_files = list(documents_dir.glob("*.pdf"))
        if not pdf_files:
            logger.info("No PDF files found in documents directory. Skipping auto-load.")
            return
            
        logger.info(f"Auto-loading {len(pdf_files)} documents from {documents_dir}")
        
        # Track existing filenames to avoid duplicates
        existing_filenames = set()
        if AUTO_LOAD_SKIP_EXISTING and st.session_state.processed_file_info:
            existing_filenames = {file_info['filename'] for file_info in st.session_state.processed_file_info}
            
        # Process each PDF file
        processed_documents = []
        
        for pdf_path in pdf_files:
            try:
                # Check if already processed
                filename = pdf_path.name
                if filename in existing_filenames:
                    logger.info(f"Skipping {filename} as it is already processed")
                    continue
                    
                logger.info(f"Auto-loading document: {filename}")
                
                # Extract text
                text, method, metadata = self.document_processor.extract_with_fallback(str(pdf_path))
                
                # Get file size
                file_size = pdf_path.stat().st_size
                
                # Update metadata
                display_name = filename
                if display_name.lower().endswith('.pdf'):
                    display_name = display_name[:-4]
                
                metadata.update({
                    'original_filename': filename,
                    'display_name': display_name,
                    'file_size': file_size,
                    'extraction_method': method,
                    'title': display_name
                })
                
                # Chunk text
                chunks = self.chunker.chunk_by_semantic_similarity(text)
                
                # Enhance with metadata
                enhanced_chunks = self.metadata_enhancer.enhance_chunks(chunks, metadata)
                
                # Add to processed documents
                processed_documents.extend(enhanced_chunks)
                
                # Save file info to session state
                file_info = {
                    'filename': filename,
                    'size': file_size,
                    'chunks': len(chunks),
                    'extraction_method': method,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'auto_loaded': True
                }
                st.session_state.processed_file_info.append(file_info)
                
                logger.info(f"Successfully processed {filename} ({len(chunks)} chunks)")
                
            except Exception as e:
                logger.error(f"Error auto-loading {pdf_path.name}: {e}")
                
        # Add documents to retrieval system
        if processed_documents:
            try:
                self.retriever.add_documents(processed_documents)
                st.session_state.documents_processed = True
                logger.info(f"Successfully auto-loaded {len(processed_documents)} document chunks into knowledge base")
                
            except Exception as e:
                logger.error(f"Error adding auto-loaded documents to knowledge base: {e}")
                
        return len(processed_documents) > 0

def main():
    """Main application entry point"""
    app = CortexApp()
    app.run()

if __name__ == "__main__":
    main()
