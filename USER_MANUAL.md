# Gemini-Claude Task System - User Manual

**Version**: 2.0
**Last Updated**: 2025-12-30
**Author**: Claude Task Executor Team

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the System Locally](#running-the-system-locally)
6. [Using the System](#using-the-system)
7. [System Architecture](#system-architecture)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## System Overview

### What is This System?

The Gemini-Claude Task System is a **multi-agent collaboration platform** that allows:

- **Gemini (Web Interface)**: Acts as the "front-end" - interacts with users and creates tasks
- **Claude (Local Executor)**: Acts as the "back-end" - executes tasks using Claude Code CLI (FREE with Claude Pro)
- **TiDB Cloud**: Provides real-time business data (orders, customers, products)
- **OneDrive**: Stores generated reports and syncs across devices

### Key Features

✅ **FREE Execution**: Uses Claude Code CLI (included with Claude Pro subscription)
✅ **Real Business Data**: Queries live TiDB database with 134,277+ orders
✅ **Hybrid Architecture**: Python executor + Claude CLI analysis
✅ **Auto-Sync Reports**: Reports automatically sync to OneDrive
✅ **Task Queue**: Gemini creates tasks, Claude executes autonomously

### Use Cases

1. **Daily Sales Reports**: Analyze today's orders, revenue, top products
2. **Inventory Intelligence**: Low stock alerts, reorder recommendations
3. **Customer Insights**: Geographic distribution, purchase patterns
4. **Scheduled Reports**: Morning intelligence, weekly summaries

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **macOS** | 10.15+ | Operating system | Pre-installed |
| **Python** | 3.8+ | Runtime environment | `brew install python3` |
| **Claude Code CLI** | Latest | Task execution (FREE) | See below |
| **OneDrive Desktop** | Latest | File sync | Download from Microsoft |
| **Git** | Any | Version control | `brew install git` |

### Required Accounts

| Service | Purpose | Sign Up |
|---------|---------|---------|
| **Claude Pro** | Access to Claude Code CLI | https://claude.ai/upgrade |
| **TiDB Cloud** | Database access | https://tidbcloud.com |
| **Neon PostgreSQL** | Task queue storage | https://neon.tech |
| **Upstash Redis** | Cache & queue (optional) | https://upstash.com |
| **OneDrive** | Report storage | https://onedrive.com |

### Installing Claude Code CLI

**Step 1**: Verify Claude Pro subscription
```bash
# Visit https://claude.ai/settings/billing
# Confirm "Claude Pro" plan is active
```

**Step 2**: Install Claude Code CLI
```bash
# Download installer from official site
# Visit: https://claude.ai/download

# Or install via Homebrew (macOS)
brew install anthropics/claude/claude-code

# Verify installation
claude --version
# Expected output: claude-code version 1.x.x
```

**Step 3**: Authenticate
```bash
# Login to Claude Code
claude auth login

# This will open a browser window
# Sign in with your Claude Pro account
# Verify authentication
claude auth status
# Expected output: Authenticated as: your-email@example.com
```

---

## Installation

### Step 1: Clone the Repository

```bash
# Navigate to OneDrive folder
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/

# Clone the project (if not already present)
# If already cloned, skip to next step

# Verify project exists
ls -la render-tidb-sync/
# You should see: unified_app.py, claude_executor.py, agent_garden/, etc.
```

### Step 2: Install Python Dependencies

```bash
# Navigate to project directory
cd render-tidb-sync

# Install core dependencies
pip3 install flask requests python-dotenv pymysql

# Install Agent Garden dependencies
pip3 install sqlalchemy celery redis apscheduler google-generativeai

# Verify installations
pip3 list | grep -E "flask|requests|sqlalchemy|celery"
```

**Expected Output:**
```
Flask                 3.0.0
requests              2.31.0
SQLAlchemy            2.0.23
celery                5.3.4
```

### Step 3: Verify File Structure

```bash
# Check critical files exist
ls -1 render-tidb-sync/

# Expected output:
# unified_app.py          ← Main server
# claude_executor.py      ← Task executor
# mcp_server.py          ← TiDB MCP interface
# sync_worker.py         ← Database sync
# agent_garden/          ← Agent configuration
# templates/             ← HTML templates
# USER_MANUAL.md         ← This file
```

---

## Configuration

### Step 1: Configure Environment Variables

**File Location**: `render-tidb-sync/agent_garden/.env`

```bash
# Open .env file
nano agent_garden/.env
```

**Required Configuration:**

```bash
# Google Gemini API (for future agent use)
GOOGLE_API_KEY=AIzaSyD6CLJVxJcNMCD3yKM1cooOeO4-kmRiTBo

# Neon PostgreSQL (Task Queue Database)
DATABASE_URL=postgresql://neondb_owner:npg_dK9LXyv3kAlh@ep-cool-frost-a1b6dm71-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Upstash Redis (Optional - for Celery)
REDIS_URL=rediss://default:AXWRAAIncDFhM2Q5YWVkYmYzZGM0YTIyODY2ZWM5OTZiOWYxNzA4MnAxMzAwOTc@tidy-oriole-30097.upstash.io:6379

# TiDB Cloud (Business Data)
TIDB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=3oTjjLfAngfGpch.root
TIDB_PASSWORD=WGHj057dYRCzAsyV
TIDB_DATABASE=test
```

**Save and Exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Configure MCP Server for Claude Code CLI

**File Location**: `render-tidb-sync/.mcp.json`

```bash
# Create MCP configuration
nano .mcp.json
```

**Content:**

```json
{
  "mcpServers": {
    "tidb-mcp": {
      "type": "sse",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

**What this does:**
- Tells Claude Code CLI to use local MCP server
- Enables access to 6 TiDB tools: `query`, `list_tables`, `describe_table`, `today_orders`, `recent_orders`, `order_details`
- Uses SSE (Server-Sent Events) transport for non-interactive execution

### Step 3: Configure OneDrive Sync

**Step 3.1**: Verify OneDrive is installed

```bash
# Check OneDrive status
ls -la ~/Library/CloudStorage/

# You should see: OneDrive-Personal/
```

**Step 3.2**: Enable sync for project folder

1. Open **OneDrive** app (menu bar icon)
2. Click **Preferences** > **Account** > **Choose folders**
3. Ensure `Claude Tools/render-tidb-sync` is checked ✅
4. Ensure `Claude Tools/Reports` is checked ✅
5. Click **OK**

**Step 3.3**: Verify sync is active

```bash
# Check OneDrive sync status
# Green checkmark = synced
# Blue cloud = syncing
# Red X = sync error

# List files to verify access
ls ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/
# Expected: render-tidb-sync, Reports, Production, etc.
```

---

## Running the System Locally

### Overview

The system consists of **2 processes** that must run simultaneously:

1. **Unified App Server** (`unified_app.py`) - Hosts API endpoints
2. **Claude Executor** (`claude_executor.py`) - Polls and executes tasks

### Starting the System

#### Terminal 1: Start Unified App Server

```bash
# Navigate to project
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/render-tidb-sync

# Start server
python3 unified_app.py
```

**Expected Output:**

```
2025-12-30 16:12:11 [INFO] 🚀 Initializing Unified Flask App...
2025-12-30 16:12:11 [INFO] ✅ TiDB MCP Server routes registered (root level)
2025-12-30 16:12:11 [INFO]    - GET  /         - Health check
2025-12-30 16:12:11 [INFO]    - POST /mcp      - MCP endpoint
2025-12-30 16:12:11 [INFO]    - GET  /tools    - List tools
2025-12-30 16:12:11 [INFO] ✅ Agent Garden registered at /AgentGarden
2025-12-30 16:12:11 [INFO]
2025-12-30 16:12:11 [INFO] ================================================================================
2025-12-30 16:12:11 [INFO] 🎯 UNIFIED FLASK APPLICATION STARTED
2025-12-30 16:12:11 [INFO] ================================================================================
2025-12-30 16:12:11 [INFO] 🌐 Server URL: http://0.0.0.0:8080
2025-12-30 16:12:11 [INFO] 🔧 TiDB MCP Endpoint: http://localhost:8080/mcp
2025-12-30 16:12:11 [INFO] 🤖 Agent Garden UI: http://localhost:8080/AgentGarden/
2025-12-30 16:12:11 [INFO] 📊 Health Check: http://localhost:8080/
2025-12-30 16:12:11 [INFO] ================================================================================
 * Running on http://127.0.0.1:8080
```

✅ **Server is ready when you see**: `Running on http://127.0.0.1:8080`

**Verify Server is Running:**

```bash
# Open a new terminal and test
curl http://localhost:8080/

# Expected output:
# {"database":"test","service":"tidb-mcp-server","status":"healthy"}
```

#### Terminal 2: Start Claude Executor

```bash
# Navigate to project
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/render-tidb-sync

# Start executor with localhost MCP server
MCP_SERVER="http://localhost:8080" python3 claude_executor.py
```

**Expected Output:**

```
[2025-12-30 16:15:55] INFO: ======================================================================
[2025-12-30 16:15:55] INFO: 🚀 CLAUDE TASK EXECUTOR STARTED
[2025-12-30 16:15:55] INFO: ======================================================================
[2025-12-30 16:15:55] INFO: 📡 Polling: http://localhost:8080
[2025-12-30 16:15:55] INFO: ⏱️  Interval: Every 30 seconds
[2025-12-30 16:15:55] INFO: 📁 OneDrive: /Users/vusmac/Library/CloudStorage/OneDrive-Personal
[2025-12-30 16:15:55] INFO: ======================================================================
```

✅ **Executor is ready when you see**: Polling messages every 30 seconds

**What the Executor Does:**

- Polls `http://localhost:8080/AgentGarden/tasks/ready` every 30 seconds
- When a task is found:
  1. Marks task as `in_progress`
  2. Fetches database context from MCP server
  3. Calls Claude Code CLI to analyze data
  4. Saves report to OneDrive
  5. Marks task as `completed`

---

## Using the System

### Method 1: Create Task via cURL (Testing)

**Step 1**: Open a new terminal (keep server + executor running)

**Step 2**: Create a test task

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "task_json": {
      "agent_type": "inventory_intelligence",
      "report_title": "Daily Sales Analysis",
      "report_type": "daily_report",
      "prompt": "Analyze today'\''s orders. Provide: total orders, total revenue, top 3 products, and geographic distribution by state.",
      "output": {
        "path": "Claude Tools/Reports/inventory_intelligence",
        "filename_pattern": "daily_sales_{date}.md"
      }
    },
    "created_by": "manual_test"
  }'
```

**Expected Response:**

```json
{
  "success": true,
  "task_id": 19,
  "message": "Task created successfully",
  "scheduled": false
}
```

**Step 3**: Wait 30 seconds for executor to pick up task

**Step 4**: Check task status

```bash
curl http://localhost:8080/AgentGarden/tasks/19 | python3 -m json.tool
```

**Expected Response (when completed):**

```json
{
  "success": true,
  "task": {
    "id": 19,
    "status": "completed",
    "result_path": "Claude Tools/Reports/inventory_intelligence/daily_sales_2025-12-30.md",
    "result_summary": "Generated Daily Sales Analysis (inventory_intelligence)",
    "execution_count": 1,
    "completed_at": "2025-12-30T16:25:42.123456"
  },
  "execution_history": [...]
}
```

**Step 5**: View the generated report

```bash
# Navigate to OneDrive reports folder
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/Reports/inventory_intelligence/

# List reports
ls -lt

# View latest report
cat daily_sales_2025-12-30.md
```

### Method 2: Create Task via Python Script

**Create a script**: `create_task.py`

```python
#!/usr/bin/env python3
import requests
import json

# Define task
task = {
    "task_type": "agent_report",
    "task_json": {
        "agent_type": "inventory_intelligence",
        "report_title": "Weekly Inventory Report",
        "report_type": "weekly",
        "prompt": "Analyze the past 7 days of orders. Identify: trending products, slow-moving inventory, and restock recommendations.",
        "output": {
            "path": "Claude Tools/Reports/inventory_intelligence",
            "filename_pattern": "weekly_inventory_{date}.md"
        }
    },
    "created_by": "automated_script"
}

# Create task
response = requests.post(
    "http://localhost:8080/AgentGarden/tasks/create",
    json=task
)

# Print result
result = response.json()
print(f"✅ Task created: ID {result['task_id']}")
print(f"📊 Check status at: http://localhost:8080/AgentGarden/tasks/{result['task_id']}")
```

**Run the script:**

```bash
python3 create_task.py
```

### Method 3: Schedule Recurring Tasks

**Create scheduled task:**

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "task_json": {
      "agent_type": "inventory_intelligence",
      "report_title": "Morning Intelligence Report",
      "report_type": "scheduled",
      "prompt": "Analyze yesterday'\''s orders and today'\''s pending orders. Provide actionable insights for today'\''s operations.",
      "output": {
        "path": "Claude Tools/Reports/intelligence",
        "filename_pattern": "morning_report_{date}.md"
      }
    },
    "schedule_cron": "0 7 * * *",
    "created_by": "scheduler"
  }'
```

**Cron Schedule Examples:**

| Cron Expression | When | Description |
|----------------|------|-------------|
| `0 7 * * *` | 7:00 AM daily | Morning report |
| `0 18 * * *` | 6:00 PM daily | End-of-day summary |
| `*/30 * * * *` | Every 30 min | Real-time monitoring |
| `0 9 * * 1` | 9:00 AM Monday | Weekly summary |
| `0 0 1 * *` | Midnight 1st of month | Monthly report |

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                        │
│  (Gemini Web Interface, cURL, Python Scripts)              │
└────────────────────┬────────────────────────────────────────┘
                     │ POST /AgentGarden/tasks/create
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              UNIFIED APP SERVER (Flask)                     │
│                http://localhost:8080                        │
├─────────────────────────────────────────────────────────────┤
│  Endpoints:                                                 │
│  - POST /AgentGarden/tasks/create      (Create task)       │
│  - GET  /AgentGarden/tasks/ready       (Get pending tasks) │
│  - POST /AgentGarden/tasks/{id}/start  (Mark in progress)  │
│  - POST /AgentGarden/tasks/{id}/complete (Mark done)       │
│  - POST /mcp                           (MCP JSON-RPC)       │
│  - GET  /tools                         (List MCP tools)     │
└────────┬────────────────────────┬───────────────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌──────────────────────┐  ┌──────────────────────┐
│  NEON POSTGRESQL     │  │    TiDB CLOUD        │
│  (Task Queue)        │  │  (Business Data)     │
├──────────────────────┤  ├──────────────────────┤
│ - claude_tasks table │  │ - orders (646K rows) │
│ - Stores task state  │  │ - customers          │
│ - Execution history  │  │ - products           │
└──────────────────────┘  │ - categories         │
                          └──────────────────────┘
                                   ▲
                                   │ Direct TiDB queries
                                   │
┌─────────────────────────────────────────────────────────────┐
│           CLAUDE EXECUTOR (Python Process)                  │
│                  claude_executor.py                         │
├─────────────────────────────────────────────────────────────┤
│  1. Polls /AgentGarden/tasks/ready every 30 seconds        │
│  2. Fetches database context via direct MCP HTTP calls     │
│  3. Calls: claude --print "<prompt with data>"             │
│  4. Saves report to OneDrive                                │
│  5. Marks task complete                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ subprocess.run(['claude', '--print', ...])
                 ▼
┌─────────────────────────────────────────────────────────────┐
│          CLAUDE CODE CLI (FREE with Pro)                    │
│                  Anthropic Claude                           │
├─────────────────────────────────────────────────────────────┤
│  - Receives: Task prompt + Database context (JSON)         │
│  - Analyzes: Order patterns, inventory trends, insights    │
│  - Generates: Markdown report with recommendations         │
│  - Returns: Report text to executor                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Write report file
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    ONEDRIVE SYNC                            │
│  ~/Library/CloudStorage/OneDrive-Personal/Claude Tools/    │
├─────────────────────────────────────────────────────────────┤
│  Reports/                                                   │
│  └── inventory_intelligence/                                │
│      ├── daily_sales_2025-12-30.md                         │
│      ├── weekly_inventory_2025-12-30.md                    │
│      └── e2e_test_20251230_161758.md ✅ (Latest)           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. Task Creation (Gemini → Server)**

```
User/Gemini
    ↓ POST /AgentGarden/tasks/create
Unified App Server
    ↓ INSERT INTO claude_tasks
Neon PostgreSQL
    ↓ Return task_id
User/Gemini (receives task_id=19)
```

**2. Task Execution (Executor → Claude CLI)**

```
Claude Executor (every 30s)
    ↓ GET /AgentGarden/tasks/ready
Unified App Server
    ↓ SELECT * FROM claude_tasks WHERE status='pending'
Neon PostgreSQL
    ↓ Return task list
Claude Executor
    ↓ POST /AgentGarden/tasks/19/start
    ↓ POST /mcp (JSON-RPC: tools/call, name: recent_orders)
Unified App Server
    ↓ SELECT * FROM orders ORDER BY date_purchased DESC LIMIT 5
TiDB Cloud
    ↓ Return order data (JSON)
Claude Executor
    ↓ Build prompt with data
    ↓ subprocess.run(['claude', '--print', prompt])
Claude Code CLI (FREE)
    ↓ Analyze data + Generate report
    ↓ Return report markdown
Claude Executor
    ↓ Write to OneDrive: Reports/inventory_intelligence/report.md
    ↓ POST /AgentGarden/tasks/19/complete
Unified App Server
    ↓ UPDATE claude_tasks SET status='completed', result_path='...'
Neon PostgreSQL
```

**3. Report Sync (OneDrive)**

```
Claude Executor writes file
    ↓
OneDrive Desktop App detects change
    ↓
File syncs to OneDrive cloud
    ↓
File available on all devices (web, mobile, other PCs)
```

### Database Schema

**Neon PostgreSQL** (`claude_tasks` table):

```sql
CREATE TABLE claude_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,           -- 'agent_report', 'query_execution', etc.
    task_json JSONB NOT NULL,                  -- Task parameters
    status VARCHAR(50) DEFAULT 'pending',      -- 'pending', 'in_progress', 'completed', 'failed'
    created_by VARCHAR(100),                   -- 'gemini', 'manual_test', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_path TEXT,                          -- Path to generated report
    result_summary TEXT,                       -- Brief description
    error_log TEXT,                            -- Error details if failed
    schedule_cron VARCHAR(100),                -- Cron expression for scheduled tasks
    schedule_enabled BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_execution_at TIMESTAMP
);
```

**TiDB Cloud** (Business Data):

- `orders` - 646,096 rows - Customer orders
- `orders_products` - Order line items
- `orders_status_history` - Order lifecycle
- `customers` - Customer accounts
- `customers_info` - Demographics, addresses
- `products` - Product catalog
- `categories` - Product categories

---

## Troubleshooting

### Issue 1: Server Won't Start - Port Already in Use

**Error:**

```
Address already in use
Port 8080 is in use by another program.
```

**Solution:**

```bash
# Find process using port 8080
lsof -i :8080

# Output:
# COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python  12345  vusmac   3u  IPv4  0x...      0t0  TCP *:8080 (LISTEN)

# Kill the process
kill -9 12345

# Verify port is free
lsof -i :8080
# (no output = port is free)

# Restart server
python3 unified_app.py
```

### Issue 2: Executor Not Picking Up Tasks - 404 Errors

**Error in executor log:**

```
[ERROR] Error polling tasks: 404 Client Error: NOT FOUND for url: http://localhost:8080/AgentGarden/tasks/ready
```

**Cause**: Executor is using old endpoint path or server not fully started

**Solution:**

```bash
# 1. Verify server is running
curl http://localhost:8080/
# Should return: {"status":"healthy"...}

# 2. Test task endpoint directly
curl http://localhost:8080/AgentGarden/tasks/ready
# Should return: {"success":true,"tasks":[],"count":0}

# 3. If 404, restart server
pkill -f unified_app.py
sleep 3
python3 unified_app.py

# 4. Restart executor with correct MCP_SERVER
pkill -f claude_executor.py
MCP_SERVER="http://localhost:8080" python3 claude_executor.py
```

### Issue 3: TiDB Password Authentication Failed

**Error:**

```
Access denied for user '3oTjjLfAngfGpch.root'@'xxx.xxx.xxx.xxx' (using password: YES)
```

**Cause**: Password in `.env` file is incorrect or outdated

**Solution:**

```bash
# 1. Check .env file
cat agent_garden/.env | grep TIDB_PASSWORD
# Current: TIDB_PASSWORD=WGHj057dYRCzAsyV

# 2. Get correct password from TiDB Cloud dashboard
# Login to: https://tidbcloud.com
# Navigate to: Clusters → Your Cluster → Connection
# Copy the password

# 3. Update .env file
nano agent_garden/.env
# Replace password, save and exit (Ctrl+X, Y, Enter)

# 4. Restart server to load new password
pkill -f unified_app.py
python3 unified_app.py
```

### Issue 4: OneDrive Sync Not Working - Reports Not Appearing

**Cause**: OneDrive Desktop app not syncing the folder

**Solution:**

```bash
# 1. Check if OneDrive is running
ps aux | grep -i onedrive
# Should see: OneDrive.app process

# 2. Check sync status
ls -la ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/Reports/

# 3. If folder doesn't exist, create it
mkdir -p ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/Reports/inventory_intelligence/

# 4. Open OneDrive preferences
# Click OneDrive icon in menu bar → Preferences

# 5. Verify "Claude Tools" folder is selected for sync
# Account tab → Choose folders → Check "Claude Tools" ✅

# 6. Manually trigger sync
# Right-click OneDrive icon → Sync now

# 7. Verify files appear
ls -la ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/Reports/inventory_intelligence/
```

### Issue 5: Claude Code CLI Not Found

**Error:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'claude'
```

**Cause**: Claude Code CLI not installed or not in PATH

**Solution:**

```bash
# 1. Check if Claude CLI is installed
which claude
# Should return: /usr/local/bin/claude or similar

# If not found:
# 2. Install Claude Code CLI
brew install anthropics/claude/claude-code

# 3. Verify installation
claude --version

# 4. Authenticate
claude auth login

# 5. Test MCP tools
claude --print "List all available MCP tools"
```

### Issue 6: Executor Crashes During Task Execution

**Error in log:**

```
[ERROR] ❌ Failed to execute Claude Code CLI: Command '['claude', '--print', ...]' returned non-zero exit status 1
```

**Cause**: Claude CLI received invalid prompt or timed out

**Solution:**

```bash
# 1. Check executor log for full error
tail -50 claude_executor.log

# 2. Test Claude CLI manually
claude --print "Test: Analyze this data: {\"test\": \"value\"}"

# 3. If timeout issue, increase timeout in claude_executor.py
# Edit line 367:
nano claude_executor.py
# Change: timeout=300 → timeout=600 (10 minutes)

# 4. Restart executor
pkill -f claude_executor.py
MCP_SERVER="http://localhost:8080" python3 claude_executor.py
```

### Issue 7: Task Stuck in "in_progress" Status

**Cause**: Executor crashed mid-execution or killed

**Solution:**

```bash
# 1. Check task status
curl http://localhost:8080/AgentGarden/tasks/19 | python3 -m json.tool

# 2. If status is "in_progress" for >10 minutes:
# Option A: Wait for executor to retry (not implemented yet)

# Option B: Manually reset task to pending
# (Requires direct database access - contact admin)

# Option C: Create a new task with same parameters
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{ ... same task_json ... }'
```

---

## Advanced Usage

### Running as Background Services (Production)

For production use, run both processes as background services that auto-restart on failure.

#### Option 1: Using `screen` (Simple)

**Terminal 1 - Start Server:**

```bash
# Create screen session for server
screen -S unified_app

# Inside screen: Start server
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/render-tidb-sync
python3 unified_app.py

# Detach from screen: Press Ctrl+A, then D
```

**Terminal 2 - Start Executor:**

```bash
# Create screen session for executor
screen -S claude_executor

# Inside screen: Start executor
cd ~/Library/CloudStorage/OneDrive-Personal/Claude\ Tools/render-tidb-sync
MCP_SERVER="http://localhost:8080" python3 claude_executor.py

# Detach from screen: Press Ctrl+A, then D
```

**Managing Screen Sessions:**

```bash
# List all screen sessions
screen -ls

# Reattach to server
screen -r unified_app

# Reattach to executor
screen -r claude_executor

# Kill a session
screen -X -S unified_app quit
```

#### Option 2: Using `launchd` (macOS Native)

**Create Service Files:**

**1. Server Service** (`~/Library/LaunchAgents/com.claude.unified_app.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.unified_app</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/unified_app.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync</string>

    <key>StandardOutPath</key>
    <string>/Users/vusmac/Library/Logs/unified_app.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/vusmac/Library/Logs/unified_app.error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**2. Executor Service** (`~/Library/LaunchAgents/com.claude.executor.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.executor</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/claude_executor.py</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
        <key>MCP_SERVER</key>
        <string>http://localhost:8080</string>
    </dict>

    <key>WorkingDirectory</key>
    <string>/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync</string>

    <key>StandardOutPath</key>
    <string>/Users/vusmac/Library/Logs/claude_executor.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/vusmac/Library/Logs/claude_executor.error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Load Services:**

```bash
# Load server service
launchctl load ~/Library/LaunchAgents/com.claude.unified_app.plist

# Load executor service
launchctl load ~/Library/LaunchAgents/com.claude.executor.plist

# Check status
launchctl list | grep claude

# View logs
tail -f ~/Library/Logs/unified_app.log
tail -f ~/Library/Logs/claude_executor.log
```

**Manage Services:**

```bash
# Stop service
launchctl unload ~/Library/LaunchAgents/com.claude.unified_app.plist

# Restart service
launchctl unload ~/Library/LaunchAgents/com.claude.unified_app.plist
launchctl load ~/Library/LaunchAgents/com.claude.unified_app.plist
```

### Monitoring and Logging

**Real-time Logs:**

```bash
# Server logs
tail -f unified_app_v2.log

# Executor logs
tail -f claude_executor_v7.log

# Filter for errors only
tail -f claude_executor_v7.log | grep ERROR

# Filter for task executions
tail -f claude_executor_v7.log | grep "📋 Claude"
```

**Task Status Dashboard:**

```bash
# List all tasks
curl http://localhost:8080/AgentGarden/tasks/list | python3 -m json.tool

# List only pending tasks
curl http://localhost:8080/AgentGarden/tasks/list?status=pending | python3 -m json.tool

# List completed tasks
curl http://localhost:8080/AgentGarden/tasks/list?status=completed | python3 -m json.tool
```

### Custom Task Types

You can create custom task handlers by modifying `claude_executor.py`:

**Example: Add Email Notification Task**

```python
# In claude_executor.py, add new handler:

def handle_email_notification(self, task_json: Dict) -> Dict:
    """Send email notification with report"""
    import smtplib
    from email.mime.text import MIMEText

    # Get email config
    recipient = task_json.get('recipient')
    subject = task_json.get('subject', 'Report Ready')
    report_path = task_json.get('report_path')

    # Read report
    with open(self.onedrive_base / report_path, 'r') as f:
        content = f.read()

    # Send email
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['To'] = recipient

    # ... SMTP configuration ...

    return {
        'path': report_path,
        'summary': f'Emailed report to {recipient}'
    }

# In execute_task(), add routing:
elif task_type == 'email_notification':
    result = self.handle_email_notification(task_json)
```

**Create Email Task:**

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "email_notification",
    "task_json": {
      "recipient": "user@example.com",
      "subject": "Daily Sales Report",
      "report_path": "Claude Tools/Reports/inventory_intelligence/daily_sales_2025-12-30.md"
    },
    "created_by": "email_automation"
  }'
```

---

## Appendix

### File Reference

| File | Purpose | Location |
|------|---------|----------|
| `unified_app.py` | Main server (Flask) | Project root |
| `claude_executor.py` | Task executor | Project root |
| `mcp_server.py` | TiDB MCP interface | Project root |
| `sync_worker.py` | Database sync (optional) | Project root |
| `.env` | Environment variables | `agent_garden/.env` |
| `.mcp.json` | MCP configuration | Project root |
| `USER_MANUAL.md` | This manual | Project root |

### API Endpoints Reference

| Method | Endpoint | Purpose | Request Body |
|--------|----------|---------|--------------|
| GET | `/` | Health check | - |
| GET | `/tools` | List MCP tools | - |
| POST | `/mcp` | MCP JSON-RPC | `{"jsonrpc":"2.0","method":"tools/call",...)` |
| POST | `/AgentGarden/tasks/create` | Create task | `{"task_type":"...", "task_json":{...}}` |
| GET | `/AgentGarden/tasks/ready` | Get pending tasks | - |
| POST | `/AgentGarden/tasks/{id}/start` | Mark in progress | - |
| POST | `/AgentGarden/tasks/{id}/complete` | Mark completed | `{"result_path":"...", "result_summary":"..."}` |
| POST | `/AgentGarden/tasks/{id}/fail` | Mark failed | `{"error_log":"..."}` |
| GET | `/AgentGarden/tasks/{id}` | Get task details | - |
| GET | `/AgentGarden/tasks/list` | List all tasks | Query: `?status=...&task_type=...` |

### MCP Tools Reference

| Tool | Purpose | Arguments | Returns |
|------|---------|-----------|---------|
| `list_tables` | List all tables | - | Table names |
| `describe_table` | Get table schema | `table_name` | Column details |
| `query` | Execute SELECT | `sql` | Query results |
| `today_orders` | Orders placed today | - | Orders + count |
| `recent_orders` | N most recent orders | `limit` | Orders list |
| `order_details` | Full order info | `order_id` | Order + products |

### Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `claude_executor.log`, `unified_app_v2.log`
3. Test components individually (server, MCP, Claude CLI)
4. Review `PROGRESS.md` for recent changes
5. Contact: vu@yourdomain.com

---

**End of User Manual**

*Last Updated: 2025-12-30*
*Version: 2.0*
*© 2025 Claude Task Executor Team*
