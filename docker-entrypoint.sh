#!/bin/bash
# Entrypoint script for Cortex Docker container

# Function to check and create necessary directories
setup_directories() {
  echo "Setting up required directories..."
  mkdir -p /app/data/documents
  mkdir -p /app/data/vectorstore
  mkdir -p /home/docuuser/.cache/huggingface
  
  # Ensure proper permissions
  chown -R docuuser:docuuser /app/data /home/docuuser/.cache
}

# Function to check if nginx can start
check_nginx() {
  echo "Checking nginx configuration..."
  nginx -t
  if [ $? -ne 0 ]; then
    echo "Error: nginx configuration test failed"
    return 1
  fi
  return 0
}

# Start Nginx in background
echo "Starting Nginx webserver..."
if check_nginx; then
  # Try to run nginx with alternate configurations if needed
  nginx || nginx -g "pid /tmp/nginx.pid;" || nginx -g "daemon off;"
  if [ $? -ne 0 ]; then
    echo "Warning: nginx failed to start. Web UI may not be available, but API should still work."
    echo "Error details:"
    cat /var/log/nginx/error.log
  else
    echo "Nginx started successfully."
  fi
else
  echo "Warning: nginx configuration is invalid. Web UI may not be available, but API should still work."
fi

# Check if Ollama is available (allows for startup timing differences)
echo "Waiting for Ollama service..."
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]
do
    if curl -s -o /dev/null -w "%{http_code}" $OLLAMA_BASE_URL/api/version | grep -q "200\|404"; then
        echo "✓ Ollama service is available!"
        break
    fi
    
    echo "Attempt $attempt of $max_attempts: Ollama not ready yet, waiting..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "⚠️ Warning: Could not connect to Ollama service after $max_attempts attempts."
    echo "The application will still start, but LLM functionality may not work."
    echo "Make sure the 'ollama' service is running and accessible."
fi

# Pre-download embedding models
echo "Pre-downloading embedding models to avoid first-query delay..."
python -c "
import os
import torch
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, CrossEncoder
from config.settings import EMBEDDING_MODEL, CROSS_ENCODER_MODEL, VECTORSTORE_PERSIST_DIRECTORY, VECTORSTORE_COLLECTION_NAME

# Force model downloads
print(f'Downloading embedding model: {EMBEDDING_MODEL}...')
model = SentenceTransformer(EMBEDDING_MODEL)
print('Embedding model downloaded and initialized successfully!')

print(f'Downloading cross encoder model: {CROSS_ENCODER_MODEL}...')
cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
print('Cross encoder model downloaded and initialized successfully!')

# Initialize ChromaDB to ensure ONNX models are downloaded
print('Initializing ChromaDB and downloading ONNX models...')
try:
    # Create the ChromaDB client
    chroma_client = chromadb.PersistentClient(
        path=VECTORSTORE_PERSIST_DIRECTORY,
        settings=Settings(allow_reset=False)
    )
    print('ChromaDB client initialized successfully!')
    
    # This will force ChromaDB to download and prepare ONNX models
    # by creating a temporary collection and adding a document
    try:
        # First check if our collection already exists
        try:
            collection = chroma_client.get_collection(VECTORSTORE_COLLECTION_NAME)
            print(f'Found existing collection {VECTORSTORE_COLLECTION_NAME}')
            
            # Force ONNX model download by performing a query on the existing collection
            if collection.count() > 0:
                print('Triggering ONNX download with existing collection')
                results = collection.query(
                    query_texts=['test document to force onnx download'],
                    n_results=1
                )
                print('Successfully queried existing collection to force ONNX download')
        except:
            # Create a temporary collection if the main one doesn't exist
            print('Creating temporary ChromaDB collection to trigger ONNX download')
            # Use default sentence transformer embedding function to match the retriever
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
            
            # Create a collection with our embedding function
            temp_collection = chroma_client.create_collection(
                name='temp_collection_for_preload', 
                embedding_function=sentence_transformer_ef
            )
            
            # Add a test document to force ONNX model download
            temp_collection.add(
                documents=['This is a test document to force ONNX model download'],
                metadatas=[{'source': 'preload'}],
                ids=['preload-test-doc-1']
            )
            
            # Query to ensure everything is loaded
            results = temp_collection.query(
                query_texts=['test document'],
                n_results=1
            )
            
            # Clean up the temporary collection
            chroma_client.delete_collection('temp_collection_for_preload')
            print('Successfully forced ONNX model download and verified ChromaDB query works')
    except Exception as e:
        print(f'Warning: Failed to force ONNX model download: {e}')
        print('This might cause a delay on the first query, but should not affect functionality')
        
except Exception as e:
    print(f'Warning: ChromaDB initialization raised an exception: {e}')
    print('This is generally fine as long as the models were downloaded.')

# Test a quick embedding generation to ensure everything is working
test_text = 'Test document to ensure embedding pipeline is working'
print('Testing embedding generation...')
test_embedding = model.encode(test_text)
print(f'Successfully generated test embedding with shape: {test_embedding.shape}')
print('All models have been downloaded and initialized!')
"

# Print environment
echo "Running with environment:"
echo "- OLLAMA_BASE_URL: $OLLAMA_BASE_URL"
echo "- HOST: $HOST"
echo "- PORT: $PORT"

# Start the API server
echo "Starting Cortex API server..."
python api.py
