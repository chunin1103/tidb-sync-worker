# Claude Task Queue - Gemini → Claude Integration

**Base URL:** https://gpt-mcp.onrender.com/AgentGarden/tasks/

System that allows Gemini to create and schedule tasks for Claude to execute. Enables multi-agent collaboration where Gemini handles user interactions and delegates complex tasks to Claude.

---

## Quick Reference

| Property | Value |
|----------|-------|
| **Base URL** | https://gpt-mcp.onrender.com/AgentGarden/tasks/ |
| **Endpoints** | 7 REST endpoints |
| **Database** | Agent Garden PostgreSQL (`claude_tasks` table) |
| **Scheduling** | Celery Beat (optional) |

---

## Architecture

```
User → Gemini → Task Queue API → Claude Executor → Agent Garden
         ↓              ↓              ↓
    Creates task    Stores in DB    Polls & executes
```

**Workflow:**
1. User requests a task via Gemini chat
2. Gemini creates task via `POST /tasks/create`
3. Claude Executor polls `GET /tasks/ready` for new tasks
4. Claude executes task using Agent Garden
5. Claude updates task status (start/complete/fail)

---

## Task Lifecycle

```
pending → in_progress → completed
                    ↘ failed
```

| State | Description |
|-------|-------------|
| `pending` | Task created, waiting for executor |
| `in_progress` | Claude currently executing |
| `completed` | Task finished successfully |
| `failed` | Task execution failed |

---

## API Endpoints

| Method | Endpoint | Description | Caller |
|--------|----------|-------------|--------|
| POST | `/tasks/create` | Create new task | Gemini |
| GET | `/tasks/ready` | Get tasks ready for execution | Claude |
| POST | `/tasks/<id>/start` | Mark as in_progress | Claude |
| POST | `/tasks/<id>/complete` | Mark as completed | Claude |
| POST | `/tasks/<id>/fail` | Mark as failed | Claude |
| GET | `/tasks/<id>` | Get task details + history | Anyone |
| GET | `/tasks/list` | List all tasks (with filters) | Anyone |

---

## Common Commands

### Create a Task (Gemini)
```bash
curl -X POST https://gpt-mcp.onrender.com/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "analysis",
    "task_json": {"description": "Analyze sales data"},
    "created_by": "gemini"
  }'
```

### Get Ready Tasks (Claude)
```bash
curl https://gpt-mcp.onrender.com/AgentGarden/tasks/ready
```

### List Pending Tasks
```bash
curl https://gpt-mcp.onrender.com/AgentGarden/tasks/list?status=pending
```

### Get Task Details
```bash
curl https://gpt-mcp.onrender.com/AgentGarden/tasks/42
```

---

## Creating Tasks

### Request Body
```json
{
  "task_type": "code_analysis",
  "task_json": {
    "description": "Analyze the codebase for performance issues",
    "parameters": {
      "directory": "/path/to/code",
      "focus_areas": ["memory_leaks", "slow_queries"]
    }
  },
  "schedule_cron": "0 2 * * *",
  "created_by": "gemini"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `task_type` | Yes | Type of task (e.g., "analysis", "report") |
| `task_json` | Yes | Task details and parameters |
| `schedule_cron` | No | Cron expression for scheduling |
| `created_by` | No | Who created the task |

### Response
```json
{
  "success": true,
  "task_id": 42,
  "message": "Task created successfully",
  "scheduled": true
}
```

---

## Executing Tasks (Claude Side)

### 1. Poll for Ready Tasks
```bash
GET /AgentGarden/tasks/ready
```

### 2. Start Execution
```bash
POST /AgentGarden/tasks/42/start
```

### 3. Complete or Fail
```bash
# Success
POST /AgentGarden/tasks/42/complete
{
  "result_path": "/path/to/output.md",
  "result_summary": "Found 5 performance issues"
}

# Failure
POST /AgentGarden/tasks/42/fail
{
  "error_log": "Could not access directory: Permission denied"
}
```

---

## Scheduling Tasks

Tasks can be scheduled using cron expressions.

**Format:** `minute hour day month day_of_week`

| Expression | Description |
|------------|-------------|
| `0 2 * * *` | Daily at 2 AM |
| `*/30 * * * *` | Every 30 minutes |
| `0 9 * * 1` | Every Monday at 9 AM |

**Note:** Requires Celery worker and beat to be running.

---

## File Locations

| File | Purpose |
|------|---------|
| `unified_app.py` (lines 210-478) | Task queue endpoints |
| `agent_garden/src/core/database_claude_tasks.py` | Database functions |
| `claude_executor.py` | Standalone executor process |
| `agent_garden/src/scheduling/celery_app.py` | Celery configuration |
| `agent_garden/init_claude_tasks_schema.py` | Database schema |

---

## Dependencies

- `celery` - Task scheduling and execution
- `celery[redis]` - Redis backend (optional)
- SQLAlchemy - Database operations

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tasks not appearing | Check database connection, verify `claude_tasks` table exists |
| Scheduled tasks not running | Ensure Celery worker and beat are running |
| Executor not picking up tasks | Check `claude_executor.log`, verify polling interval |
| Task stuck in `in_progress` | Manually update via database or call fail endpoint |
| Permission errors | Ensure executor has access to required directories |

---

## Integration

Same deployment as TiDB Sync + Agent Garden + Wiki Viewer:
- URL: https://gpt-mcp.onrender.com
- Paths:
  - `/` (TiDB MCP)
  - `/AgentGarden/` (Agent Garden UI)
  - `/AgentGarden/tasks/` (Task Queue)
  - `/wiki/` (Wiki Viewer)

For architecture diagrams, see `agent_garden/docs/GEMINI_CLAUDE_TASK_SYSTEM_PLAN.md`
