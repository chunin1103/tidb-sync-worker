# Unified TiDB + Agent Garden Service

🎯 **Single Render Web Service** hosting three integrated systems:

1. **TiDB MCP Server** - Query TiDB database from Claude (root level)
2. **Sync Worker** - Automated IDrive → TiDB data sync (root level)
3. **Agent Garden** - Autonomous agent management platform (`/AgentGarden`)

**Live URL:** https://gpt-mcp.onrender.com

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────┐
│           Render Web Service (unified_app.py)                 │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ROOT LEVEL ENDPOINTS (TiDB/Sync)                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  TiDB MCP Server                                    │    │
│  │  • POST /mcp      - MCP JSON-RPC for Claude        │    │
│  │  • GET  /tools    - List MCP tools                 │    │
│  │  • POST /query    - Direct SQL queries             │    │
│  │                                                     │    │
│  │  Sync Worker                                       │    │
│  │  • GET  /status   - Sync status/schedule           │    │
│  │  • POST /sync     - Trigger manual sync            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  /AgentGarden PREFIX (Agent Management)                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Agent Garden Platform                              │    │
│  │  • GET  /AgentGarden/                - Dashboard   │    │
│  │  • POST /AgentGarden/execute_agent   - Run agent   │    │
│  │  • GET  /AgentGarden/sessions        - Sessions    │    │
│  │  • GET  /AgentGarden/get_schedules   - Schedules   │    │
│  │  • 30+ more endpoints for full functionality       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │  TiDB   │          │ IDrive  │          │  Redis  │
    │  Cloud  │          │ Storage │          │ (Celery)│
    └─────────┘          └─────────┘          └─────────┘
```

## Quick Start

### Access the Services

**TiDB MCP (from Claude Code):**
```bash
claude mcp add tidb-mcp https://gpt-mcp.onrender.com/mcp --transport http
```

**Agent Garden Dashboard:**
```
https://gpt-mcp.onrender.com/AgentGarden/
```

**Sync Worker:**
```bash
# Check status
curl https://gpt-mcp.onrender.com/status

# Trigger manual sync
curl -X POST https://gpt-mcp.onrender.com/sync
```

## API Endpoints Reference

### Root Level - TiDB/Sync

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Unified health check |
| POST | `/mcp` | MCP JSON-RPC endpoint (Claude) |
| GET | `/tools` | List MCP tools |
| POST | `/query` | Direct SQL query (testing) |
| GET | `/status` | Sync status and schedule |
| POST | `/sync` | Trigger manual sync |

### /AgentGarden - Agent Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/AgentGarden/` | Dashboard UI |
| POST | `/AgentGarden/execute_agent` | Execute agent with SSE streaming |
| GET | `/AgentGarden/sessions` | Get active sessions |
| GET | `/AgentGarden/get_sessions` | Get all chat sessions |
| POST | `/AgentGarden/clear_session` | Clear session history |
| GET | `/AgentGarden/load_session/<id>` | Load session conversation |
| GET | `/AgentGarden/export_session/<id>/<format>` | Export session (json/md/txt) |
| GET | `/AgentGarden/get_agent_runs` | Get autonomous agent runs |
| GET | `/AgentGarden/get_agent_reports` | Get agent-generated reports |
| POST | `/AgentGarden/mark_report_read/<id>` | Mark report as read |
| POST | `/AgentGarden/trigger_agent_task` | Manually trigger agent task |
| GET | `/AgentGarden/get_task_status/<id>` | Check Celery task status |
| GET | `/AgentGarden/get_schedules` | Get all schedules |
| GET | `/AgentGarden/get_schedule/<name>` | Get specific schedule |
| POST | `/AgentGarden/update_schedule/<name>` | Update schedule |
| GET | `/AgentGarden/celery_status` | Check if Celery Beat is running |
| POST | `/AgentGarden/restart_celery_beat` | Restart Celery Beat |
| GET | `/AgentGarden/get_settings` | Get system settings |
| GET | `/AgentGarden/get_timezones` | Get available timezones |
| POST | `/AgentGarden/update_timezone` | Update system timezone |
| GET | `/AgentGarden/health` | Agent Garden health check |

## MCP Tools (for Claude)

| Tool | Description |
|------|-------------|
| `query` | Run any SELECT query |
| `list_tables` | List all tables in the database |
| `describe_table` | Get schema of a specific table |
| `recent_orders` | Get recent orders (shortcut) |
| `today_orders` | Get all orders placed today |
| `order_details` | Get full order with products and totals |

### Example Claude Queries

Once connected, ask Claude:
- "Show me the most recent orders"
- "What tables are in the database?"
- "Describe the orders table"
- "SELECT * FROM products WHERE products_price > 100 LIMIT 10"
- "Show me all orders placed today"

## Environment Variables

### TiDB Configuration (Required)
- `TIDB_HOST` - TiDB host (default: `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`)
- `TIDB_PORT` - TiDB port (default: `4000`)
- `TIDB_USER` - **Required** - TiDB username
- `TIDB_PASSWORD` - **Required** - TiDB password
- `TIDB_DATABASE` - Database name (default: `test`)

### IDrive Sync Configuration (Required)
- `IDRIVE_ACCESS_KEY` - **Required** - IDrive access key
- `IDRIVE_SECRET_KEY` - **Required** - IDrive secret key
- `IDRIVE_ENDPOINT` - **Required** - IDrive S3 endpoint
- `IDRIVE_BUCKET` - Bucket name (default: `dbdaily`)

### MCP Configuration
- `MAX_QUERY_ROWS` - Max rows to return (default: `1000`)

### Agent Garden Configuration (Optional)
- `GOOGLE_API_KEY` - Google Gemini API key for AI agents
- `REDIS_URL` - Redis URL for Celery background tasks
- `FLASK_DEBUG` - Debug mode (default: `False`)

### Server Configuration
- `PORT` - Server port (default: `8080`)

## Project Structure

```
render-tidb-sync/
├── unified_app.py              # Main unified Flask application
├── mcp_server.py              # TiDB MCP server implementation
├── sync_worker.py             # Sync worker with scheduling
├── requirements.txt           # Merged Python dependencies
├── render.yaml               # Render deployment configuration
├── README.md                 # This file
├── MERGE_GUIDE.md           # Detailed merge documentation
│
└── agent_garden/            # Agent Garden application
    ├── app.py               # Agent Garden launcher
    ├── src/
    │   ├── core/
    │   │   ├── app.py              # Main Agent Garden Flask app
    │   │   ├── agent_backend.py    # Agent execution engine
    │   │   └── database.py         # Database layer
    │   ├── scheduling/
    │   ├── connectors/
    │   └── utils/
    ├── templates/           # HTML templates
    ├── autonomous_agents/   # Autonomous agent definitions
    └── docs/               # Agent Garden documentation
```

## Features

### TiDB MCP Server ✅
- Read-only SQL queries from Claude
- JSON-RPC 2.0 protocol
- Safety limits (max rows)
- Table listing and schema inspection
- Convenience queries (recent orders, order details)

### Sync Worker ✅
- Scheduled syncs (6 AM / 6 PM UTC)
- Manual sync trigger via API
- IDrive S3-compatible storage
- Status monitoring
- Error handling and logging

### Agent Garden ✅
- Interactive agent chat with SSE streaming
- Multiple agent types (inventory, analytics, etc.)
- Session management and history
- Export conversations (JSON/Markdown/Text)
- Autonomous scheduled agents (Celery)
- Agent-generated reports
- Schedule management UI
- Timezone configuration
- PostgreSQL/SQLite database support

## Deployment to Render

### Using render.yaml (Recommended)

The repository includes `render.yaml` for easy deployment:

1. Push to GitHub
2. Connect repository to Render
3. Render will automatically detect `render.yaml`
4. Set required environment variables in dashboard
5. Deploy!

### Manual Setup

**Service Config:**
- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python unified_app.py`
- **Health Check Path:** `/`

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TIDB_USER="your_user"
export TIDB_PASSWORD="your_password"
export TIDB_HOST="gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
export TIDB_PORT="4000"
export TIDB_DATABASE="test"
export IDRIVE_ACCESS_KEY="your_key"
export IDRIVE_SECRET_KEY="your_secret"
export IDRIVE_ENDPOINT="https://endpoint.idrivee2.com"
export GOOGLE_API_KEY="your_gemini_key"  # Optional

# Run unified app
python unified_app.py
```

### Access Locally

- **TiDB MCP**: `http://localhost:8080/mcp`
- **Agent Garden**: `http://localhost:8080/AgentGarden/`
- **Health Check**: `http://localhost:8080/`

## Sync Schedule

The sync scheduler runs at:
- **6:00 AM UTC** (1 hour after 05:00 backup)
- **6:00 PM UTC** (1 hour after 17:00 backup)

## Documentation

- **[MERGE_GUIDE.md](MERGE_GUIDE.md)** - Detailed guide on the merge process
- **[SYNC_INSTRUCTIONS.md](SYNC_INSTRUCTIONS.md)** - Sync worker setup
- **[agent_garden/docs/](agent_garden/docs/)** - Agent Garden documentation

## Testing

### Test MCP Endpoint
```bash
curl -X POST https://gpt-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Query Tables
```bash
curl -X POST https://gpt-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_tables","arguments":{}},"id":2}'
```

### Check Agent Garden
```bash
curl https://gpt-mcp.onrender.com/AgentGarden/health
```

## License

MIT
