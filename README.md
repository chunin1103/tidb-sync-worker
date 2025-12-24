# TiDB Unified Service

A single Render web service providing:
1. **Sync Worker** - Syncs IDrive e2 backups to TiDB Cloud (6 AM / 6 PM UTC)
2. **MCP Server** - Query TiDB directly from Claude via MCP protocol

**Live URL:** https://gpt-mcp.onrender.com

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check (combined status) |
| `/status` | GET | Sync status & next scheduled run |
| `/sync` | POST | Trigger manual sync |
| `/sync` | GET | Info about last sync |
| `/mcp` | POST | MCP JSON-RPC endpoint for Claude |
| `/tools` | GET | List available MCP tools |
| `/query` | POST | Direct query endpoint (for testing) |

## MCP Tools

| Tool | Description |
|------|-------------|
| `query` | Run any SELECT query |
| `list_tables` | List all tables in the database |
| `describe_table` | Get schema of a specific table |
| `recent_orders` | Get recent orders (shortcut) |
| `order_details` | Get full order with products and totals |

## Using with Claude Code

### Option 1: Project-level config (recommended for teams)

The `.mcp.json` file in the Claude Tools folder configures MCP servers for everyone:

```json
{
  "mcpServers": {
    "render": {
      "type": "http",
      "url": "https://mcp.render.com/sse"
    },
    "tidb-mcp": {
      "type": "http",
      "url": "https://gpt-mcp.onrender.com/mcp"
    }
  }
}
```

When you open the folder in Claude Code, you'll be prompted to approve these servers.

### Option 2: Manual setup

```bash
claude mcp add tidb-mcp https://gpt-mcp.onrender.com/mcp --transport http
```

### Example queries

Once connected, ask Claude:
- "Show me the most recent orders"
- "What tables are in the database?"
- "Describe the orders table"
- "SELECT * FROM products WHERE products_price > 100 LIMIT 10"

## Deployment

### Environment Variables (set in Render Dashboard)

| Variable | Description |
|----------|-------------|
| `TIDB_HOST` | TiDB Cloud gateway host |
| `TIDB_PORT` | TiDB port (usually 4000) |
| `TIDB_USER` | TiDB username |
| `TIDB_PASSWORD` | TiDB password |
| `TIDB_DATABASE` | Database name |
| `IDRIVE_ACCESS_KEY` | IDrive e2 access key |
| `IDRIVE_SECRET_KEY` | IDrive e2 secret key |
| `IDRIVE_ENDPOINT` | IDrive e2 endpoint URL |
| `IDRIVE_BUCKET` | S3 bucket name (default: dbdaily) |
| `MAX_QUERY_ROWS` | Max rows per MCP query (default: 1000) |

### Service Config

- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python sync_worker.py`
- **Health Check Path:** `/`

## Schedule

The sync scheduler runs at:
- **6:00 AM UTC** (1 hour after 05:00 backup)
- **6:00 PM UTC** (1 hour after 17:00 backup)

## Usage

### Check status
```bash
curl https://gpt-mcp.onrender.com/status
```

### Trigger manual sync
```bash
curl -X POST https://gpt-mcp.onrender.com/sync
```

### Test MCP endpoint
```bash
curl -X POST https://gpt-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Query tables
```bash
curl -X POST https://gpt-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_tables","arguments":{}},"id":2}'
```
