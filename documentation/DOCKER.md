# filepath: /Users/fakhrulfauzi/Documents/Projects/Cortex/DOCKER.md
# Docker Setup for Cortex

This guide explains how to run Cortex using Docker, allowing for easy deployment on any operating system (Windows, macOS, or Linux).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- At least 4GB of free RAM (8GB+ recommended)
- At least 10GB of free disk space (more if you plan to use larger models)

### Recommended System Requirements

- **Minimum**: 4GB RAM, dual-core CPU
- **Recommended**: 8GB RAM, quad-core CPU
- **For GPU Acceleration**: NVIDIA GPU with 4GB+ VRAM and NVIDIA Container Toolkit installed

## Quick Start

The easiest way to get started is to use the included helper script:

```bash
# Make the script executable (if needed)
chmod +x run_docker.sh

# Run the script and follow the menu options
./run_docker.sh
./run_docker.sh
```

Select option 1 from the menu to start Cortex.

## Manual Setup

If you prefer to run commands manually:

1. **Build and start the containers**:
   ```bash
   docker compose up -d
   ```

2. **Pull the Ollama model**:
   ```bash
   docker compose exec ollama ollama pull llama3.2:3b
   ```

3. **View logs**:
   ```bash
   docker compose logs -f
   ```

4. **Stop all containers**:
   ```bash
   docker compose down
   ```

## Configuration

### Using an Alternative Ollama Model

1. Edit the `config/settings.py` file and change the `OLLAMA_MODEL` variable.
2. Restart the containers.
3. Pull the new model:
   ```bash
   docker compose exec ollama ollama pull your-model-name
   ```

### GPU Support

For GPU acceleration:

1. Make sure you have the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed.
2. The docker-compose file already includes the necessary GPU configuration.

If you're on a non-NVIDIA system or don't want GPU support, remove or comment out the `deploy` section in the docker-compose.yml file for the ollama service.

## Accessing the Application

After starting the containers:

- **Web UI**: http://localhost:8080
- **Direct API Endpoint**: http://localhost:8000/api

## Data Persistence

All data is persisted in the following directories:

- `./data/documents`: Uploaded documents
- `./data/vectorstore`: Vector database
- `./data/models_cache`: Model cache

## GPU Support

By default, Cortex runs in CPU mode, which is compatible with all systems. If you have an NVIDIA GPU, you can enable GPU acceleration:

### Automatic GPU Detection (Recommended)

The included `run_docker.sh` script automatically detects if you have a compatible NVIDIA GPU and enables GPU support if available.

### Manual GPU Configuration

To manually enable GPU support:

1. Make sure you have:
   - NVIDIA GPU with up-to-date drivers
   - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed

2. Run with the GPU configuration:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
   ```

### Performance Considerations

- CPU mode will still work but may be slower for running LLMs
- If you get errors about NVIDIA drivers, ensure they are correctly installed or use CPU mode

## Troubleshooting

### The web UI is not accessible

- Check if containers are running: `docker compose ps`
- Check logs: `docker compose logs`

### GPU-related errors

- If you see errors about NVIDIA driver or GPU capabilities, your system might not have proper GPU support
- Try running without GPU configuration: `docker compose up -d` (without the GPU override)

### Ollama model is not working

- Check if Ollama is running: `docker compose ps ollama`
- Check if the model is pulled: `docker compose exec ollama ollama list`
- Pull the model manually: `docker compose exec ollama ollama pull llama3.2:3b`

## Advanced Configuration

### Environment Variables

You can create or modify the `.env` file in the project root with the following variables:

```
# Timezone setting
TZ=YOUR_TIMEZONE  # e.g., America/New_York, Europe/London

# Port configuration
WEB_UI_PORT=8080  # Port for accessing web UI
API_PORT=8000     # Port for direct API access
OLLAMA_PORT=11434 # Port for Ollama service

# Debug mode
DEBUG=false       # Set to true for verbose logging

# GPU support
ENABLE_GPU=auto   # Options: true, false, or auto (for automatic detection)
```

### Running on a Different Port

To run on a different port, modify the `docker-compose.yml` file and change the port mapping:

```yaml
ports:
  - "8888:80"    # Change 8888 to your desired port for Web UI
  - "9000:8080"  # Change 9000 to your desired port for direct API access
```
