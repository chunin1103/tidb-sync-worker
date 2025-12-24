# TiDB Sync & MCP Server

Two services for working with TiDB Cloud:

1. **Sync Worker** - Syncs IDrive e2 backups to TiDB Cloud on schedule
2. **MCP Server** - Query TiDB directly from Claude via MCP protocol

**No Docker required** - uses native Python runtime.

## Services

### Sync Worker (`sync_worker.py`)
- **Auto-sync twice daily** at 6 AM and 6 PM UTC (via APScheduler)
- **Manual sync** via POST /sync endpoint
- **Status monitoring** via /status endpoint

### MCP Server (`mcp_server.py`)
- **Query TiDB from Claude** via MCP protocol
- **Read-only access** - only SELECT queries allowed
- **Built-in tools**: query, list_tables, describe_table, recent_orders, order_details

## API Endpoints

### Sync Worker (port 10000)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/status` | GET | Detailed sync status + next scheduled run |
| `/sync` | POST | Trigger manual sync |
| `/sync` | GET | Info about last sync |

### MCP Server (port 8080)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/mcp` | POST | MCP JSON-RPC endpoint |
| `/tools` | GET | List available tools |
| `/query` | POST | Direct query endpoint (for testing)

## Deployment

### If you have an existing Render web service:

1. In Render Dashboard, go to your service settings
2. Change the **Repository** to this repo
3. Add the environment variables below
4. Deploy!

### Fresh deployment:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect `chunin1103/tidb-sync-worker`
4. Configure:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python sync_worker.py`
   - **Health Check Path:** `/`
5. Add environment variables below
6. Deploy!

## Environment Variables

| Variable | Value |
|----------|-------|
| `TIDB_HOST` | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` |
| `TIDB_PORT` | `4000` |
| `TIDB_USER` | `3oTjjLfAngfGpch.root` |
| `TIDB_PASSWORD` | `WGHj057dYRCzAsyV` |
| `TIDB_DATABASE` | `test` |
| `IDRIVE_ACCESS_KEY` | (your IDrive access key) |
| `IDRIVE_SECRET_KEY` | (your IDrive secret key) |
| `IDRIVE_ENDPOINT` | `https://k8j8.or4.idrivee2-57.com` |
| `IDRIVE_BUCKET` | `dbdaily` |

## Usage

### Check status
```bash
curl https://your-service.onrender.com/status
```

### Trigger manual sync
```bash
curl -X POST https://your-service.onrender.com/sync
```

### Monitor sync progress
```bash
# Keep checking status until is_running becomes false
curl https://your-service.onrender.com/status
```

## Logs

View logs in Render Dashboard → Your Service → Logs

Example:
```
2025-12-23 06:00:00 [INFO] Scheduled sync triggered
2025-12-23 06:00:00 [INFO] TiDB Sync Starting
2025-12-23 06:00:01 [INFO] Connecting to TiDB Cloud...
2025-12-23 06:00:01 [INFO] Connected!
2025-12-23 06:00:02 [INFO] PHASE 1: Categories/Products
...
2025-12-23 06:25:00 [INFO] SYNC COMPLETE - SUCCESS
```

## Schedule

The scheduler runs at:
- **6:00 AM UTC** (1 hour after 05:00 backup)
- **6:00 PM UTC** (1 hour after 17:00 backup)

To change the schedule, modify these lines in `sync_worker.py`:
```python
scheduler.add_job(scheduled_sync, CronTrigger(hour=6, minute=0), ...)
scheduler.add_job(scheduled_sync, CronTrigger(hour=18, minute=0), ...)
```

## Connecting Claude Code to MCP Server

After deploying the MCP server to Render, add it to Claude Code:

```bash
claude mcp add --transport http tidb https://tidb-mcp-server.onrender.com/mcp
```

Then you can ask Claude things like:
- "Show me the most recent orders"
- "What tables are in the database?"
- "Describe the orders table"
- "SELECT * FROM products WHERE products_price > 100 LIMIT 10"

## MCP Tools

| Tool | Description |
|------|-------------|
| `query` | Run any SELECT query |
| `list_tables` | List all tables in the database |
| `describe_table` | Get schema of a specific table |
| `recent_orders` | Get recent orders (shortcut) |
| `order_details` | Get full order with products and totals |
