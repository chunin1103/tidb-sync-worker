# Merge Guide: TiDB + Agent Garden Unification

This document explains how the `render-tidb-sync` and `AgentGarden` projects were merged into a single unified web service.

## Overview

**Goal:** Host both TiDB MCP Server and Agent Garden on the same Render web service, sharing the same repository and deployment pipeline.

**Solution:** Created a unified Flask application (`unified_app.py`) that:
- Mounts **TiDB MCP** routes at **root level** (`/`, `/mcp`, `/tools`, etc.)
- Mounts **Agent Garden** routes at **/AgentGarden** prefix
- Combines all dependencies into one `requirements.txt`
- Uses a single `render.yaml` deployment configuration

## Architecture Changes

### Before Merge

```
render-tidb-sync/                AgentGarden/
├── mcp_server.py       (/)      ├── src/core/app.py    (/)
├── sync_worker.py      (/)      ├── templates/
├── requirements.txt             ├── requirements.txt
└── render.yaml                  └── (standalone)
```

### After Merge

```
render-tidb-sync/
├── unified_app.py              # NEW: Main entry point
├── mcp_server.py              # Imported by unified_app
├── sync_worker.py             # Imported by unified_app
├── requirements.txt           # MERGED: All dependencies
├── render.yaml               # UPDATED: Points to unified_app
│
└── agent_garden/             # NEW: Copied from AgentGarden
    ├── src/core/app.py       # Mounted at /AgentGarden
    ├── templates/
    ├── autonomous_agents/
    └── docs/
```

## File Changes

### 1. Created `unified_app.py`

**Purpose:** Main Flask application that combines all services.

**Key Features:**
- Imports routes from `mcp_server.py` and `sync_worker.py`
- Mounts them at root level
- Imports Agent Garden app from `agent_garden/src/core/app.py`
- Uses Flask Blueprint to mount Agent Garden at `/AgentGarden` prefix
- Provides unified health check at `/`

**Code Structure:**
```python
# Import MCP routes → Register at root
from mcp_server import app as mcp_app
app.add_url_rule(...)

# Import Agent Garden → Register at /AgentGarden
from agent_garden.src.core.app import app as garden_app
garden_blueprint = Blueprint('agent_garden', __name__, url_prefix='/AgentGarden')
app.register_blueprint(garden_blueprint)
```

### 2. Updated `requirements.txt`

**Merged dependencies from both projects:**

```diff
# Original (render-tidb-sync)
pymysql>=1.1.0
flask>=3.0.0
apscheduler>=3.10.0
boto3>=1.34.0

# Added (from AgentGarden)
+ gunicorn>=21.2.0
+ google-genai>=1.0.0
+ python-dotenv>=1.0.0
+ psycopg2-binary>=2.9.9
+ sqlalchemy>=2.0.0
+ celery>=5.3.0
+ redis>=5.0.0
```

### 3. Updated `render.yaml`

**Changes:**
```diff
services:
  - type: web
-   name: tidb-unified
+   name: tidb-agent-garden-unified
    runtime: python
    buildCommand: pip install -r requirements.txt
-   startCommand: python sync_worker.py
+   startCommand: python unified_app.py
    healthCheckPath: /
    envVars:
      # ... existing TiDB and IDrive vars
+     # Agent Garden Configuration
+     - key: GOOGLE_API_KEY
+       sync: false
+     - key: REDIS_URL
+       sync: false
+     - key: FLASK_DEBUG
+       value: "False"
```

### 4. Updated `README.md`

- Added Agent Garden documentation
- Updated architecture diagram
- Added `/AgentGarden` endpoint reference
- Included Agent Garden features
- Updated deployment instructions

## URL Structure

### Root Level (TiDB/Sync)

All TiDB and Sync routes remain at root level:

| Old URL | New URL | Status |
|---------|---------|--------|
| `GET /` | `GET /` | ✅ Same (now shows unified health) |
| `POST /mcp` | `POST /mcp` | ✅ Same |
| `GET /tools` | `GET /tools` | ✅ Same |
| `POST /query` | `POST /query` | ✅ Same |
| `GET /status` | `GET /status` | ✅ Same |
| `POST /sync` | `POST /sync` | ✅ Same |

### Agent Garden Routes

All Agent Garden routes are prefixed with `/AgentGarden`:

| Old URL (AgentGarden) | New URL (Unified) |
|----------------------|-------------------|
| `GET /` | `GET /AgentGarden/` |
| `POST /execute_agent` | `POST /AgentGarden/execute_agent` |
| `GET /sessions` | `GET /AgentGarden/sessions` |
| `GET /get_sessions` | `GET /AgentGarden/get_sessions` |
| `POST /clear_session` | `POST /AgentGarden/clear_session` |
| ... (30+ more) | ... (all prefixed) |

## Deployment Steps

### Step 1: Update Render Service

Since the repository is already deployed to Render:

1. **Push changes** to GitHub:
   ```bash
   cd render-tidb-sync
   git add .
   git commit -m "Merge Agent Garden into unified service"
   git push origin main
   ```

2. **Render auto-deploys** (if enabled) or manually trigger deployment

3. **Update environment variables** in Render dashboard:
   - Add `GOOGLE_API_KEY` (optional - for AI features)
   - Add `REDIS_URL` (optional - for Celery)

### Step 2: Test Endpoints

**Test TiDB MCP (should still work):**
```bash
curl https://gpt-mcp.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

**Test Agent Garden (new):**
```bash
# Open in browser
https://gpt-mcp.onrender.com/AgentGarden/

# Or test API
curl https://gpt-mcp.onrender.com/AgentGarden/health
```

**Test Unified Health:**
```bash
curl https://gpt-mcp.onrender.com/
```

Should return:
```json
{
  "status": "healthy",
  "service": "unified-tidb-agent-garden",
  "services": {
    "tidb_mcp": true,
    "agent_garden": true,
    "sync_worker": true
  },
  "endpoints": {
    "tidb_mcp": { ... },
    "agent_garden": { ... },
    "sync_worker": { ... }
  }
}
```

## Backward Compatibility

### TiDB MCP - ✅ Fully Compatible
- All existing MCP endpoints remain at same URLs
- No changes needed to Claude Code configuration
- `claude mcp add tidb-mcp https://gpt-mcp.onrender.com/mcp` still works

### Sync Worker - ✅ Fully Compatible
- `/status` and `/sync` endpoints remain unchanged
- Scheduled syncs continue to run (6 AM / 6 PM UTC)
- No changes needed to any automation

### Agent Garden - 🆕 New Prefix
- All Agent Garden routes now require `/AgentGarden` prefix
- Update any frontend code or API calls to use new URLs
- Example: `fetch('/execute_agent', ...)` → `fetch('/AgentGarden/execute_agent', ...)`

## Environment Variables

### Previously Required
- ✅ `TIDB_USER` (unchanged)
- ✅ `TIDB_PASSWORD` (unchanged)
- ✅ `TIDB_HOST` (unchanged)
- ✅ `IDRIVE_ACCESS_KEY` (unchanged)
- ✅ `IDRIVE_SECRET_KEY` (unchanged)
- ✅ `IDRIVE_ENDPOINT` (unchanged)

### Newly Added (Optional)
- 🆕 `GOOGLE_API_KEY` - For Agent Garden AI features
- 🆕 `REDIS_URL` - For Agent Garden Celery tasks
- 🆕 `FLASK_DEBUG` - Debug mode (default: False)

## Troubleshooting

### Issue: "Module not found: agent_garden"

**Cause:** Agent Garden folder not in repository

**Solution:**
```bash
# Ensure agent_garden folder was copied
ls render-tidb-sync/agent_garden/
```

### Issue: "Import error: src.core.app"

**Cause:** Python path not configured correctly

**Solution:** Check `unified_app.py` line:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent_garden'))
```

### Issue: "/AgentGarden/ returns 404"

**Cause:** Blueprint not registered properly

**Solution:** Check logs for:
```
✅ Agent Garden registered at /AgentGarden
```

If missing, check import errors in `unified_app.py`

### Issue: "MCP endpoints not working"

**Cause:** Route conflict or import error

**Solution:** Check logs for:
```
✅ TiDB MCP Server routes registered (root level)
```

## Benefits of Unified Service

1. **Single Deployment** - One Render service instead of two
2. **Shared Resources** - Same database connections, environment variables
3. **Unified Health Check** - Monitor all services at once
4. **Simplified Maintenance** - One codebase, one deployment pipeline
5. **Cost Effective** - One Render instance instead of multiple
6. **Shared Authentication** - Can add auth layer for all services
7. **Consistent Logging** - All logs in one place

## Next Steps

### Optional Enhancements

1. **Add Authentication** - Protect Agent Garden routes
2. **Shared Database** - Use same TiDB for Agent Garden data
3. **Unified Monitoring** - Add metrics/observability
4. **CORS Configuration** - If Agent Garden needs frontend
5. **Rate Limiting** - Protect public endpoints
6. **Caching** - Add Redis caching for both services

### Agent Garden Features to Explore

- 📊 Create custom agents for TiDB analytics
- 🤖 Set up autonomous agents for database monitoring
- 📅 Schedule reports to run automatically
- 💾 Export conversations and reports
- ⚙️ Configure timezone for schedules

## Rollback Plan

If needed, can rollback to separate services:

1. **TiDB Only:**
   - Change `render.yaml`: `startCommand: python sync_worker.py`
   - Remove Agent Garden env vars
   - Deploy

2. **Agent Garden Separately:**
   - Deploy `agent_garden/` as new Render service
   - Use `agent_garden/app.py` as entry point
   - Set `PORT`, `GOOGLE_API_KEY`, `REDIS_URL`

## Summary

The merge successfully combines TiDB MCP, Sync Worker, and Agent Garden into a single unified Flask application while maintaining:

- ✅ Backward compatibility for TiDB MCP
- ✅ Backward compatibility for Sync Worker
- ✅ All Agent Garden functionality (at `/AgentGarden` prefix)
- ✅ Single deployment configuration
- ✅ Merged dependencies
- ✅ Clear URL structure

**No breaking changes** for existing TiDB/Sync users. Agent Garden adds **new capabilities** without disrupting existing functionality.
