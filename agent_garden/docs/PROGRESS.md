# Progress Log

This file tracks all completed tasks with concise summaries (≤10 lines per task).

---

## 2025-12-26: Remove Dangerous Restart Button & Reduce Auto-Reload to 30s
**Status**: Completed
**Files Modified**: src/scheduling/custom_scheduler.py:32, start_celery_beat.sh:34,46, src/core/app.py:677-679,879-881, templates/index.html:2696-2698,2736-2738
**What Changed**: Removed restart button that was terminating Celery Beat, reduced auto-reload from 60s to 30s
**Problem**: UI restart button killed Celery Beat without restarting (only works with systemd/supervisor)
**Approach**: Remove button + show auto-reload message (vs fixing restart logic) - simpler and safer
**Key Changes**:
- DatabaseScheduler refresh interval: 60s → 30s
- Backend API: requires_restart=True → False, added auto_reload_seconds=30
- UI: Replaced restart button with "Changes take effect in 30s" message
**Testing**: Verified scheduler loads, config shows 30s interval, all tests pass

---

## 2025-12-26: Project Reorganization & Cleanup
**Status**: Completed
**Files Modified**: 17 Python files, 35+ MD files relocated
**What Changed**: Reorganized agent_garden_flask from chaotic 50+ file root to clean src/ structure
**Approach**: Aggressive cleanup (vs gentle) - archived outdated docs, organized code by purpose
**Key Changes**:
- Created src/{core,connectors,scheduling,utils} structure
- Moved 35+ MD files: 6 to docs/, 20+ to docs/archive/
- Updated all imports in 17 Python files automatically
- Created consolidated ARCHITECTURE.md from multiple summaries
**Testing**: All imports verified working (database, tidb_connector, agent_backend)

---

## 2025-12-26: Fix Celery Startup Scripts
**Status**: Completed
**Files Modified**: start_celery_worker.sh:31, start_celery_beat.sh:23,44
**What Changed**: Updated Celery scripts to work with new src/ structure
**Approach**: Added PYTHONPATH=. and updated module paths from celery_app to src.scheduling.celery_app
**Key Fixes**:
- Worker script: celery -A src.scheduling.celery_app worker
- Beat script: celery -A src.scheduling.celery_app beat -S src.scheduling.custom_scheduler:DatabaseScheduler
- Schedule loader: from src.scheduling.schedule_loader import get_schedule_summary
**Testing**: Verified celery_app loads, schedule_loader works, CLI commands work

---

## 2025-12-26: Fix Flask App Startup
**Status**: Completed
**Files Modified**: Created app.py (launcher), start.sh already compatible
**What Changed**: Created launcher script in root to start Flask app from src/core/app.py
**Approach**: Launcher script (vs updating all commands) - maintains familiar "python app.py" workflow
**Key Changes**: app.py imports from src.core.app and runs with port/debug config from env
**Testing**: Verified app.py exists, imports work, Flask app loads successfully
**Note**: start.sh already uses "python app.py" so no changes needed

---

## 2025-12-26: Fix Flask Template Path
**Status**: Completed
**Files Modified**: src/core/app.py:30-38
**What Changed**: Fixed Flask template folder to point to project root instead of src/core/
**Approach**: Calculate project root (2 levels up from src/core/app.py) and set template_folder explicitly
**Issue**: Flask(__name__) used file location as base, couldn't find templates/ in root
**Fix**: Flask(__name__, template_folder=os.path.join(project_root, 'templates'))
**Testing**: Verified template folder path correct, index.html found successfully

---

## 2025-12-26: Fix Shell Script Line Endings
**Status**: Completed
**Files Modified**: start.sh, start_celery_worker.sh, start_celery_beat.sh
**What Changed**: Converted Windows CRLF line endings to Unix LF format
**Issue**: Scripts had ^M characters causing "bad interpreter" error on macOS/Linux
**Approach**: Used sed to strip carriage returns, then chmod +x to make executable
**Testing**: Verified Unix line endings with file/od commands, confirmed start.sh executes

---

## 2025-12-26: Merge Documentation Folders
**Status**: Completed
**Files Modified**: Moved PROGRESS.md, DEPENDENCIES.md; Updated CLAUDE.md:2,4,6,10,13
**What Changed**: Merged documentation/ into docs/ for single documentation location
**Approach**: Approach 1 (merge INTO docs/) vs keeping separate - chose consolidation for simplicity
**Key Changes**:
- Moved PROGRESS.md and DEPENDENCIES.md from documentation/ to docs/
- Updated all CLAUDE.md references from "documentation/" to "docs/"
- Removed empty documentation/ folder
**Testing**: Verified files in docs/, CLAUDE.md updated correctly, old folder removed

---

## 2025-12-30: Gemini-Claude Task System - Phase 0: MCP Configuration (NOT IN ORIGINAL PLAN)
**Status**: Completed
**Files Created**: .mcp.json (project root)
**What Changed**: Configured Claude Code CLI to access TiDB via MCP server
**Difference from Plan**: Original plan assumed Claude would query TiDB directly; we added MCP layer for Claude Code CLI
**Approach**: SSE transport type pointing to localhost MCP endpoint for secure, non-interactive execution
**Key Changes**:
- Created .mcp.json: {"mcpServers": {"tidb-mcp": {"type": "sse", "url": "http://localhost:8080/mcp"}}}
- Tested Claude Code CLI --print flag for non-interactive mode
- Verified 6 MCP tools: query, list_tables, describe_table, today_orders, recent_orders, order_details
**Testing**: `claude --print "List MCP tools"` successfully returned all tools

---

## 2025-12-30: Gemini-Claude Task System - Infrastructure Fixes (NOT IN ORIGINAL PLAN)
**Status**: Completed
**Files Modified**: claude_executor.py:231-274, unified_app.py:27-35, agent_garden/.env:16
**What Changed**: Fixed critical infrastructure issues blocking task execution
**Difference from Plan**: Original plan assumed all infrastructure working; spent 3 hours debugging
**Problem 1 - MCP Endpoint Format**: Executor calling POST /mcp/list_tables (404 errors)
**Fix 1**: Changed to JSON-RPC 2.0: POST /mcp with {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "list_tables"}}
**Problem 2 - Missing Environment Variables**: unified_app.py not loading .env file
**Fix 2**: Added load_dotenv(Path(__file__).parent / 'agent_garden' / '.env') at startup
**Problem 3 - TiDB Password Mismatch**: Local password incorrect (Ke6...), Render had different password (WGH...)
**Fix 3**: User updated .env with correct password from Render dashboard
**Testing**: Local MCP endpoint now returns real TiDB data (recent orders with customer info)

---

## 2025-12-30: Gemini-Claude Task System - Security Architecture Decision (NOT IN ORIGINAL PLAN)
**Status**: Completed (Decision Documented)
**What Changed**: Evaluated security trade-offs and selected localhost MCP endpoint
**Difference from Plan**: Plan didn't address security implications of public MCP endpoint
**Option A (Rejected)**: Public Render endpoint (https://gpt-mcp.onrender.com/mcp)
  - Risk: No authentication, IP restrictions, or rate limiting
  - Risk: Anyone with URL can query business data
  - Pro: Already working, no password fixes needed
**Option B (Selected)**: Localhost endpoint (http://localhost:8080/mcp)
  - Security: Network-isolated, only accessible from Mac
  - Security: Requires correct TiDB password
  - Security: Protects customer data, orders, revenue
**Rationale**: User has real business data; chose security over convenience
**Testing**: Localhost endpoint working with WGH... password; Render endpoint available as fallback only

---

## 2025-12-30: Gemini-Claude Task System - Hybrid Executor Architecture (MODIFIED FROM PLAN)
**Status**: Completed
**Files Modified**: claude_executor.py:231-305, 306-442
**What Changed**: Implemented hybrid architecture - Python executor makes direct MCP calls, Claude Code CLI analyzes data
**Difference from Plan**: Plan Phase 4 assumed executor would use subprocess to call Claude Code CLI for everything
**Original Plan Approach**: Executor → Claude Code CLI → MCP → TiDB (Claude CLI handles all MCP calls)
**Actual Implementation**: Executor → MCP (direct HTTP) → TiDB, THEN Executor → Claude Code CLI (with data pre-fetched)
**Rationale**: Avoids Claude Code CLI permission prompts for HTTP requests in non-interactive mode
**Key Functions**:
- call_mcp_tool(tool_name, arguments): Direct JSON-RPC calls to MCP server
- fetch_database_context(agent_type, prompt): Fetches relevant TiDB data based on agent type
- handle_agent_report(task_json): Fetches data via MCP, passes to Claude Code CLI for analysis
**Testing**: Successfully fetched 3 recent orders via direct MCP call; ready for Claude CLI integration test

---

## 2025-12-30: TiDB Sync - Enhanced Visual Status Dashboard
**Status**: Completed
**Files Modified**: templates/sync_status.html (new 570 lines), sync_worker.py:32,643-712
**What Changed**: Created modern HTML dashboard for monitoring TiDB sync operations
**Problem**: /status endpoint returned raw JSON - hard to monitor sync progress visually
**Approach**: HTML template with gradient design, real-time updates, auto-refresh (vs improving JSON API)
**Key Features**: Color-coded badges (success/error/running/idle), progress bars, manual sync button, 10s auto-refresh toggle
**Implementation**: Added render_template import, created /status (HTML) and /status/json (backward compatibility)
**Impact**: Can now visually monitor sync progress at https://gpt-mcp.onrender.com/status
**Testing**: Syntax verified, deployed to Render (commit 89bd9b7)

---

## 2025-12-30: TiDB Sync - Enhanced File Logging for Debugging
**Status**: Completed
**Files Modified**: sync_worker.py:161-174,282-284,348-367,377-401
**What Changed**: Added comprehensive logging to show which S3 files are synced and order counts
**Problem**: When 0 orders returned, unclear if wrong S3 file synced or truly no orders for today
**Approach**: Extract metadata from S3 filenames + log database counts after sync (vs manual verification)
**Key Logs**: Full S3 path, backup timestamp (YYYY-MM-DD HH:MM:SS), total orders, today's orders, latest order date
**Example Output**: "✅ Latest backup: 2025-12-30-08-00-01.sql.gz | 📊 Total orders: 134,277 | Today: 0 | Latest: 2025-12-28"
**Impact**: Eliminates guesswork when debugging "0 orders today" - see exact file and database state
**Testing**: Syntax verified, deployed to Render (commit cdb5de2)

---

## 2025-12-30: Unified App Merge - Claude Task Queue Integration
**Status**: Completed
**Files Modified**: unified_app.py:298→592 lines, .gitignore:4→39 lines
**What Changed**: Merged two unified_app.py versions - retained all features from both
**Problem**: Two versions existed (current: Wiki+.env; MacBook: Task Queue) - risk losing functionality
**Approach**: Line-by-line audit to verify all logic migrated (vs trusting assumptions)
**Merged Features**: ✅ Wiki Viewer, ✅ .env loading, ✅ 7 Task Queue endpoints at /AgentGarden/tasks/
**Intentional Change**: Moved task endpoints from /tasks/ to /AgentGarden/tasks/ (per user request)
**Audit**: Performed comprehensive comparison, verified 100% logic migrated, deleted old file
**Impact**: All 4 services (TiDB MCP, Sync, Agent Garden, Wiki) + Task Queue in single deployment
**Testing**: Syntax verified, deployed to Render (commit 4721f0c)

---

## 2025-12-30: Claude Task Queue - Database Module & Executor
**Status**: Completed
**Files Added**: database_claude_tasks.py (360 lines), init_claude_tasks_schema.py, claude_executor.py, start/stop scripts
**What Changed**: Added missing database module that unified_app.py imports for task operations
**Problem**: unified_app.py imported agent_garden.src.core.database_claude_tasks but file not in git - deployment failed
**Approach**: Add all required files for task queue feature (vs fixing imports)
**Key Functions**: create_claude_task, get_ready_tasks, start/complete/fail_claude_task, get_all_claude_tasks (8 total)
**Dependencies**: SQLAlchemy for database ops, Celery for scheduled tasks (optional)
**Impact**: Task queue endpoints now have all required imports - Gemini can create tasks for Claude to execute
**Testing**: Files added to git, syntax verified, deployed to Render (commit 49a5587)

---

