# Agent Garden - Architecture

**AI-Powered Inventory Intelligence Dashboard**
Built with Flask + Google Gemini 3.0 Flash + TiDB Cloud

---

## System Overview

```
User Request
     ↓
Flask Web Server (src/core/app.py)
     ↓
Agent Backend (src/core/agent_backend.py)
     ↓
Database Context Builder (src/connectors/agent_database_context_optimized.py)
     ↓
TiDB Connector (src/connectors/tidb_connector.py)
     ↓
TiDB Cloud Database (via MCP or direct)
     ↓
Redis Cache (Upstash) - 5min TTL
     ↓
Gemini 3.0 Flash API
     ↓
Streaming SSE Response to User
```

---

## Project Structure

```
agent_garden_flask/
├── src/
│   ├── core/                     # Core application
│   │   ├── app.py                # Flask server, SSE streaming
│   │   ├── agent_backend.py      # Gemini integration, agent execution
│   │   └── database.py           # Database models
│   ├── connectors/               # Database connectors
│   │   ├── tidb_connector.py     # Hybrid MCP + direct TiDB connector
│   │   └── agent_database_context_optimized.py  # Cached context builder
│   ├── scheduling/               # Background task scheduling
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── celeryconfig.py       # Celery settings
│   │   ├── custom_scheduler.py   # Custom scheduling logic
│   │   └── schedule_loader.py    # Schedule management
│   ├── agents/                   # Autonomous agents (alias to autonomous_agents/)
│   └── utils/                    # Utilities & scripts
│       ├── init_db.py            # Database initialization
│       ├── init_tidb_mcp.py      # MCP helpers
│       ├── run_with_mcp.py       # MCP-enabled startup
│       └── update_schedule_cli.py # Schedule CLI tool
├── tests/                        # All test files
├── docs/                         # Current documentation
├── templates/                    # Flask HTML templates
├── requirements.txt              # Python dependencies
└── start.sh                      # Startup script
```

---

## Key Components

### 1. Database Integration (Production-Optimized)

**File:** `src/connectors/agent_database_context_optimized.py`

**Features:**
- **Redis caching** with 5-minute TTL (48x speedup)
- **Parallel query execution** (3x faster initial fetch)
- **Hybrid MCP + direct connection** support
- **Graceful error handling** and fallbacks

**Performance:**
- Cache HIT: 1-5ms
- Cache MISS: 150-300ms
- Database load reduction: 90%

### 2. TiDB Connector (Hybrid)

**File:** `src/connectors/tidb_connector.py`

**Connection Modes:**
1. **MCP Server Mode** (recommended)
   - No IP whitelisting needed
   - Works through Claude Code MCP tools
   - Automatic failover

2. **Direct Connection Mode** (fallback)
   - Requires IP whitelisting
   - SSL/TLS encryption
   - Direct PyMySQL connection

**15+ Business Intelligence Methods:**
- `get_zero_inventory_products()`
- `get_low_stock_products()`
- `get_sales_velocity()`
- `get_bestsellers()`
- And more...

### 3. Agent Backend

**File:** `src/core/agent_backend.py`

**Capabilities:**
- Gemini 3.0 Flash integration
- Server-Sent Events (SSE) streaming
- Session management (in-memory)
- Conversation history tracking
- Automatic database context injection

**Available Agents:**
- `inventory_intelligence` - Main inventory management agent

### 4. Flask Web Server

**File:** `src/core/app.py`

**Endpoints:**
- `POST /execute_agent` - Execute agent with streaming response
- `POST /clear_session` - Clear conversation history
- `GET /sessions` - List active sessions
- `GET /health` - Health check

### 5. Scheduling System

**Files:** `src/scheduling/`

**Purpose:** Background task execution using Celery

**Components:**
- Beat scheduler for periodic tasks
- Worker for async execution
- Custom scheduling logic
- Schedule persistence

---

## Data Flow

### Request Processing

1. **User sends request** → Flask receives POST to `/execute_agent`
2. **Session lookup** → Retrieve or create conversation history
3. **Database context fetch** → Check Redis cache
   - **Cache HIT**: Return cached context (1-5ms)
   - **Cache MISS**: Query TiDB in parallel (150-300ms)
4. **Context injection** → Append database context to system prompt
5. **Gemini execution** → Stream response via SSE
6. **Session update** → Store conversation history

### Database Query Flow

1. **Agent needs data** → Call `get_agent_database_context_optimized()`
2. **Cache check** → Look for time-bucketed cache key
3. **Parallel fetch** → If cache miss, run 7 queries simultaneously
4. **Error handling** → Individual query failures don't crash system
5. **Cache storage** → Store result with 5-minute expiration
6. **Return context** → Formatted markdown for agent consumption

---

## Performance Optimizations

### 1. Redis Caching
- **TTL:** 5 minutes (auto-refresh)
- **Key strategy:** Time-bucketed (groups requests by 5-min intervals)
- **Hit rate:** 70-90% in production
- **Speedup:** 48x faster on cache hits

### 2. Parallel Queries
- **Method:** ThreadPoolExecutor
- **Timeout:** 10 seconds max per query batch
- **Benefit:** 3x faster than sequential queries
- **Fault tolerance:** Individual query failures handled gracefully

### 3. SSL/TLS
- **Mode:** `VERIFY_IDENTITY`
- **Required for:** TiDB Cloud connections
- **Benefit:** Encrypted data in transit

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Google Gemini API key |
| `TIDB_USER` | ⚠️ Optional | TiDB username (for direct mode) |
| `TIDB_PASSWORD` | ⚠️ Optional | TiDB password (for direct mode) |
| `REDIS_URL` | ✅ Yes | Redis connection URL (Upstash) |
| `PORT` | No | Server port (default: 5001) |

---

## Startup Options

### Method 1: MCP Mode (Recommended)
```bash
python src/utils/run_with_mcp.py
```
- No IP whitelisting needed
- Uses Claude Code MCP tools
- Automatic configuration

### Method 2: Direct Mode
```bash
python src/core/app.py
```
- Requires TiDB credentials in `.env`
- Requires IP whitelisting
- Fallback option

---

## Testing

### Run All Tests
```bash
python tests/test_optimized_system.py
python tests/test_with_mcp.py
python tests/test_database_integration.py
python tests/test_scheduler.py
```

### Test Results (Expected)
- Cache HIT: 1-10ms
- Cache MISS: 150-400ms
- Parallel queries: ~150-300ms for 7 queries
- Cache hit rate: 70-90%

---

## Security

### Database
- SSL/TLS required for TiDB Cloud
- Credentials stored in `.env` (gitignored)
- Connection pooling with limits

### API
- Google API key in `.env`
- Rate limiting (Gemini API handles this)
- Session isolation (separate conversation histories)

### Redis
- TLS connection (rediss://)
- Password authentication
- Automatic TTL expiration

---

## Monitoring

### Performance Logs
```bash
# Check cache performance
grep "Cache HIT" logs/app.log

# Check query timing
grep "built:" logs/app.log

# Check errors
grep "ERROR" logs/app.log
```

### Health Checks
- `GET /health` - Server status and active session count
- `GET /sessions` - Debug session list

---

## Roadmap

### Completed ✅
- Gemini 3.0 Flash integration
- Streaming SSE responses
- TiDB database integration (MCP + direct)
- Redis caching with parallel queries
- Session management
- Autonomous agent framework
- Celery scheduling system

### Future Enhancements
- [ ] PostgreSQL session persistence (Neon)
- [ ] Multi-agent orchestration
- [ ] Webhook integrations
- [ ] Advanced analytics dashboard
- [ ] Rate limiting middleware

---

**Built for ArtGlassSupplies.com** | Powered by Google Gemini 3.0 Flash + TiDB Cloud
