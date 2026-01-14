#!/bin/bash
# This script helps run Cortex using Docker Compose

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Function to check if NVIDIA GPU is available
check_gpu() {
    # Check for Linux systems with nvidia-smi
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi &> /dev/null
        if [ $? -eq 0 ]; then
            return 0  # GPU available
        fi
    fi
    
    # Check for macOS with Metal (future compatibility)
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS - check for eGPU or integrated GPU that could be used
        # For now, return 1 as Docker GPU support on macOS is limited
        return 1
    fi
    
    # Check for Windows with WSL2 and NVIDIA
    if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
        # We're in WSL2, check for NVIDIA
        if command -v nvidia-smi &> /dev/null; then
            nvidia-smi &> /dev/null
            if [ $? -eq 0 ]; then
                return 0  # GPU available
            fi
        fi
    fi
    
    return 1  # GPU not available
}

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists, if not create it from template
if [ ! -f .env ]; then
    echo "Creating .env file with default settings..."
    if [ -f .env.example ]; then
        cp .env.example .env
        # Update timezone
        if [[ "$(uname)" == "Darwin" ]]; then
            # macOS
            TZ=$(date +%Z)
        else
            # Linux/WSL
            TZ=$(cat /etc/timezone 2>/dev/null || date +%Z)
        fi
        sed -i.bak "s/TZ=UTC/TZ=${TZ}/" .env && rm -f .env.bak
    else
        echo "# Cortex Docker Environment Settings" > .env
        echo "TZ=$(date +%Z)" >> .env
        echo "DEBUG=false" >> .env
        echo "WEB_UI_PORT=8080" >> .env
        echo "API_PORT=8000" >> .env
        echo "OLLAMA_PORT=11434" >> .env
        echo "ENABLE_GPU=auto" >> .env
    fi
    echo "Created .env file with default settings. Edit this file to customize your setup."
fi

# Check if config/settings.py exists
if [ ! -f config/settings.py ]; then
    echo "Configuration file not found. Please copy config/settings.example.py to config/settings.py and edit it."
    exit 1
fi

# Function to pull Ollama models
pull_models() {
    echo "Pulling Ollama models (this may take a while)..."
    MODEL=$(grep -E "OLLAMA_MODEL\s*=" config/settings.py | cut -d'"' -f2 | cut -d"'" -f2)
    if [ -z "$MODEL" ]; then
        echo "Could not determine model from settings. Using default model."
        MODEL="llama3.2:3b"
    fi
    
    echo "Pulling model: $MODEL"
    docker compose exec ollama ollama pull "$MODEL"
    
    # Ask if user wants to pull a smaller backup model for faster responses
    read -p "Do you want to pull a smaller model (phi3:mini) as a backup for faster responses? (y/n): " pull_backup
    if [ "$pull_backup" = "y" ] || [ "$pull_backup" = "Y" ]; then
        echo "Pulling phi3:mini as a backup model..."
        docker compose exec ollama ollama pull phi3:mini
        echo "To use this model, update OLLAMA_MODEL in config/settings.py to 'phi3:mini'"
    fi
}

# Function to ensure embedding models are persisted
ensure_model_cache() {
    # Create chroma cache directory if it doesn't exist
    if [ ! -d "data/chroma_cache" ]; then
        echo "Creating directory for persisting embedding models..."
        mkdir -p data/chroma_cache
    fi
    
    # Check if container is running and has models downloaded
    if docker ps -q -f name=cortex >/dev/null; then
        echo "Checking for embedding models in container..."
        if docker exec -i cortex bash -c "[ -d /home/docuuser/.cache/chroma/onnx_models ]" >/dev/null 2>&1; then
            echo "Ensuring embedding models are preserved..."
            docker exec -i cortex bash -c "cp -r /home/docuuser/.cache/chroma/onnx_models /tmp/ 2>/dev/null" >/dev/null 2>&1
            docker cp cortex:/tmp/onnx_models ./data/chroma_cache/ >/dev/null 2>&1
            echo "Embedding models backed up to data/chroma_cache/"
        fi
    fi
}

# Main menu
echo "==== Cortex Docker Management ===="
echo "1. Start Cortex"
echo "2. Start Cortex with n8n (automation workflows)"
echo "3. Stop Cortex"
echo "4. View logs"
echo "5. Pull Ollama models"
echo "6. Switch to a faster model (may reduce quality)"
echo "7. Reset and rebuild (Warning: This will rebuild all containers)"
echo "8. Exit"

read -p "Please select an option (1-8): " option

# Function to switch LLM model
switch_model() {
    echo "Available models to switch to:"
    echo "1. llama3.2:3b (default, better quality but may be slower)"
    echo "2. phi3:mini (faster, lower resource requirements)"
    echo "3. Custom model"
    
    read -p "Choose a model (1-3): " model_choice
    
    case $model_choice in
        1)
            MODEL="llama3.2:3b"
            ;;
        2)
            MODEL="phi3:mini"
            # Pull the model if not already available
            docker compose exec ollama ollama list | grep -q "phi3:mini" || docker compose exec ollama ollama pull phi3:mini
            ;;
        3)
            read -p "Enter custom model name (e.g., llama3:8b, tinyllama, etc): " MODEL
            docker compose exec ollama ollama list | grep -q "$MODEL" || docker compose exec ollama ollama pull "$MODEL"
            ;;
        *)
            echo "Invalid choice. Keeping current model."
            return
            ;;
    esac
    
    # Update the settings.py file
    sed -i.bak "s/OLLAMA_MODEL = \"[^\"]*\"/OLLAMA_MODEL = \"$MODEL\"/" config/settings.py && rm -f config/settings.py.bak
    echo "Model updated to $MODEL in settings. Restart the containers to apply changes."
    
    read -p "Restart containers now? (y/n): " restart
    if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
        docker compose restart
        echo "Containers restarted, new model will be used."
    else
        echo "Remember to restart containers to apply the new model."
    fi
}

case $option in
    1)
        echo "Starting Cortex..."
        # Ensure model cache directories exist
        ensure_model_cache

        # Check if GPU is available
        if check_gpu; then
            echo "NVIDIA GPU detected! Starting with GPU support..."
            docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
            echo "Cortex is now available with GPU acceleration at:"
        else
            echo "No NVIDIA GPU detected. Starting in CPU mode..."
            docker compose up -d
            echo "Cortex is now available at:"
        fi
        echo "- Web UI: http://localhost:8080"
        echo "- API: http://localhost:8000/api"
        ;;
    2)
        echo "Starting Cortex with n8n automation workflows..."
        # Ensure model cache directories exist
        ensure_model_cache

        # Create n8n data directory if it doesn't exist
        mkdir -p n8n-data

        # Check if GPU is available
        if check_gpu; then
            echo "NVIDIA GPU detected! Starting with GPU support..."
            docker compose -f docker-compose.yml -f docker-compose.gpu.yml -f docker-compose.n8n.yml up -d
            echo "Cortex is now available with GPU acceleration at:"
        else
            echo "No NVIDIA GPU detected. Starting in CPU mode..."
            docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
            echo "Cortex is now available at:"
        fi
        echo "- Web UI: http://localhost:8080"
        echo "- API: http://localhost:8000/api"
        echo "- n8n Workflows: http://localhost:5678"
        echo ""
        echo "n8n login credentials (configured in .env):"
        echo "- Username: ${N8N_USER:-admin}"
        echo "- Password: ${N8N_PASSWORD:-changeme123}"
        echo ""
        echo "To import workflows:"
        echo "1. Open http://localhost:5678 in your browser"
        echo "2. Login with the credentials above"
        echo "3. Go to Workflows > Import from File"
        echo "4. Select workflow JSON files from n8n-workflows/ directory"
        ;;
    3)
        echo "Stopping Cortex..."
        docker compose -f docker-compose.yml -f docker-compose.n8n.yml down
        ;;
    4)
        echo "Viewing logs (press Ctrl+C to exit)..."
        docker compose logs -f
        ;;
    5)
        pull_models
        ;;
    6)
        switch_model
        ;;
    7)
        echo "Rebuilding Cortex..."
        # Backup embedding models first
        ensure_model_cache

        docker compose -f docker-compose.yml -f docker-compose.n8n.yml down
        docker compose build --no-cache

        # Check if GPU is available
        if check_gpu; then
            echo "NVIDIA GPU detected! Starting with GPU support..."
            docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
            echo "Cortex has been rebuilt with GPU acceleration and is now available at:"
        else
            echo "No NVIDIA GPU detected. Starting in CPU mode..."
            docker compose up -d
            echo "Cortex has been rebuilt and is now available at:"
        fi
        echo "- Web UI: http://localhost:8080"
        echo "- API: http://localhost:8000/api"
        ;;
    8)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac