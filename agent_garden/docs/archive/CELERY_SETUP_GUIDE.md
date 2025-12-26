# Celery + Redis Setup Guide for Agent Garden

Complete guide to setting up autonomous agents with Celery and Upstash Redis.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Upstash Redis Setup](#step-1-upstash-redis-setup)
4. [Step 2: Install Dependencies](#step-2-install-dependencies)
5. [Step 3: Configure Environment](#step-3-configure-environment)
6. [Step 4: Start Services](#step-4-start-services)
7. [Testing](#testing)
8. [API Endpoints](#api-endpoints)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT GARDEN SYSTEM                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Flask App  │◄─────┤    User      │               │
│  │  (app.py)    │      │  Browser     │               │
│  └──────┬───────┘      └──────────────┘               │
│         │                                              │
│         │ Trigger Tasks                                │
│         ▼                                              │
│  ┌──────────────────────────────────────┐             │
│  │      Upstash Redis (Free Cloud)      │             │
│  │      - Task Queue                    │             │
│  │      - Result Storage                │             │
│  └──┬───────────────────────┬───────────┘             │
│     │                       │                         │
│     │ Schedule              │ Execute                 │
│     ▼                       ▼                         │
│  ┌──────────────┐      ┌──────────────┐              │
│  │ Celery Beat  │      │Celery Worker │              │
│  │  (Scheduler) │      │  (Executor)  │              │
│  └──────┬───────┘      └──────┬───────┘              │
│         │                     │                       │
│         └─────────────┬───────┘                       │
│                       │                               │
│                       ▼                               │
│            ┌──────────────────────┐                   │
│            │  Autonomous Agents   │                   │
│            │  - Morning Report    │                   │
│            │  - Health Check      │                   │
│            │  - Weekly Summary    │                   │
│            └──────────┬───────────┘                   │
│                       │                               │
│                       ▼                               │
│            ┌──────────────────────┐                   │
│            │   Neon PostgreSQL    │                   │
│            │   - Agent Runs       │                   │
│            │   - Reports          │                   │
│            └──────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.9+
- Neon PostgreSQL account (already set up)
- Upstash Redis account (free tier)

---

## Step 1: Upstash Redis Setup

### 1.1 Create Upstash Account

1. Go to **https://console.upstash.com/**
2. Sign up for free (no credit card required)
3. Verify your email

### 1.2 Create Redis Database

1. Click **"Create Database"**
2. **Settings:**
   - **Name:** `agent-garden-queue`
   - **Type:** Regional
   - **Region:** Choose closest to you (e.g., `us-east-1`)
   - **Primary Region:** Auto-selected
   - **Read Region:** None (not needed)
   - **TLS:** Enabled (default)
   - **Eviction:** No eviction (default)

3. Click **"Create"**

### 1.3 Get Redis URL

1. After creation, you'll see the **"REST API"** tab
2. Click **"Redis Connect"** button (or look for connection strings)
3. Copy the **"UPSTASH_REDIS_REST_URL"** - it looks like:
   ```
   rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379
   ```

4. Save this URL - you'll need it in the next step!

**Example:**
```
rediss://default:AXWRAAIncDFhM2Q5YWVkYmYzZGM0YTIyODY2ZWM5OTZiOWYxNzA4MnAxMzAwOTc@tidy-oriole-30097.upstash.io:6379
```

---

## Step 2: Install Dependencies

### 2.1 Update Requirements

```bash
cd "/Users/vusmac/Desktop/AGS_LAB/Claude Tools 2/agent_garden_flask"
pip install -r requirements.txt
```

This installs:
- `celery>=5.3.0` - Task queue framework
- `redis>=5.0.0` - Redis client library

### 2.2 Verify Installation

```bash
# Check Celery
celery --version
# Should show: 5.3.x

# Check Redis
python -c "import redis; print(redis.__version__)"
# Should show: 5.0.x
```

---

## Step 3: Configure Environment

### 3.1 Update .env File

Open your `.env` file and update the `REDIS_URL`:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your_existing_key

# Database Configuration (Neon PostgreSQL)
DATABASE_URL=your_existing_neon_url

# Upstash Redis Configuration (for Celery task queue)
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

**Replace** `YOUR_PASSWORD` and `YOUR_ENDPOINT` with values from Step 1.3!

### 3.2 Test Redis Connection

```bash
python -c "import redis, os; from dotenv import load_dotenv; load_dotenv(); r = redis.from_url(os.getenv('REDIS_URL')); r.ping(); print('✅ Redis connected!')"
```

If successful, you'll see: `✅ Redis connected!`

---

## Step 4: Start Services

You need to run **3 processes** in separate terminal windows:

### Terminal 1: Flask Server

```bash
cd "/Users/vusmac/Desktop/AGS_LAB/Claude Tools 2/agent_garden_flask"
python app.py
```

Output:
```
Starting Agent Garden server on port 5001
Access at: http://localhost:5001
```

### Terminal 2: Celery Worker

```bash
cd "/Users/vusmac/Desktop/AGS_LAB/Claude Tools 2/agent_garden_flask"
./start_celery_worker.sh
```

Or manually:
```bash
celery -A celery_app worker --loglevel=info -Q agent_tasks
```

Output:
```
🚀 Starting Celery Worker for Agent Garden...
✅ Redis connection successful!

 -------------- celery@hostname v5.3.x
--- ***** -----
-- ******* ---- Darwin-24.6.0-x86_64-arm64
- *** --- * ---
- ** ---------- [queues]
                .> agent_tasks     exchange=agent_tasks(direct)

[tasks]
  . autonomous_agents.morning_intelligence_report
  . autonomous_agents.inventory_health_check
  . autonomous_agents.weekly_summary_report

[2024-12-22 10:00:00,000: INFO/MainProcess] Connected to redis://...
[2024-12-22 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### Terminal 3: Celery Beat Scheduler

```bash
cd "/Users/vusmac/Desktop/AGS_LAB/Claude Tools 2/agent_garden_flask"
./start_celery_beat.sh
```

Or manually:
```bash
celery -A celery_app beat --loglevel=info
```

Output:
```
📅 Starting Celery Beat Scheduler for Agent Garden...
✅ Redis connection successful!

📊 Scheduled Tasks:
  • Morning Intelligence Report: Daily at 7:00 AM
  • Inventory Health Check: Every 6 hours
  • Weekly Summary Report: Monday at 8:00 AM

[2024-12-22 10:00:00,000: INFO/MainProcess] beat: Starting...
[2024-12-22 10:00:00,000: INFO/MainProcess] Scheduler: Sending due task morning-intelligence-report-daily
```

---

## Testing

### Test 1: Manual Task Trigger (API)

```bash
curl -X POST http://localhost:5001/trigger_agent_task \
  -H "Content-Type: application/json" \
  -d '{"task_name": "morning_intelligence_report"}'
```

Expected response:
```json
{
  "success": true,
  "task_id": "abc-123-def-456",
  "task_name": "morning_intelligence_report",
  "message": "Task 'morning_intelligence_report' triggered successfully"
}
```

### Test 2: Check Task Status

```bash
curl http://localhost:5001/get_task_status/abc-123-def-456
```

Expected response:
```json
{
  "task_id": "abc-123-def-456",
  "state": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": null
}
```

### Test 3: View Agent Runs

```bash
curl http://localhost:5001/get_agent_runs?limit=5
```

Expected response:
```json
{
  "runs": [
    {
      "id": 1,
      "agent_type": "inventory_intelligence",
      "run_type": "manual",
      "trigger": "manual:user_triggered",
      "started_at": "2024-12-22T10:05:00",
      "completed_at": "2024-12-22T10:07:30",
      "status": "completed",
      "output_summary": "Morning Intelligence Report completed..."
    }
  ]
}
```

### Test 4: View Agent Reports

```bash
curl http://localhost:5001/get_agent_reports?limit=5
```

Expected response:
```json
{
  "reports": [
    {
      "id": 1,
      "agent_run_id": 1,
      "agent_type": "inventory_intelligence",
      "report_type": "morning_intelligence",
      "title": "Morning Intelligence Report - December 22, 2024",
      "content": "## CRITICAL ALERTS\n...",
      "created_at": "2024-12-22T10:07:00",
      "read_at": null,
      "is_unread": true
    }
  ]
}
```

---

## API Endpoints

### Autonomous Agent Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/get_agent_runs?limit=10` | Get recent agent executions |
| `GET` | `/get_agent_reports?limit=10&unread_only=true` | Get generated reports |
| `POST` | `/mark_report_read/<report_id>` | Mark report as read |
| `POST` | `/trigger_agent_task` | Manually trigger a task |
| `GET` | `/get_task_status/<task_id>` | Check Celery task status |

### Available Tasks

- `morning_intelligence_report` - Daily at 7:00 AM
- `inventory_health_check` - Every 6 hours
- `weekly_summary_report` - Monday at 8:00 AM

---

## Troubleshooting

### Issue 1: "Cannot connect to Redis"

**Symptoms:**
```
ConnectionError: Error connecting to Redis
```

**Solutions:**
1. Check your `REDIS_URL` in `.env` is correct
2. Verify Upstash Redis database is **Active** (not paused)
3. Test connection manually:
   ```bash
   python -c "import redis, os; from dotenv import load_dotenv; load_dotenv(); r = redis.from_url(os.getenv('REDIS_URL')); print(r.ping())"
   ```

### Issue 2: "Tasks not executing"

**Symptoms:**
- Tasks appear in Beat logs but don't run
- Worker shows no activity

**Solutions:**
1. Ensure **both** Celery Worker AND Celery Beat are running
2. Check worker logs for errors
3. Verify tasks are registered:
   ```bash
   celery -A celery_app inspect registered
   ```

### Issue 3: "Import errors"

**Symptoms:**
```
ModuleNotFoundError: No module named 'celery_app'
```

**Solutions:**
1. Ensure you're in the correct directory:
   ```bash
   cd "/Users/vusmac/Desktop/AGS_LAB/Claude Tools 2/agent_garden_flask"
   ```
2. Check file structure:
   ```
   agent_garden_flask/
   ├── celery_app.py       ✅ Must exist
   ├── autonomous_agents.py ✅ Must exist
   ├── app.py              ✅ Must exist
   └── .env                ✅ Must have REDIS_URL
   ```

### Issue 4: "Upstash free tier limits"

**Symptoms:**
```
Error: Max commands exceeded
```

**Solutions:**
- Upstash free tier: **10,000 commands/day**
- Each task = ~10 commands (send + receive + result)
- You can run ~1,000 tasks/day easily
- If exceeding: Upgrade to paid tier or reduce task frequency

### Issue 5: "Port already in use"

**Symptoms:**
```
OSError: [Errno 48] Address already in use
```

**Solutions:**
1. Flask app auto-finds available port (5001-5010)
2. Kill existing processes:
   ```bash
   lsof -ti:5001 | xargs kill -9
   ```

### Issue 6: "Database errors"

**Symptoms:**
```
Error saving agent run: ...
```

**Solutions:**
1. Check Neon database is accessible:
   ```bash
   python -c "from database import init_db; init_db(); print('✅ Database connected!')"
   ```
2. Verify `DATABASE_URL` in `.env`
3. Check Neon dashboard for connection issues

---

## Production Deployment

### Using Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5001:5001"
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - worker
      - beat

  worker:
    build: .
    command: celery -A celery_app worker --loglevel=info -Q agent_tasks
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

  beat:
    build: .
    command: celery -A celery_app beat --loglevel=info
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
```

Then run:
```bash
docker-compose up -d
```

### Using Systemd (Linux Servers)

Create service files:

**`/etc/systemd/system/agent-garden-worker.service`:**
```ini
[Unit]
Description=Agent Garden Celery Worker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/agent_garden_flask
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A celery_app worker --loglevel=info -Q agent_tasks
Restart=always

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/agent-garden-beat.service`:**
```ini
[Unit]
Description=Agent Garden Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/agent_garden_flask
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable agent-garden-worker agent-garden-beat
sudo systemctl start agent-garden-worker agent-garden-beat
sudo systemctl status agent-garden-worker agent-garden-beat
```

---

## Monitoring

### Celery Flower (Web UI)

Install Flower for task monitoring:
```bash
pip install flower
celery -A celery_app flower
```

Access at: **http://localhost:5555**

### Upstash Dashboard

Monitor Redis usage at: **https://console.upstash.com/**

Shows:
- Commands per day
- Memory usage
- Connection stats
- Request latency

---

## Summary

**What you built:**
- ✅ Celery task queue with Upstash Redis (free)
- ✅ 3 autonomous agents on schedules
- ✅ API endpoints for triggering/monitoring
- ✅ Database persistence for runs/reports
- ✅ Production-ready architecture

**Services running:**
1. **Flask** - Web API (port 5001)
2. **Celery Worker** - Task executor
3. **Celery Beat** - Task scheduler

**Next steps:**
- Add notification system (Slack, Email)
- Build agent dashboard UI
- Add more autonomous agents
- Monitor with Flower

---

**Built for ArtGlassSupplies.com | Agent Garden v2.2.0**
