# Cortex n8n Workflows

This directory contains pre-built n8n workflow definitions for extending Cortex's capabilities.

## Available Workflows

### 01-web-search-tool.json
**Purpose**: External web search integration using DuckDuckGo API

**Features**:
- Webhook endpoint: `/webhook/web-search`
- Free DuckDuckGo Instant Answer API (no API key required)
- Automatically triggered when internal documents lack information
- Returns top 5 search results with titles, snippets, and URLs

**Usage**:
- Import into n8n
- Activate the workflow
- Cortex will automatically call it when needed

**Test manually**:
```bash
curl -X POST http://localhost:5678/webhook/web-search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

---

### 02-telegram-bot.json
**Purpose**: Telegram chat interface for Cortex

**Features**:
- Natural language queries via Telegram
- `/start` command for help
- Rich formatted responses with sources and page numbers
- Shows execution time
- Uses agentic RAG mode

**Setup Required**:
1. Create bot with @BotFather on Telegram
2. Get bot token
3. Add token to `.env` file: `TELEGRAM_BOT_TOKEN=your_token`
4. Configure Telegram credentials in n8n workflow
5. Activate workflow

**Commands**:
- `/start` - Show help message
- Any other message - Query Cortex

---

### 03-url-document-ingestion.json
**Purpose**: Automatically download and ingest documents from URLs

**Features**:
- Webhook endpoint: `/webhook/ingest-url`
- Downloads PDF from any public URL
- Automatically processes and adds to vector database
- Same pipeline as manual uploads (chunking, embeddings, metadata)
- Error handling for invalid URLs or download failures

**Usage**:
```bash
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf"}'
```

**With custom filename**:
```bash
curl -X POST http://localhost:5678/webhook/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/doc.pdf", "filename": "my-report.pdf"}'
```

**Response**:
```json
{
  "success": true,
  "message": "Document ingested successfully",
  "filename": "document.pdf",
  "url": "https://example.com/document.pdf",
  "file_info": {
    "filename": "document.pdf",
    "size": 245678,
    "chunks": 42,
    "extraction_method": "pymupdf",
    "timestamp": "2026-01-13 12:34:56"
  },
  "ingestion_source": "url",
  "timestamp": "2026-01-13T12:34:56.789Z"
}
```

**Use Cases**:
- Ingest public documentation (API docs, research papers)
- Monitor websites for document updates
- Bulk import from document repositories
- Integrate with document management systems

---

### 04-daily-summary-telegram.json
**Purpose**: Automated daily summary sent to Telegram with enhanced analytics

**Features**:
- Scheduled execution (daily at 8:00 PM)
- Enhanced system analytics from Cortex API
- Intelligent status indicators (healthy/idle/warning)
- Storage and database metrics
- Recent documents with file sizes
- System capabilities overview
- Actionable quick links

**Schedule**: Runs daily at 20:00 (8:00 PM) - customizable via cron expression

**Setup Required**:
1. Configure Telegram credentials in n8n
2. Get your Telegram chat ID
3. Update "Set Chat ID" node with your chat ID
4. Activate workflow

**How to Get Your Telegram Chat ID**:
```bash
# Method 1: Use a bot
1. Message your bot in Telegram
2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
3. Look for "chat":{"id":123456789}
4. Use that number as your chat_id

# Method 2: Use @userinfobot
1. Start chat with @userinfobot in Telegram
2. It will show your chat ID
```

**Example Summary Message**:
```
📊 Cortex Daily Summary
Monday, Jan 13, 08:00 PM

🟢 Healthy • System ready for queries

📚 Knowledge Base
• 3 documents • 85 chunks (~28.3 chunks/file)
• Storage: 0.45 MB • Database: 2.1 MB

Recent Documents:
1. `iso27001.pdf` (42 chunks, 245.7 KB)
2. `dummy.pdf` (1 chunks, 13.0 KB)
3. `policy-handbook.pdf` (42 chunks, 189.3 KB)

⚡ Capabilities
• 🤖 Agentic RAG mode
• Hybrid search (semantic + keyword)
• External knowledge via web search
• Comparison & calculation tools

Quick Actions:
→ /start - Query documents
→ 🌐 Web UI (http://localhost:8000)
→ 📤 Upload more documents
```

**Customization**:
- Change schedule: Edit cron expression in "Schedule Trigger" node
  - `0 20 * * *` = Daily at 8:00 PM
  - `0 9 * * *` = Daily at 9:00 AM
  - `0 18 * * 1` = Every Monday at 6:00 PM
- Change message format: Edit JavaScript in "Format Message" node
- Send to multiple chats: Duplicate "Send to Telegram" node with different chat IDs

---

## How to Import

### Method 1: Using n8n UI (Recommended)

1. Start Cortex with n8n:
   ```bash
   ./run_docker.sh
   # Select option 2
   ```

2. Open n8n: http://localhost:5678
   - Username: `admin` (default)
   - Password: `changeme123` (default)

3. Click **"Workflows"** → **"Import from File"**

4. Select workflow JSON file from this directory

5. Click **"Import"** → **"Save"**

6. Toggle **"Active"** to enable the workflow

### Method 2: Using n8n CLI (Advanced)

```bash
# Copy workflows to n8n data directory
docker cp n8n-workflows/01-web-search-tool.json cortex-n8n:/home/node/.n8n/

# Restart n8n to load workflows
docker restart cortex-n8n
```

## Workflow Details

### Web Search Tool Architecture

```
Webhook Trigger (POST /webhook/web-search)
    ↓
HTTP Request (DuckDuckGo API)
    ↓
Parse Results (JavaScript Node)
    ↓
Respond to Webhook (JSON)
```

**Input**:
```json
{
  "query": "your search query",
  "max_results": 5
}
```

**Output**:
```json
{
  "query": "your search query",
  "source": "duckduckgo",
  "results": [
    {
      "title": "Result title",
      "snippet": "Result description",
      "url": "https://example.com",
      "rank": 1
    }
  ],
  "count": 5,
  "success": true
}
```

### Telegram Bot Architecture

```
Telegram Trigger (New Message)
    ↓
Check if Command? (/start, /help)
    ├─ Yes → Send Help Message
    └─ No → Continue
         ↓
    Send "Processing..." Message
         ↓
    HTTP Request → Cortex API
    POST http://cortex:8080/api/query
    Body: {"query": "...", "session_id": "telegram_123", "mode": "agentic"}
         ↓
    Format Response (JavaScript Node)
    - Add emoji indicators
    - Format sources with page numbers
    - Add execution time
         ↓
    Send Answer (Telegram Message)
```

## Customization

### Changing Search Provider

To use a different search API (Brave, SerpAPI, Google):

1. Open workflow in n8n
2. Edit the **HTTP Request** node
3. Update URL and parameters
4. Edit **Parse Results** node to handle different response format
5. Save and test

### Adding More Commands to Telegram Bot

1. Open Telegram Bot workflow
2. Find the **Check if Command** (IF node)
3. Add more conditions for new commands
4. Add corresponding response nodes
5. Connect the nodes
6. Save and test

### Adjusting Response Format

Edit the **Format Response** JavaScript node to customize how answers are displayed in Telegram:

```javascript
// Example: Add confidence score to response
let message = `📚 Answer (${mode} mode):\n\n${answer}\n`;

// Add confidence indicator
if (confidence > 0.8) {
    message += '\n✅ High confidence answer\n';
} else if (confidence > 0.5) {
    message += '\n⚠️ Medium confidence answer\n';
} else {
    message += '\n❓ Low confidence answer\n';
}
```

## Troubleshooting

### Workflow Not Triggering

**Check**:
1. Workflow is activated (green toggle)
2. Webhook URL is correct in Cortex logs
3. n8n container is running: `docker ps | grep n8n`

**Test manually**:
```bash
# Test web search webhook
curl -X POST http://localhost:5678/webhook/web-search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Telegram Bot Not Responding

**Check**:
1. Bot token is correct in `.env`
2. Telegram credentials configured in n8n workflow
3. Cortex API accessible from n8n:
   ```bash
   docker exec cortex-n8n curl http://cortex:8080/api/health
   ```

### Execution Errors

**View logs**:
1. n8n UI → Click **"Executions"** tab
2. Find failed execution
3. Click to see error details
4. Check each node for error messages

**Common Issues**:
- API rate limits (add delays)
- Network connectivity (check Docker network)
- Invalid credentials (reconfigure in n8n)
- Timeout (increase timeout in HTTP Request node)

## Creating New Workflows

### Template: Document Upload Webhook

```json
{
  "name": "Document Upload Handler",
  "nodes": [
    {
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "document-upload",
        "httpMethod": "POST"
      }
    },
    {
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://cortex:8080/api/upload",
        "sendBody": true,
        "bodyContentType": "form-data"
      }
    },
    {
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "respondWith": "json"
      }
    }
  ]
}
```

### Best Practices

1. **Error Handling**: Add error handling nodes for API failures
2. **Logging**: Add Set nodes to log execution data
3. **Validation**: Validate input data before processing
4. **Timeouts**: Set appropriate timeouts for HTTP requests
5. **Testing**: Test workflows with various inputs before deploying
6. **Documentation**: Add notes to nodes explaining their purpose

## Resources

- **Full Setup Guide**: See `documentation/N8N_INTEGRATION.md`
- **n8n Documentation**: https://docs.n8n.io/
- **Workflow Examples**: https://n8n.io/workflows/
- **Community Forum**: https://community.n8n.io/

## Contributing

To contribute new workflows:

1. Create and test your workflow in n8n
2. Export the workflow (JSON format)
3. Add descriptive name: `XX-workflow-name.json`
4. Update this README with workflow description
5. Test the import process
6. Submit pull request with:
   - Workflow JSON file
   - Updated README
   - Screenshots (optional)
   - Example usage

## Support

For workflow-specific issues:
- Check n8n execution logs in the UI
- Review `documentation/N8N_INTEGRATION.md`
- Open issue on Cortex repository

For n8n platform issues:
- Visit https://community.n8n.io/
- Check https://docs.n8n.io/
