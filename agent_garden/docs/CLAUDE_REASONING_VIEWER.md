# Claude Reasoning Viewer - Implementation Documentation

**Date:** 2026-01-13
**Session:** Admin page for viewing Claude's full reasoning chain during task execution

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Brainstorming & Approaches](#brainstorming--approaches)
3. [Key Discovery: Session Files](#key-discovery-session-files)
4. [Implementation Details](#implementation-details)
5. [Files Modified/Created](#files-modifiedcreated)
6. [API Endpoints](#api-endpoints)
7. [Database Schema](#database-schema)
8. [Bug Fix: Path Generation](#bug-fix-path-generation)
9. [Testing Results](#testing-results)
10. [Usage Guide](#usage-guide)

---

## Problem Statement

**User Request:** Build an admin page to display Claude's reasoning when executing tasks - similar to how ChatGPT and Gemini show their thinking process.

**Goal:** Capture and display the full chain-of-thought including:
- Internal thinking/reasoning
- Tool calls and their inputs
- Tool results/outputs
- Final text responses
- Token usage and execution metrics

**Constraint:** The system runs with `--dangerously-skip-permissions` flag for automated file generation, so we needed a way to capture reasoning without modifying Claude's behavior.

---

## Brainstorming & Approaches

We discussed 6 different approaches:

### Approach 1: Real-Time Streaming (SSE/WebSocket)
```
Claude Executor → POST /tasks/{id}/stream → SSE → Admin Page
```
- **Pros:** Live visibility, engaging UX
- **Cons:** Requires persistent connection, more complex

### Approach 2: Step-Based Progress Tracking
```
Claude Executor → POST /tasks/{id}/step → Database → Admin polls
```
- **Pros:** Simple to implement, survives disconnects
- **Cons:** Not truly real-time

### Approach 3: Log Capture + Replay
```
Claude Executor → writes reasoning.log → POST on complete → Admin views
```
- **Pros:** Complete history, easy debugging
- **Cons:** No live view

### Approach 4: Structured Reasoning Objects
Send structured JSON with reasoning metadata
- **Pros:** Parseable, can build rich UI
- **Cons:** Requires modifying executor output format

### Approach 5: Hybrid (Steps + Final Log)
Combine approaches 2 and 3
- **Pros:** Best of both worlds
- **Cons:** More implementation work

### Approach 6: Claude Code Hooks
Use Claude Code's hook system to intercept events
- **Pros:** Native integration
- **Cons:** Need to research hook capabilities

**Decision:** User prioritized capturing full reasoning over real-time display. This led to discovering session files.

---

## Key Discovery: Session Files

### The Breakthrough

Claude Code already stores **full conversation transcripts** including thinking blocks in session files:

```
~/.claude/projects/{project-key}/{session-id}.jsonl
```

### Session File Format

Each line is a JSON object representing a message:

```json
// User message
{
  "type": "user",
  "message": {"role": "user", "content": "..."},
  "timestamp": "2026-01-12T16:24:00.842Z"
}

// Assistant message with thinking
{
  "type": "assistant",
  "message": {
    "model": "claude-opus-4-5-20251101",
    "content": [
      {
        "type": "thinking",
        "thinking": "The user wants to see the executor in action..."
      },
      {
        "type": "text",
        "text": "I'll help you with that."
      },
      {
        "type": "tool_use",
        "id": "toolu_01...",
        "name": "Bash",
        "input": {"command": "ls -la"}
      }
    ]
  },
  "timestamp": "2026-01-12T16:24:04.117Z"
}

// Tool result
{
  "type": "user",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_01...",
      "content": "file1.txt\nfile2.txt"
    }]
  },
  "toolUseResult": {"stdout": "...", "stderr": ""}
}
```

### Content Types Captured

| Type | Description | Example |
|------|-------------|---------|
| `thinking` | Claude's internal reasoning | "I need to check if the file exists first..." |
| `text` | Final response to user | "Here's the report you requested." |
| `tool_use` | Tool call with name + input | `{name: "Write", input: {file_path: "..."}}` |
| `tool_result` | What the tool returned | "File created successfully" |

---

## Implementation Details

### Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Claude Executor    │     │   Render Server      │     │   Admin Page        │
│  (local Mac)        │     │   (unified_app)      │     │   (browser)         │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
         │                           │                            │
         │  1. Run Claude with       │                            │
         │     --session-id flag     │                            │
         │                           │                            │
         │  2. Parse session file    │                            │
         │     for reasoning chain   │                            │
         │                           │                            │
         │  3. POST reasoning ──────▶│  4. Store in PostgreSQL    │
         │                           │                            │
         │                           │  5. GET reasoning ────────▶│
         │                           │                            │
         │                           │                            │  6. Display UI
```

### Flow

1. **Task Created:** Gemini creates task via `/AgentGarden/tasks/create`
2. **Executor Polls:** `claude_executor.py` polls `/AgentGarden/tasks/ready`
3. **Execution Starts:** Generate UUID session ID, run Claude with `--session-id`
4. **Claude Works:** Creates session file at `~/.claude/projects/{key}/{id}.jsonl`
5. **Execution Completes:** Parse session file for reasoning chain
6. **Store Reasoning:** POST to `/admin/tasks/{id}/reasoning`
7. **Admin Views:** Browse at `/admin/reasoning/viewer`

---

## Files Modified/Created

### 1. claude_executor.py

**New Methods Added:**

```python
def _get_session_file_path(self, session_id: str, cwd: str) -> Path:
    """Build path to Claude session file"""
    # Converts: /Users/vusmac/Claude Tools/Reports
    # To: -Users-vusmac-Claude-Tools-Reports
    project_key = cwd.replace('/', '-').replace(' ', '-').replace('_', '-')
    if not project_key.startswith('-'):
        project_key = '-' + project_key
    return Path.home() / '.claude' / 'projects' / project_key / f'{session_id}.jsonl'

def parse_session_reasoning(self, session_id: str, cwd: str) -> Dict:
    """Parse session file for full reasoning chain"""
    # Returns:
    # {
    #   'session_id': '...',
    #   'reasoning_chain': [...],
    #   'total_steps': 4,
    #   'model': 'claude-opus-4-5-20251101',
    #   'token_usage': {'input': 100, 'output': 200, 'total': 300}
    # }

def store_reasoning_to_server(self, task_id: int, reasoning_data: Dict,
                               prompt_sent: str, duration_seconds: float) -> bool:
    """POST reasoning to server for admin viewing"""
```

**Modified Methods:**

```python
def _stream_claude_execution(..., session_id: str = None) -> tuple:
    # Now generates/uses session_id
    # Returns: (stdout, stderr, returncode, tools_used, session_id)

def handle_agent_report(...):
    # Now captures reasoning after execution:
    # 1. Records start_time
    # 2. Gets session_id from execution
    # 3. Parses session reasoning
    # 4. Stores to server
```

### 2. agent_garden/src/core/database.py

**New Model:**

```python
class TaskReasoning(Base):
    __tablename__ = "task_reasoning"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, index=True, nullable=False)
    session_id = Column(String(100), index=True)
    reasoning_chain = Column(Text)  # JSON array
    total_steps = Column(Integer, default=0)
    model = Column(String(100))
    token_usage = Column(Text)  # JSON object
    prompt_sent = Column(Text)
    duration_seconds = Column(Float)
    captured_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**New Functions:**

```python
def save_task_reasoning(...) -> Optional[int]
def get_task_reasoning(task_id: int) -> Optional[Dict]
def get_all_task_reasoning(limit: int = 50) -> List[Dict]
```

### 3. unified_app.py

**New Endpoints Added:**

```python
@app.route('/admin/tasks/<int:task_id>/reasoning', methods=['POST'])
def store_task_reasoning_endpoint(task_id):
    """Store reasoning - called by executor"""

@app.route('/admin/tasks/<int:task_id>/reasoning', methods=['GET'])
def get_task_reasoning_endpoint(task_id):
    """Get reasoning for specific task"""

@app.route('/admin/reasoning', methods=['GET'])
def list_all_reasoning():
    """List all reasoning records"""

@app.route('/admin/reasoning/viewer')
def reasoning_viewer_page():
    """Admin HTML page"""
```

**Migration Updated:**

```python
# Added task_reasoning table creation to /AgentGarden/migrate endpoint
CREATE TABLE task_reasoning (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    session_id VARCHAR(100),
    reasoning_chain TEXT,
    total_steps INTEGER DEFAULT 0,
    model VARCHAR(100),
    token_usage TEXT,
    prompt_sent TEXT,
    duration_seconds FLOAT,
    captured_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. templates/admin_reasoning_viewer.html (NEW)

Full admin UI with:
- Dark theme matching existing UI
- Sidebar with task list
- Main content area for reasoning display
- Color-coded step types:
  - 💭 Thinking (red accent)
  - 🔧 Tool Call (green accent)
  - 📋 Tool Result (blue accent)
  - 💬 Response (amber accent)
- Expandable/collapsible sections
- Token usage display
- Duration tracking

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/tasks/{id}/reasoning` | POST | Store reasoning (executor → server) |
| `/admin/tasks/{id}/reasoning` | GET | Get reasoning for task |
| `/admin/reasoning` | GET | List all reasoning (with `?limit=N`) |
| `/admin/reasoning/viewer` | GET | Admin HTML page |

### Example Response: GET /admin/tasks/68/reasoning

```json
{
  "success": true,
  "reasoning": {
    "id": 1,
    "task_id": 68,
    "session_id": "954dc9b1-bcf3-45c9-ab6f-3184a0ff91fb",
    "model": "claude-opus-4-5-20251101",
    "total_steps": 4,
    "duration_seconds": 24.7,
    "token_usage": {
      "input_tokens": 7,
      "output_tokens": 401,
      "total_tokens": 408
    },
    "reasoning_chain": [
      {
        "type": "text",
        "content": "# Fused Glass Art: Quick Facts...",
        "timestamp": "2026-01-12T18:00:14.743Z"
      },
      {
        "type": "tool_use",
        "tool_name": "Write",
        "tool_id": "toolu_01Xk...",
        "tool_input": {
          "file_path": "/path/to/report.md",
          "content": "..."
        },
        "timestamp": "2026-01-12T18:00:16.660Z"
      },
      {
        "type": "tool_result",
        "tool_id": "toolu_01Xk...",
        "content": "File created successfully",
        "is_error": false,
        "timestamp": "2026-01-12T18:00:16.748Z"
      },
      {
        "type": "text",
        "content": "Report saved to report.md",
        "timestamp": "2026-01-12T18:00:20.237Z"
      }
    ]
  }
}
```

---

## Database Schema

### task_reasoning Table

```sql
CREATE TABLE task_reasoning (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,           -- FK to claude_tasks.id
    session_id VARCHAR(100),            -- Claude Code session ID
    reasoning_chain TEXT,               -- JSON array of steps
    total_steps INTEGER DEFAULT 0,      -- Count of reasoning steps
    model VARCHAR(100),                 -- e.g., 'claude-opus-4-5-20251101'
    token_usage TEXT,                   -- JSON: {input, output, total}
    prompt_sent TEXT,                   -- Full prompt sent to Claude
    duration_seconds FLOAT,             -- Execution time
    captured_at TIMESTAMP,              -- When reasoning was captured
    created_at TIMESTAMP DEFAULT NOW()  -- Record creation time
);

CREATE INDEX idx_task_reasoning_task_id ON task_reasoning(task_id);
CREATE INDEX idx_task_reasoning_session_id ON task_reasoning(session_id);
CREATE INDEX idx_task_reasoning_created_at ON task_reasoning(created_at);
```

---

## Bug Fix: Path Generation

### The Problem

Initial implementation failed to find session files:

```
[WARN] Session file not found:
  /Users/vusmac/.claude/projects/Users-vusmac-Library-CloudStorage-OneDrive-Personal-Claude Tools-Reports-reasoning_test/...
```

But actual path was:
```
/Users/vusmac/.claude/projects/-Users-vusmac-Library-CloudStorage-OneDrive-Personal-Claude-Tools-Reports-reasoning-test/...
```

### Differences Found

1. Missing leading `-`
2. Spaces should be `-` not ` `
3. Underscores should be `-`

### The Fix

```python
# Before (broken)
project_key = cwd.replace('/', '-').replace('\\', '-')
if project_key.startswith('-'):
    project_key = project_key[1:]  # WRONG: removed leading dash

# After (fixed)
project_key = cwd.replace('/', '-').replace('\\', '-').replace(' ', '-').replace('_', '-')
if not project_key.startswith('-'):
    project_key = '-' + project_key  # Ensure leading dash
```

---

## Testing Results

### Test Tasks Executed

| Task ID | Type | Steps | Model | Status |
|---------|------|-------|-------|--------|
| #68 | reasoning_test | 4 | claude-opus-4-5-20251101 | ✅ Captured |
| #69 | full_test | 3 | claude-opus-4-5-20251101 | ✅ Captured |

### Reasoning Chain Captured for Task #68

```
Step 1: text
  → Generated report content about fused glass art

Step 2: tool_use
  → Tool: Write
  → Input: {file_path: "report.md", content: "..."}

Step 3: tool_result
  → "File created successfully"

Step 4: text
  → "Report saved to report.md with 2 facts about fused glass art."
```

### Verification Commands

```bash
# List all reasoning records
curl https://gpt-mcp.onrender.com/admin/reasoning

# Get specific task reasoning
curl https://gpt-mcp.onrender.com/admin/tasks/68/reasoning

# Access admin viewer
open https://gpt-mcp.onrender.com/admin/reasoning/viewer
```

---

## Usage Guide

### For Users

1. **Access Admin Viewer:**
   ```
   https://gpt-mcp.onrender.com/admin/reasoning/viewer
   ```

2. **View Task Reasoning:**
   - Click any task in the sidebar
   - See full reasoning chain with:
     - Thinking blocks (Claude's internal reasoning)
     - Tool calls and inputs
     - Tool results
     - Final responses

3. **Understanding the Display:**
   - 💭 **Thinking** (red): Claude's internal reasoning process
   - 🔧 **Tool Call** (green): Tools used with their inputs
   - 📋 **Tool Result** (blue): What the tools returned
   - 💬 **Response** (amber): Claude's text responses

### For Developers

1. **Trigger Reasoning Capture:**
   - Reasoning is automatically captured when `claude_executor.py` runs a task
   - No manual intervention needed

2. **Query Reasoning via API:**
   ```bash
   # Get all reasoning
   GET /admin/reasoning?limit=50

   # Get specific task
   GET /admin/tasks/{task_id}/reasoning
   ```

3. **Manual Reasoning Capture:**
   ```python
   from claude_executor import ClaudeExecutor

   executor = ClaudeExecutor()
   reasoning = executor.parse_session_reasoning(session_id, cwd)
   executor.store_reasoning_to_server(task_id, reasoning, prompt, duration)
   ```

---

## Git Commits

### Commit 1: Main Implementation
```
d3ca049 - Add Claude Reasoning Viewer for admin task monitoring

- claude_executor.py: Capture session ID, parse reasoning from session files
- database.py: Add TaskReasoning model and CRUD operations
- unified_app.py: Add admin endpoints for storing/retrieving reasoning
- admin_reasoning_viewer.html: New admin UI to view full reasoning chain
```

### Commit 2: Bug Fix
```
97ce1f8 - Fix session file path generation for reasoning capture

- Replace spaces with hyphens
- Replace underscores with hyphens
- Ensure leading dash for absolute paths
```

---

## Future Enhancements

Potential improvements discussed but not implemented:

1. **Real-time streaming** - SSE updates as Claude executes
2. **Thinking block highlighting** - Syntax highlighting in thinking content
3. **Search/filter** - Search across reasoning content
4. **Export** - Download reasoning as JSON/Markdown
5. **Diff view** - Compare reasoning between task runs
6. **Cost tracking** - Calculate API costs from token usage

---

## Summary

This implementation captures Claude's full reasoning chain by:

1. **Discovering** that Claude Code already stores thinking blocks in session files
2. **Generating** unique session IDs for each task execution
3. **Parsing** session JSONL files after execution completes
4. **Storing** reasoning data in PostgreSQL for persistence
5. **Displaying** in a clean admin UI at `/admin/reasoning/viewer`

The solution requires no changes to Claude's behavior and captures 100% of the reasoning chain including internal thinking, tool usage, and responses.
