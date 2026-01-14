# Environment Setup Guide

## Ollama Connection Configuration

Cortex is designed to work seamlessly with Ollama whether you're running it through Docker or manually. The application automatically detects the environment and sets the appropriate connection URL:

- **Docker Environment**: Uses `http://ollama:11434` (container service name)
- **Manual/Local Environment**: Uses `http://localhost:11434`

### How It Works

The `settings.py` file contains logic to detect whether the application is running in Docker:

```python
# Determine Ollama URL based on environment
# In Docker, Ollama is accessible via service name; otherwise use localhost
import os
OLLAMA_BASE_URL = "http://ollama:11434" if os.environ.get("DOCKER_ENV") == "true" else "http://localhost:11434"
```

The Docker Compose configuration sets this environment variable:

```yaml
environment:
  - DOCKER_ENV=true
```

### Manual Configuration

If you need to override this behavior or connect to an Ollama instance running on another machine, you can manually modify the `OLLAMA_BASE_URL` in `config/settings.py`.

## Other Environment Variables

Cortex uses several environment variables to control its behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `TZ` | Timezone | `UTC` |
| `WEB_UI_PORT` | Port for web interface | `8080` |
| `API_PORT` | Port for API | `8000` |
| `OLLAMA_PORT` | Port for Ollama service | `11434` |
| `DOCKER_ENV` | Indicates Docker environment | Not set (manual) / `true` (Docker) |

These can be set in the `.env` file when using Docker or in your environment when running manually.
