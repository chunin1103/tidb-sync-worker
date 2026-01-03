# Progress Log

This file tracks all completed tasks with concise summaries (≤10 lines per task).

---

## 2026-01-01: Agent Garden UI Redesign - Gemini → Claude Dashboard
**Status**: Completed
**Files Modified**: templates/index.html (1,112 lines - complete rebuild), src/core/app.py (added /api/reports/view route)
**What Changed**: Complete UI redesign to reflect new Gemini → Claude architecture
**Old Paradigm**: User interacts with Agent Garden UI directly (agent cards, execute agent button)
**New Paradigm**: Gemini as front-end (user chat) → Task Queue API → Claude Code CLI as back-end (executor)
**Dashboard Components Built**:
1. **Task Queue Panel** (8 columns) - Live stats (total/pending/in-progress/completed/failed) + scrollable task list with status badges
2. **Reports Gallery Panel** (8 columns) - Grid view of markdown reports from OneDrive with click-to-open, emoji icons, file sizes
3. **Executor Activity Feed** (4 columns) - Real-time feed showing polling/executing/completed/failed operations with colored indicators
4. **Create Task Form** (4 columns) - Agent type selector, prompt textarea, optional cron schedule input
**Design**: Dark neon glassmorphism theme, AGS Labs branding, animated gradients, auto-refresh every 10 seconds
**API Routes**:
- `/AgentGarden/` - Dashboard UI (app.py:97)
- `/AgentGarden/tasks/list` - Get all tasks with filtering (unified_app.py:478)
- `/AgentGarden/api/reports/list` - Scan OneDrive Reports folder (app.py:507)
- `/AgentGarden/api/reports/view/<path>` - Serve markdown files (app.py:644) ✨ NEW
**Testing**: Launched at http://localhost:8080/AgentGarden/, all panels load, auto-refresh works, reports clickable

---

## 2026-01-01: Report Viewer Route - Fix 404 Errors When Clicking Reports
**Status**: Completed
**Files Modified**: src/core/app.py:644-696, templates/index.html:1008
**Problem**: Clicking report cards in dashboard returned 404 errors - no route to serve OneDrive markdown files
**Error Log**: `GET /AgentGarden/inventory_intelligence/e2e_test_20251230_161758.md HTTP/1.1" 404`
**Solution**: Added new Flask route to serve markdown files from OneDrive Reports folder
**Implementation**:
- Created `/api/reports/view/<path:report_path>` route (app.py:644-696)
- Security: Path traversal protection - verifies resolved path is within Reports folder
- Returns markdown with proper content-type headers (`text/markdown; charset=utf-8`)
- Updated report card onclick handler: `window.open('/AgentGarden/api/reports/view/${report.path}', '_blank')`
**Impact**: Users can now click report cards to view markdown reports in new browser tab
**Testing**: Server restarted, reports now open without 404 errors

---

## 2025-12-30: Replace Celery Scheduling with Database Polling
**Status**: Completed
**Files Modified**: src/core/database.py:131, src/core/database_claude_tasks.py:1-48,67-96,99-141,206-215,320-337,370-382, unified_app.py:213-265
**Files Moved**: celery_app.py, celeryconfig.py, custom_scheduler.py, schedule_loader.py, start_celery_*.sh → agent_garden/celery/
**Files Created**: migrations/001_add_next_run_time.sql
**What Changed**: Replaced Celery Beat scheduling with database-based polling using next_run_time column
**Problem**: Celery adds infrastructure complexity (Redis + Worker + Beat processes) for low-volume task scheduling
**Approach**: Database polling (vs Celery Beat) - executor already polls every 30s, just check next_run_time <= now
**Key Changes**:
- Added `next_run_time` column to `claude_tasks` table (indexed for efficient polling)
- `create_claude_task()`: Calculates initial next_run_time from cron using APScheduler's CronTrigger
- `get_ready_tasks()`: Returns immediate tasks OR scheduled tasks where next_run_time <= now
- `complete_claude_task()`: Calculates next next_run_time for recurring tasks
- Removed Celery imports and Beat registration from unified_app.py
- Moved Celery files to celery/ folder (kept for reference, can delete later)
**Testing**: Syntax verified; requires running migration SQL on Neon database

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

## 2025-12-30: Claude Executor - API Endpoint Path Updates
**Status**: Completed
**Files Modified**: claude_executor.py:51,62,74,92
**What Changed**: Updated all task queue endpoint paths from /tasks/ to /AgentGarden/tasks/
**Problem**: Coworker updated API routes in unified_app.py to use /AgentGarden/tasks/ namespace but executor still using old /tasks/ paths
**Approach**: Update 4 endpoint references in executor (vs asking coworker to revert API changes)
**Key Changes**:
- poll_ready_tasks(): /tasks/ready → /AgentGarden/tasks/ready
- mark_task_started(): /tasks/{id}/start → /AgentGarden/tasks/{id}/start
- mark_task_completed(): /tasks/{id}/complete → /AgentGarden/tasks/{id}/complete
- mark_task_failed(): /tasks/{id}/fail → /AgentGarden/tasks/{id}/fail
**Testing**: curl http://localhost:8080/AgentGarden/tasks/ready returned 200 OK with {"success":true,"tasks":[],"count":0}

---

## 2025-12-30: Gemini-Claude Task System - End-to-End Test Success
**Status**: Completed
**Test**: Created task 18 via cURL → Executor picked up task → Generated report with real TiDB data
**What Changed**: Validated complete hybrid architecture (Gemini → Task Queue → Executor → MCP → TiDB → Claude CLI → OneDrive)
**Test Details**: POST /AgentGarden/tasks/create with agent_type=inventory_intelligence, prompt="Analyze 3 most recent orders"
**Execution**: Task 18 started at 16:17:58, completed at 16:18:22 (23 seconds total)
**Result**: Report saved to Claude Tools/Reports/inventory_intelligence/e2e_test_20251230_161758.md
**Real Data Verified**: Report contains 3 actual orders (646094-646096), customer names (Robin Wolf, Anne Wilhelm, Loren Eskenazi), cities/states
**Key Insights Generated**: Geographic analysis (66.7% West Coast), evening purchase pattern (10-11 PM), strategic recommendations
**Impact**: Proves FREE Claude Code CLI can analyze TiDB data without API costs - production ready

---

## 2025-12-30: Comprehensive User Manual Creation
**Status**: Completed
**Files Created**: USER_MANUAL.md (800+ lines)
**What Changed**: Created step-by-step guide for running entire system locally
**Sections Included**: System overview, prerequisites, installation, configuration (.env + .mcp.json), running locally (2 terminals)
**Usage Methods**: 3 approaches documented - cURL examples, Python script, scheduled tasks
**Architecture**: Component diagram, data flow, database schema, OneDrive sync explanation
**Troubleshooting**: 7 common scenarios with solutions (port conflicts, database connection, MCP errors, executor not picking up tasks, etc.)
**Advanced Usage**: Background services with screen/launchd for persistent operation
**Impact**: Any developer can now set up and run system locally following documented steps
**Note**: Manual includes exact Terminal commands, file paths, expected outputs, configuration examples

---

## 2025-12-30: OneDrive Sync Strategy Decision
**Status**: Decision Documented
**What Changed**: Evaluated OneDrive access methods and confirmed local sync approach
**Question**: User asked "is the most stable way is connect through api key?" for OneDrive access
**Option A (Selected)**: Local OneDrive Sync (current approach)
  - Pro: Simple, fast, works offline, no API setup, real-time sync
  - Pro: Already working - executor saves to ~/Library/CloudStorage/OneDrive-Personal/
  - Con: Requires OneDrive desktop app installed
**Option B (Rejected)**: OneDrive API Access
  - Con: Complex OAuth2 setup, API rate limits (100K requests/day), network latency
  - Con: Requires internet connection, error handling for API failures
  - Pro: Direct upload control, no desktop app dependency
**Decision**: "okay just stick with it" - Continue with local OneDrive sync
**Impact**: No code changes needed, leveraging existing OneDrive Desktop app for Mac

---

## 2026-01-02: Reorder Calculator - Oceanside Glass Implementation
**Status**: Completed
**Files Created**: reports_viewer/ (Flask blueprint, 15 files total), REORDER_CALCULATOR_README.md
**What Changed**: Built CSV-based reorder calculation system to replace manual Excel workflows for Oceanside Glass
**Problem**: Manual Excel calculations for 377-product inventory lists - time-consuming and error-prone
**Approach**: Flask Blueprint + SQLite temp sessions + PostgreSQL persistent storage (vs Excel macros)
**Key Features**: Drag-drop CSV upload, auto-calculate reorder quantities (0.35yr target), clarification questions (HIGH/MEDIUM/LOW), zero stock URGENT alerts, download with preview
**Database**: 4 PostgreSQL tables (reorder_sessions, reorder_questions, reorder_manual_edits, reorder_decision_learning) for permanent question history
**PostgreSQL Fixes**: DATETIME→TIMESTAMP, AUTO_INCREMENT→SERIAL, template type casting (Years_in_Stock|float)
**URL**: https://gpt-mcp.onrender.com/reports/reorder-calculator
**Testing**: Successfully processed 377-product CSV, calculations verified, download working

---

## 2026-01-02: Reorder Calculator - Bullseye Glass Implementation
**Status**: Completed
**Files Created**: bullseye_calculator.py (205 lines), updated routes.py, upload template
**What Changed**: Added Bullseye Glass calculator with dual-threshold logic (0.25 decision / 0.40 target)
**Business Rules**: Order Decision: 0.25yr (91d), Order Target: 0.40yr (146d), Lean Alert: 0.20yr (73d), 5-step cascade algorithm
**Approach**: Simplified algorithm for CSV workflow + flag cascade opportunities for manual review (vs full automation)
**Key Features**: Dual thresholds, optional reordering questions, cascade opportunity detection (3mm Half Sheet, 10×10, 5×10), zero stock URGENT
**Reference**: Production/wiki/03_Decision_Workflows/Bullseye_Vendor_Purchase_Decision_Tree.md
**Note**: Full 5-step cascade algorithm (cutting yields, Half Sheet combinations) requires manual review per business rules
**Testing**: Deployed successfully, available in manufacturer dropdown alongside Oceanside Glass

---

## 2026-01-02: Reorder Calculator - Questions Dashboard
**Status**: Completed
**Files Created**: all_questions.html (370 lines), updated database.py (get_all_questions), routes.py (dashboard + save-answer)
**What Changed**: Created centralized dashboard to view/answer all reorder questions across all sessions
**Problem**: Questions scattered across individual CSV upload sessions - hard to track pending decisions
**Approach**: Single dashboard with filtering + inline answers + PostgreSQL storage (vs session-by-session review)
**Key Features**: Filter by status (Pending/Answered/All) and priority (HIGH/MEDIUM/LOW), stats dashboard (6 metrics), inline answer boxes with direct save, color-coded badges (RED=HIGH, ORANGE=MEDIUM, GREEN=LOW), manufacturer tags, timestamps
**Database**: get_all_questions() joins reorder_sessions for context (filename, manufacturer), returns full history
**URL**: https://gpt-mcp.onrender.com/reports/reorder-calculator/questions
**Impact**: Single source of truth for all questions - never lose track of pending decisions

---

## 2026-01-03: Output Format Support (CSV/XLSX/JSON) - Claude as AI Employee
**Status**: Completed
**Files Modified**: migrations/002_add_output_format.sql (NEW), database.py:127, database_claude_tasks.py:12,37,73,261,311, unified_app.py:290, claude_executor.py:51,62,74,92,108,307-408,474-484, requirements.txt:30, TEST_OUTPUT_FORMATS.md (NEW)
**What Changed**: Added output_format column and executor logic to enable Claude Code CLI to generate CSV/XLSX/JSON files autonomously
**Problem**: Claude could only generate .md files; needed variety of business file formats (vendor orders, inventory reports, sales dashboards) for "AI Employee" concept
**Approach**: Changed working directory to OneDrive output folder, used relative filenames, removed `--print` flag, added `--dangerously-skip-permissions` (vs complex stdout capture)
**Key User Insight**: "bro why are you trying to generate the file outside directory" - simplified solution to run Claude from output folder itself
**Fixes Applied**: Git OneDrive conflict cleanup, executor endpoint URLs (/tasks/→/AgentGarden/tasks/), working directory (cwd=output_path), removed `--print` blocking file writes, XLSX prompts instructing Claude to execute Python scripts
**Testing**: Task 35 (CSV) ✅ 69-byte real CSV with proper data; Task 37 (XLSX) ✅ 5.7KB Microsoft Excel 2007+ file with multiple sheets, bold headers, formatted data
**Impact**: Claude Code CLI can now act as autonomous "AI Employee" generating business files in multiple formats without API costs

---

