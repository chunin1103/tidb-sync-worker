# Agent Garden - Flask Backend

**AI-Powered Inventory Intelligence Dashboard**
Built with Flask + Google Gemini 3.0 Flash

---

## Quick Start

### 1. Install Dependencies

```bash
cd agent_garden_flask
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your Google API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

**Get your API key:** https://aistudio.google.com/app/apikey

### 3. Run Development Server

```bash
python app.py
```

Server will start at: **http://localhost:5001**

**Note:** Default port is 5001 to avoid conflict with macOS AirPlay Receiver (which uses port 5000). You can change the port by setting `PORT=<your_port>` in `.env`.

---

## Project Structure

```
agent_garden_flask/
├── app.py                # Flask server (routes, SSE streaming)
├── agent_backend.py      # Gemini 3.0 integration (intelligence engine)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (API key)
├── .env.example          # Template for .env
├── .gitignore            # Git exclusions
├── README.md             # This file
└── templates/
    └── index.html        # UI (placeholder - Phase 2)
```

---

## API Endpoints

### **POST /execute_agent**
Execute an agent with streaming response (SSE).

**Request:**
```json
{
  "agent_type": "inventory_intelligence",
  "message": "What should we cut this week?",
  "session_id": "unique-session-id"
}
```

**Response:** `text/event-stream` (Server-Sent Events)
```
data: 📊 BIWEEKLY CUTTING PRIORITIES (Top 3 Urgent):

data: Priority 1: Product 0001-0044-F (5×5)
data: ├─ Current: 19 days (CRITICAL - below 91 day target)
...
data: [DONE]
```

### **POST /clear_session**
Clear conversation history for a session.

**Request:**
```json
{
  "session_id": "session-to-clear"
}
```

### **GET /sessions**
Get list of active sessions (debugging).

### **GET /health**
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 3
}
```

---

## Available Agents

### **inventory_intelligence**
Specialized agent for ArtGlassSupplies.com glass inventory management.

**Capabilities:**
- Inventory monitoring (stockout alerts, overstock detection)
- Cutting recommendations (biweekly priorities)
- Reorder alerts (Bullseye orders)
- Seasonal deadline tracking (Holly Berry Red, Tekta)
- Scenario analysis (what-if questions)
- **Session management** (view past chats, switch conversations)
- **Export conversations** (JSON, Markdown, Text formats)

**Example Queries:**
- "What should we cut this week?"
- "Check seasonal deadlines"
- "Should I cut this Full Sheet or wait?"
- "What products need reordering?"

---

## Testing with cURL

### Execute Agent (Streaming)
```bash
curl -X POST http://localhost:5001/execute_agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "inventory_intelligence",
    "message": "Hello! Can you explain your role?",
    "session_id": "test-session-1"
  }'
```

### Clear Session
```bash
curl -X POST http://localhost:5001/clear_session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1"}'
```

### Check Health
```bash
curl http://localhost:5001/health
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Google Gemini API key |
| `FLASK_ENV` | No | `development` or `production` (default: development) |
| `FLASK_DEBUG` | No | `True` or `False` (default: True) |
| `PORT` | No | Server port (default: 5001, avoids macOS AirPlay on 5000) |

### Gemini Configuration

Model: `gemini-2.5-flash` (Gemini 3.0 Flash)
Temperature: `0.7`

---

## Deployment (Render)

### 1. Create `render.yaml` (Optional)
```yaml
services:
  - type: web
    name: agent-garden
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11
```

### 2. Deploy
1. Push to GitHub repository
2. Connect repository to Render
3. Add `GOOGLE_API_KEY` environment variable in Render dashboard
4. Deploy

**Production Start Command:**
```bash
gunicorn app:app --workers 4 --timeout 120 --bind 0.0.0.0:$PORT
```

---

## Conversation History

Sessions are stored **in-memory** (current implementation).

**Future Enhancement:** Migrate to Redis or PostgreSQL for:
- Session persistence across server restarts
- Multi-instance deployment support
- Automatic session expiration (TTL)

---

## Error Handling

The backend handles common errors gracefully:

- ⚠️ **Authentication Error:** Invalid API key
- ⚠️ **Rate Limit:** Too many requests (429 errors)
- ⚠️ **Network Error:** Connection timeouts
- ⚠️ **Validation Error:** Invalid agent type or missing fields

All errors are logged and returned as user-friendly SSE messages.

---

## Development Notes

### Adding New Agents

1. Add system prompt to `AGENT_PROMPTS` in `agent_backend.py`:
```python
AGENT_PROMPTS = {
    "inventory_intelligence": "...",
    "operations_optimizer": "Your new agent prompt here..."
}
```

2. Update validation in `execute_agent()` (automatic)

3. Document in this README

### Session Management

Current implementation: In-memory dictionary
- ✅ Fast access
- ✅ No dependencies
- ❌ Lost on server restart
- ❌ Not suitable for multi-instance deployment

Migrate to Redis when scaling.

---

## Roadmap

### Phase 1: Backend ✅ (Complete)
- [x] Gemini 3.0 Flash integration
- [x] Streaming SSE responses
- [x] Conversation history management
- [x] Inventory Intelligence agent
- [x] Error handling
- [x] API endpoints

### Phase 2: Frontend ✅ (Complete)
- [x] Agent selection UI (glassmorphism cards)
- [x] Chat interface with streaming
- [x] Session management UI
- [x] Dark mode aesthetic (#0e1117, #00ff9d)
- [x] Chat history sidebar
- [x] Session export (JSON, Markdown, Text)

### Phase 3: Deployment
- [ ] Render deployment
- [ ] Health monitoring
- [ ] Session persistence (Neon PostgreSQL) ✅

---

## Support

**Issues?** Check:
1. API key is valid (`GOOGLE_API_KEY` in `.env`)
2. Dependencies installed (`pip install -r requirements.txt`)
3. Port 5001 is available (or set custom `PORT` in `.env`)
4. Python 3.10+ installed

**macOS Users:** If you see "Port 5000 in use", this is AirPlay Receiver. The app now defaults to port 5001 to avoid this conflict.

**Logs:** Check console output for detailed error messages.

---

**Built for ArtGlassSupplies.com** | Powered by Google Gemini 3.0 Flash
