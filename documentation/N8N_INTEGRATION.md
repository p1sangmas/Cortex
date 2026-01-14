# n8n Integration Guide for Cortex

## Overview

Cortex integrates with [n8n](https://n8n.io/), a powerful low-code automation platform, to extend its capabilities beyond traditional document search. With n8n, you can:

- **Web Search Integration**: Augment internal documents with external web search when needed
- **Telegram Bot Interface**: Interact with Cortex through Telegram chat
- **Automated Workflows**: Create custom automation workflows without coding
- **Multi-Platform Integration**: Connect Cortex with hundreds of services (Slack, Gmail, Google Drive, etc.)

## Quick Start

### 1. Start Cortex with n8n

Using the management script:
```bash
./run_docker.sh
# Select option 2: "Start Cortex with n8n (automation workflows)"
```

Or manually with Docker Compose:
```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
```

### 2. Access n8n Interface

Open your browser and navigate to:
```
http://localhost:5678
```

**Default Login Credentials** (configured in `.env`):
- Username: `admin`
- Password: `changeme123`

> **Security Note**: Change these credentials in your `.env` file before deploying to production!

## Available Workflows

Cortex comes with two pre-built n8n workflows:

### 1. Web Search Tool (`01-web-search-tool.json`)

**Purpose**: Provides external web search capability using DuckDuckGo API

**How it works**:
1. Cortex calls n8n webhook when internal documents lack information
2. n8n queries DuckDuckGo API
3. Results are parsed and returned to Cortex
4. User receives synthesized answer combining internal + external sources

**Webhook URL**: `http://cortex-n8n:5678/webhook/web-search`

**API**: Uses DuckDuckGo's free Instant Answer API (no API key required)

**Trigger Conditions** (automatic):
- No internal documents found for query
- Internal results have low confidence (< 0.5)
- Query contains keywords: "current", "latest", "recent", "today", year references
- Query mentions external entities: weather, stock prices, etc.

**Example Queries**:
- "What is the current stock price of Tesla?" (triggers web search)
- "What's the weather in New York today?" (triggers web search)
- "Summarize our Q4 report" (uses internal documents only)

### 2. Telegram Bot (`02-telegram-bot.json`)

**Purpose**: Chat interface to Cortex via Telegram

**Features**:
- `/start` command shows help message
- Natural language queries to your documents
- Rich formatted responses with sources and page numbers
- Shows execution time for each query
- Uses agentic RAG mode by default

**Commands**:
- `/start` - Display help message and available commands
- Any other message - Treated as a query to Cortex

**Response Format**:
```
📚 Answer (agentic mode):

[Your comprehensive answer here]

📄 Sources:
1. Document.pdf (Page 5)
2. Report.pdf (Page 12)

⏱️ Time: 3.2s
```

## Setup Instructions

### Step 1: Configure Environment Variables

Edit your `.env` file (created from `.env.example`):

```bash
# n8n Configuration
N8N_PORT=5678
N8N_BASE_URL=http://cortex-n8n:5678
N8N_USER=admin
N8N_PASSWORD=your_secure_password_here

# Telegram Bot (optional - only if using Telegram workflow)
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Step 2: Start Services

```bash
./run_docker.sh
# Select option 2
```

Wait for all containers to start (may take 1-2 minutes on first run).

### Step 3: Import Workflows

1. Open n8n interface: http://localhost:5678
2. Login with your credentials
3. Click **"Workflows"** in the left sidebar
4. Click **"Import from File"** button (top right)
5. Select workflow files from `n8n-workflows/` directory:
   - `01-web-search-tool.json`
   - `02-telegram-bot.json` (optional, if using Telegram)
6. Click **"Import"** to load the workflow
7. Click **"Save"** button (top right)
8. Toggle **"Active"** switch to enable the workflow

Repeat for each workflow you want to use.

### Step 4: Configure Telegram Bot (Optional)

If you want to use the Telegram bot workflow:

#### A. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to choose a name and username
4. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### B. Add Token to Environment

Edit `.env` file:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### C. Configure n8n Credentials

1. In n8n, open the **Telegram Bot** workflow
2. Click on any **Telegram node** (Trigger or Send nodes)
3. Click **"Create New Credential"** for Telegram API
4. Paste your bot token
5. Click **"Save"**
6. Repeat for all Telegram nodes in the workflow
7. Save and activate the workflow

#### D. Test Your Bot

1. Open Telegram and search for your bot's username
2. Send `/start` command
3. You should receive a welcome message
4. Send any question about your documents
5. Bot will query Cortex and return the answer

## Architecture

### Web Search Flow
```
User Query
    ↓
Cortex Agentic Orchestrator
    ↓
WebSearchTool (if needed)
    ↓
POST http://cortex-n8n:5678/webhook/web-search
    ↓
n8n Workflow: Web Search Tool
    ├─ Webhook Trigger
    ├─ HTTP Request (DuckDuckGo API)
    ├─ Parse Results (JavaScript)
    └─ Respond to Webhook
    ↓
Return to Cortex
    ↓
Synthesize with Internal Results
    ↓
Display to User
```

### Telegram Bot Flow
```
User → Telegram Message
    ↓
n8n Workflow: Telegram Bot
    ├─ Telegram Trigger
    ├─ Check if Command (/start, /help)
    │   ├─ Yes → Send Help Message
    │   └─ No → Continue
    ├─ Send Processing Message
    ├─ HTTP Request → Cortex API
    │   POST http://cortex:8080/api/query
    │   Body: {"query": "...", "mode": "agentic"}
    ├─ Format Response (JavaScript)
    └─ Send Answer via Telegram
    ↓
User receives answer in Telegram
```

## Customization

### Creating Custom Workflows

n8n's visual workflow editor makes it easy to create custom integrations:

#### Example: Slack Notifications

1. Create new workflow in n8n
2. Add **Webhook Trigger** node
3. Add **Slack** node
4. Connect them
5. Configure Slack credentials
6. Save and activate

Then modify Cortex to call your webhook when certain conditions are met.

#### Example: Auto-Summarization

1. Create webhook trigger for new document uploads
2. Add HTTP Request to Cortex API to get document summary
3. Add Email/Slack node to send summary
4. Save and activate

### Modifying Existing Workflows

All workflow files are in `n8n-workflows/` directory as JSON files. You can:

1. Edit them directly in n8n UI (recommended)
2. Export modified workflows: Workflows → Export
3. Edit JSON files manually (advanced)

### Adding More Search Providers

To replace DuckDuckGo with another search provider:

1. Open `01-web-search-tool.json` workflow in n8n
2. Click on the **HTTP Request** node
3. Update the URL and parameters for your chosen provider:
   - **Brave Search API**: https://brave.com/search/api/
   - **SerpAPI**: https://serpapi.com/ (requires API key)
   - **Google Custom Search**: https://developers.google.com/custom-search
4. Update the **Parse Results** node to handle different response format
5. Save the workflow

## Troubleshooting

### n8n Not Accessible

**Problem**: Cannot access http://localhost:5678

**Solutions**:
1. Check if n8n container is running:
   ```bash
   docker ps | grep cortex-n8n
   ```

2. Check n8n logs:
   ```bash
   docker logs cortex-n8n
   ```

3. Verify port is not already in use:
   ```bash
   lsof -i :5678
   ```

4. Restart n8n container:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.n8n.yml restart n8n
   ```

### Web Search Not Working

**Problem**: Cortex says "Web search service not available"

**Solutions**:
1. Ensure n8n is running and web search workflow is imported and activated
2. Check webhook URL in Cortex logs:
   ```bash
   docker logs cortex | grep "n8n"
   ```

3. Test webhook manually:
   ```bash
   curl -X POST http://localhost:5678/webhook/web-search \
     -H "Content-Type: application/json" \
     -d '{"query": "test query"}'
   ```

4. Check n8n execution logs in the UI

### Telegram Bot Not Responding

**Problem**: Bot doesn't reply to messages

**Solutions**:
1. Verify bot token is correct in `.env`
2. Check Telegram credentials in n8n workflow
3. Ensure Telegram workflow is activated (green toggle)
4. Check Cortex API is accessible from n8n:
   ```bash
   docker exec cortex-n8n curl http://cortex:8080/api/health
   ```

5. Check n8n workflow executions for errors (n8n UI → Executions tab)

### DuckDuckGo API Rate Limiting

**Problem**: Web searches fail intermittently

**Cause**: DuckDuckGo Instant Answer API has rate limits

**Solutions**:
1. Add delay between requests in n8n workflow
2. Switch to paid search API (Brave, SerpAPI) for production use
3. Implement caching in n8n workflow (use Set node to store recent results)

### Webhook Timeout

**Problem**: "Web search timed out after 30 seconds"

**Solutions**:
1. Increase timeout in `src/tools/web_search_tool.py`:
   ```python
   self.timeout = 60  # Increase from 30 to 60 seconds
   ```

2. Check n8n workflow execution time (should be < 5 seconds normally)
3. Optimize search API calls in workflow

## Security Best Practices

### Production Deployment

When deploying to production:

1. **Change default credentials**:
   ```bash
   N8N_USER=your_secure_username
   N8N_PASSWORD=your_very_secure_password
   ```

2. **Use HTTPS**: Configure reverse proxy (nginx/caddy) with SSL
   ```yaml
   # In docker-compose.n8n.yml, add:
   environment:
     - N8N_PROTOCOL=https
     - N8N_HOST=n8n.yourdomain.com
   ```

3. **Restrict access**: Use firewall rules to limit n8n access
   ```bash
   # Only allow localhost
   ufw allow from 127.0.0.1 to any port 5678
   ```

4. **Protect API keys**: Store Telegram bot token and API keys securely
   - Use Docker secrets instead of .env file
   - Never commit .env to git (already in .gitignore)

5. **Enable n8n encryption**: Set encryption key for sensitive data
   ```bash
   N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
   ```

### Network Security

n8n and Cortex communicate via Docker network `cortex_default`:
- Internal communication uses container names (`documind`, `cortex-n8n`)
- No external network access required for core functionality
- Only expose ports you need (5678 for n8n UI, 8080 for Cortex web)

## Advanced: Creating Custom Tools

You can create new Cortex tools that use n8n workflows:

### Example: Database Query Tool

1. **Create n8n workflow**:
   - Webhook trigger on `/webhook/db-query`
   - Postgres/MySQL node to query database
   - Return formatted results

2. **Create Cortex tool**:
   ```python
   # src/tools/database_tool.py
   from src.tools import BaseTool, ToolResult
   import requests

   class DatabaseTool(BaseTool):
       name = "database_query"
       description = "Query internal database for structured data"

       def execute(self, query: str, context: Dict) -> ToolResult:
           response = requests.post(
               "http://cortex-n8n:5678/webhook/db-query",
               json={"query": query}
           )
           return ToolResult(
               success=True,
               data=response.json(),
               metadata={'tool': self.name}
           )
   ```

3. **Register tool** in `src/agent/orchestrator.py`

## Resources

- **n8n Documentation**: https://docs.n8n.io/
- **n8n Workflow Templates**: https://n8n.io/workflows/
- **DuckDuckGo API Docs**: https://duckduckgo.com/api
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Cortex GitHub**: (add your repo URL here)

## Support

For issues related to:
- **Cortex + n8n integration**: Open issue on Cortex repository
- **n8n platform**: Check [n8n community forum](https://community.n8n.io/)
- **Telegram Bot**: Read [Telegram Bot FAQ](https://core.telegram.org/bots/faq)

## What's Next?

Consider adding these n8n integrations:

1. **Email Integration**: Auto-process PDF attachments from Gmail
2. **Slack Bot**: Chat with Cortex in Slack channels
3. **Google Drive Sync**: Auto-ingest new documents from shared folder
4. **Notion Export**: Query Cortex from Notion pages
5. **Scheduled Reports**: Daily summary emails of important documents
6. **Multi-language Support**: Translate queries/responses in real-time
7. **Voice Interface**: Integrate with Twilio for phone queries

All of these can be built with n8n's visual workflow editor without writing code!
