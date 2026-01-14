"""LLM integration and prompt management for question answering"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import OLLAMA_MODEL, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)

class OllamaHandler:
    """Handler for Ollama LLM integration"""
    
    def __init__(self, model_name: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.chat_url = f"{base_url}/api/chat"
        
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> str:
        """Generate response using Ollama"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_thread": 4  # Utilize multiple threads for generation
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=240  # Increased timeout to 4 minutes for slower hardware
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama generate failed: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error("Ollama response timed out. This could be due to high system load or complex query processing.")
            return "I'm sorry, but the response generation timed out. This might be because the system is under heavy load or the query is particularly complex. Please try again with a simpler query or try later when the system is less busy."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ""

class PromptTemplateManager:
    """Manages different prompt templates for various use cases"""
    
    def __init__(self):
        self.templates = {
            'qa_template': self._build_qa_template(),
            'summarization_template': self._build_summarization_template(),
            'comparison_template': self._build_comparison_template(),
            'extraction_template': self._build_extraction_template()
        }
    
    def get_template(self, template_name: str) -> str:
        """Get a specific template"""
        return self.templates.get(template_name, self.templates['qa_template'])
    
    def _build_qa_template(self) -> str:
        """Build the main Q&A template"""
        return """You are Cortex, an expert AI assistant specializing in organizational knowledge retrieval and analysis. You help users find and understand information from their internal documents.

CONTEXT INFORMATION:
{context}

CONVERSATION HISTORY:
{chat_history}

CURRENT QUESTION: {question}

INSTRUCTIONS:
1. Provide accurate, specific answers based SOLELY on the provided context
2. If information is not available in the context, clearly state "I don't have enough information in the provided documents to answer this question."
3. When citing documents, you MUST ALWAYS use ONLY the original filename without any doc_ID numbers. For example: [Source: Computer Vision Approaches]
4. NEVER cite documents using the format [doc_123], [doc_0], or any numeric document IDs
5. IMPORTANT: Citations must show the actual document title/original filename, not internal document IDs
6. Maintain a professional tone suitable for internal organizational use
7. For ambiguous questions, ask for clarification while providing any partial answers possible
8. If the question requires information from multiple documents, synthesize the information coherently

RESPONSE FORMAT:
- Direct answer to the question
- Supporting evidence directly quoted from documents with proper citations using ONLY the original document title
- Confidence level if uncertain
- Related topics or documents that might be helpful (if applicable)

Remember: Only use information from the provided context. Do not add external knowledge or assumptions.

Answer:"""

    def _build_summarization_template(self) -> str:
        """Build template for document summarization"""
        return """You are Cortex, tasked with creating comprehensive summaries of organizational documents.

DOCUMENT CONTENT:
{context}

SUMMARIZATION REQUEST: {question}

INSTRUCTIONS:
1. Create a clear, structured summary that captures the key points
2. Maintain the document's original intent and tone
3. Organize information logically with bullet points or sections
4. Highlight critical information, deadlines, or action items
5. Keep the summary concise but comprehensive

Provide a well-structured summary:"""

    def _build_comparison_template(self) -> str:
        """Build template for comparing information across documents"""
        return """You are Cortex, analyzing and comparing information across multiple organizational documents.

DOCUMENTS TO COMPARE:
{context}

COMPARISON REQUEST: {question}

INSTRUCTIONS:
1. Identify similarities and differences between the documents
2. Highlight any conflicts or inconsistencies
3. Organize the comparison in a clear, structured format
4. Cite specific documents for each point
5. Note any missing information that would be helpful for the comparison

Provide a structured comparison:"""

    def _build_extraction_template(self) -> str:
        """Build template for extracting specific information"""
        return """You are Cortex, extracting specific information from organizational documents.

DOCUMENT CONTENT:
{context}

EXTRACTION REQUEST: {question}

INSTRUCTIONS:
1. Extract only the specific information requested
2. Present the information in a clear, organized format
3. Include exact quotes when relevant
4. Cite the source document for each piece of information
5. If the requested information is not found, state this clearly

Extracted information:"""

class AdaptiveQAChain:
    """Adaptive QA chain that routes queries to appropriate processing strategies"""
    
    def __init__(self):
        self.ollama = OllamaHandler()
        self.prompt_manager = PromptTemplateManager()
        self.conversation_history = []
        
    def process_query(self, query: str, context_documents: List[Dict[str, Any]], 
                     chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process query with adaptive routing to appropriate chain"""
        
        if not self.ollama.is_available():
            return {
                'answer': "I'm sorry, but the AI service is currently unavailable. Please make sure Ollama is running with the required model.",
                'confidence': 'low',
                'sources': [],
                'error': 'ollama_unavailable'
            }
        
        # Analyze query type
        query_analysis = self._analyze_query_type(query)
        
        # Route to appropriate processing chain
        if query_analysis['type'] == 'summarization':
            return self._summarization_chain(query, context_documents)
        elif query_analysis['type'] == 'comparison':
            return self._comparison_chain(query, context_documents)
        elif query_analysis['type'] == 'extraction':
            return self._extraction_chain(query, context_documents)
        else:
            return self._factual_qa_chain(query, context_documents, chat_history)
    
    def _analyze_query_type(self, query: str) -> Dict[str, str]:
        """Analyze query to determine the best processing approach"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['summarize', 'summary', 'overview', 'main points']):
            return {'type': 'summarization', 'confidence': 'high'}
        elif any(keyword in query_lower for keyword in ['compare', 'difference', 'versus', 'vs', 'contrast']):
            return {'type': 'comparison', 'confidence': 'high'}
        elif any(keyword in query_lower for keyword in ['extract', 'find', 'list', 'what are', 'show me']):
            return {'type': 'extraction', 'confidence': 'medium'}
        else:
            return {'type': 'factual', 'confidence': 'medium'}
    
    def _factual_qa_chain(self, query: str, context_documents: List[Dict[str, Any]], 
                         chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process factual questions"""
        
        # Format context
        context = self._format_context(context_documents)
        
        # Format chat history
        formatted_history = self._format_chat_history(chat_history or [])
        
        # Build prompt
        prompt = self.prompt_manager.get_template('qa_template').format(
            context=context,
            question=query,
            chat_history=formatted_history
        )
        
        # Generate response (increased tokens for comprehensive answers with native Ollama)
        response = self.ollama.generate(prompt, max_tokens=1000, temperature=0.1)
        
        if not response:
            return {
                'answer': "I'm sorry, I couldn't generate a response. Please try rephrasing your question.",
                'confidence': 'low',
                'sources': [],
                'error': 'generation_failed'
            }
        
        # Extract sources
        sources = self._extract_sources(context_documents)
        
        # Determine confidence
        confidence = self._assess_confidence(response, context_documents)
        
        return {
            'answer': response,
            'confidence': confidence,
            'sources': sources,
            'query_type': 'factual_qa'
        }
    
    def _summarization_chain(self, query: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process summarization requests"""
        
        context = self._format_context(context_documents)
        
        prompt = self.prompt_manager.get_template('summarization_template').format(
            context=context,
            question=query
        )
        
        response = self.ollama.generate(prompt, max_tokens=1000, temperature=0.2)
        
        sources = self._extract_sources(context_documents)
        
        return {
            'answer': response,
            'confidence': 'medium',
            'sources': sources,
            'query_type': 'summarization'
        }
    
    def _comparison_chain(self, query: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process comparison requests"""
        
        context = self._format_context(context_documents)
        
        prompt = self.prompt_manager.get_template('comparison_template').format(
            context=context,
            question=query
        )

        response = self.ollama.generate(prompt, max_tokens=1000, temperature=0.1)
        
        sources = self._extract_sources(context_documents)
        
        return {
            'answer': response,
            'confidence': 'medium',
            'sources': sources,
            'query_type': 'comparison'
        }
    
    def _extraction_chain(self, query: str, context_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process information extraction requests"""
        
        context = self._format_context(context_documents)
        
        prompt = self.prompt_manager.get_template('extraction_template').format(
            context=context,
            question=query
        )

        response = self.ollama.generate(prompt, max_tokens=1000, temperature=0.1)
        
        sources = self._extract_sources(context_documents)
        
        return {
            'answer': response,
            'confidence': 'high',
            'sources': sources,
            'query_type': 'extraction'
        }
    
    def _format_context(self, context_documents: List[Dict[str, Any]]) -> str:
        """Format context documents for inclusion in prompts"""
        if not context_documents:
            return "No relevant documents found."
        
        formatted_context = []
        
        for i, doc in enumerate(context_documents[:5], 1):  # Limit to top 5 documents
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # ALWAYS use original filename if available
            doc_id = f"Document {i}"
            
            # First priority: Use original_filename from metadata
            if 'original_filename' in metadata:
                orig_filename = metadata.get('original_filename')
                # Clean the filename for better display
                if orig_filename.lower().endswith('.pdf'):
                    orig_filename = orig_filename[:-4]
                doc_id = orig_filename
            # Second priority: Try to extract from source_document field
            elif 'source_document' in metadata:
                source_doc = metadata.get('source_document')
                # Try to get a cleaner name 
                if '_' in source_doc and not source_doc.startswith('doc_') and not source_doc.startswith('tmp'):
                    parts = source_doc.split('_')
                    if len(parts) >= 2:
                        doc_id = " ".join(parts[:-1])  # Remove the last numeric part
                elif not source_doc.startswith('doc_') and not source_doc.startswith('tmp'):
                    # If there are no underscores but it's not a tmp file or doc_xx format
                    if source_doc.lower().endswith('.pdf'):
                        doc_id = source_doc[:-4]  # Remove .pdf extension
                    else:
                        doc_id = source_doc
            
            # Ensure we don't have reference to numeric IDs
            if 'doc_' in doc_id.lower() or doc_id.startswith('tmp'):
                doc_id = f"Document {i}"
                
            # Truncate very long content
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            formatted_context.append(f"[Document {i}: {doc_id}]\n{content}\n")
        
        return "\n".join(formatted_context)
    
    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Format conversation history"""
        if not chat_history:
            return "No previous conversation."
        
        formatted_history = []
        for entry in chat_history[-5:]:  # Last 5 interactions
            role = entry.get('role', 'user')
            content = entry.get('content', '')
            formatted_history.append(f"{role.title()}: {content}")
        
        return "\n".join(formatted_history)
    
    def _extract_sources(self, context_documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from context documents"""
        sources = []
        seen_sources = set()
        
        for doc in context_documents:
            metadata = doc.get('metadata', {})
            source_doc = metadata.get('source_document', 'Unknown')
            
            # Handle common problematic source IDs
            if source_doc.startswith('doc_'):
                # Try to extract original filename from content
                content = doc.get('content', '')
                first_line = content.split('\n')[0] if content else ''
                if first_line and len(first_line) < 100:  # Reasonable title length
                    better_name = first_line.strip()
                    source_doc = better_name  # Use first line as document name
            
            # Use a composite key to avoid duplicates but allow different pages from same source
            composite_key = f"{source_doc}_{metadata.get('page', 0)}"
            
            if composite_key not in seen_sources:
                # Base source info with enriched defaults
                source_info = {
                    'document': source_doc,
                    'author': metadata.get('author', 'Unknown'),
                    'creation_date': metadata.get('creation_date', 'Unknown')
                }
                
                # Always include display-friendly metadata
                # Include original filename if available
                if 'original_filename' in metadata:
                    source_info['original_filename'] = metadata.get('original_filename')
                    
                    # If we have original filename but no title, use filename as title
                    if 'title' not in metadata and 'display_name' not in metadata:
                        filename = metadata.get('original_filename', '')
                        if filename.lower().endswith('.pdf'):
                            filename = filename[:-4]
                        source_info['title'] = filename
                
                # Include title or display_name if available
                if 'title' in metadata:
                    source_info['title'] = metadata.get('title')
                elif 'display_name' in metadata:
                    source_info['display_name'] = metadata.get('display_name')
                    
                # Include page number if available
                page_num = metadata.get('page_number') or metadata.get('page')
                if page_num:
                    source_info['page'] = page_num
                    
                sources.append(source_info)
                seen_sources.add(composite_key)
        
        return sources
    
    def _assess_confidence(self, response: str, context_documents: List[Dict[str, Any]]) -> str:
        """Assess confidence level of the response"""
        
        # Simple heuristics for confidence assessment
        if not context_documents:
            return 'low'
        
        if len(context_documents) >= 3 and len(response) > 200:
            return 'high'
        elif len(context_documents) >= 2 and len(response) > 100:
            return 'medium'
        else:
            return 'low'
    
    def add_to_conversation_history(self, user_query: str, assistant_response: str):
        """Add interaction to conversation history"""
        self.conversation_history.extend([
            {'role': 'user', 'content': user_query, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': assistant_response, 'timestamp': datetime.now().isoformat()}
        ])
        
        # Keep only last 10 interactions
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
