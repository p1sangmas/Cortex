#!/usr/bin/env python3
"""
Script to pre-download and initialize all required models for Cortex.
This ensures that the first query doesn't have delays from model downloads.
"""

import os
import sys
import logging
import torch
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, CrossEncoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("preload_models")

# Import settings
try:
    from config.settings import (
        EMBEDDING_MODEL, 
        CROSS_ENCODER_MODEL, 
        VECTORSTORE_PERSIST_DIRECTORY,
        VECTORSTORE_COLLECTION_NAME
    )
except ImportError:
    logger.error("Failed to import settings, using defaults")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    VECTORSTORE_PERSIST_DIRECTORY = "data/vectorstore"
    VECTORSTORE_COLLECTION_NAME = "documents"

def preload_models():
    """Download and initialize all models needed by Cortex"""
    
    # Step 1: Download the sentence transformer embedding model
    logger.info(f"Downloading embedding model: {EMBEDDING_MODEL}")
    try:
        device = 'cpu'  # Use CPU to avoid MPS/CUDA issues
        model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info("Embedding model downloaded and initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}")
        return False
    
    # Step 2: Download the cross-encoder model
    logger.info(f"Downloading cross encoder model: {CROSS_ENCODER_MODEL}")
    try:
        cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
        logger.info("Cross encoder model downloaded and initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize cross encoder: {e}")
        # Continue anyway, as this might not be critical
    
    # Step 3: Initialize ChromaDB and force ONNX model download
    logger.info("Initializing ChromaDB and downloading ONNX models")
    try:
        # Create the ChromaDB client
        chroma_client = chromadb.PersistentClient(
            path=VECTORSTORE_PERSIST_DIRECTORY,
            settings=Settings(allow_reset=False)
        )
        logger.info("ChromaDB client initialized successfully!")
        
        # Force ONNX download
        # Create embedding function
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device='cpu'
        )
        
        # Try to get existing collection
        try:
            collection = chroma_client.get_collection(
                name=VECTORSTORE_COLLECTION_NAME,
                embedding_function=sentence_transformer_ef
            )
            logger.info(f"Found existing collection {VECTORSTORE_COLLECTION_NAME}")
            
            # If collection exists and has documents, query it to force ONNX download
            if collection.count() > 0:
                logger.info("Running test query on existing collection to force ONNX download")
                results = collection.query(
                    query_texts=["test document to force ONNX download"],
                    n_results=1
                )
                logger.info("Successfully queried existing collection")
            else:
                # Collection exists but is empty, add a test document
                logger.info("Collection is empty, adding test document to force ONNX download")
                collection.add(
                    documents=["This is a test document to force ONNX model download"],
                    metadatas=[{"source": "preload", "temporary": True}],
                    ids=["temp-preload-doc-1"]
                )
                logger.info("Added temporary document to collection")
                
                # Query to ensure models are downloaded
                results = collection.query(
                    query_texts=["test document"],
                    n_results=1
                )
                
                # Clean up the temporary document
                collection.delete(ids=["temp-preload-doc-1"])
                logger.info("Removed temporary document after successful query")
        except Exception as collection_error:
            # Collection doesn't exist - create a temporary one
            logger.info(f"Creating temporary collection to force ONNX download: {collection_error}")
            temp_collection = chroma_client.create_collection(
                name="temp_collection_for_preload",
                embedding_function=sentence_transformer_ef
            )
            
            # Add a test document to trigger ONNX download
            temp_collection.add(
                documents=["This is a test document to force ONNX model download"],
                metadatas=[{"source": "preload"}],
                ids=["temp-preload-doc-1"]
            )
            
            # Query to ensure models are downloaded
            results = temp_collection.query(
                query_texts=["test document"],
                n_results=1
            )
            
            # Clean up
            chroma_client.delete_collection("temp_collection_for_preload")
            logger.info("Created and deleted temporary collection to download ONNX models")
    
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB and download ONNX models: {e}")
        logger.warning("This might cause delays on the first query. Error details:")
        import traceback
        logger.warning(traceback.format_exc())
    
    # Step 4: Test embedding generation to ensure everything is working
    logger.info("Testing embedding generation...")
    test_text = "Test document to ensure embedding pipeline is working"
    try:
        test_embedding = model.encode(test_text)
        logger.info(f"Successfully generated test embedding with shape: {test_embedding.shape}")
    except Exception as e:
        logger.error(f"Failed to generate test embedding: {e}")
        return False
    
    logger.info("All models have been downloaded and initialized!")
    return True

if __name__ == "__main__":
    success = preload_models()
    if not success:
        logger.error("Failed to preload all required models")
        sys.exit(1)
    sys.exit(0)
