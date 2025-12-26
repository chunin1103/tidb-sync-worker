# Agent Garden - Quick Start Guide

## Setup (One-Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
cp .env.example .env

# 3. Add your Google API key to .env
# Edit .env and replace: GOOGLE_API_KEY=your_actual_api_key_here
```

Get API key: https://aistudio.google.com/app/apikey

---

## Run Server

```bash
python app.py
```

**Server URL:** http://localhost:5001

**Note:** Port 5001 is used by default to avoid macOS AirPlay Receiver conflict on port 5000.

---

## Test Commands

### Check Health
```bash
curl http://localhost:5001/health
```

### Ask the Agent
```bash
curl -X POST http://localhost:5001/execute_agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "inventory_intelligence",
    "message": "What should we cut this week?",
    "session_id": "my-session"
  }'
```

### Clear Session
```bash
curl -X POST http://localhost:5001/clear_session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my-session"}'
```

---

## Available Agent

**`inventory_intelligence`** - Glass inventory management specialist

**Capabilities:**
- Inventory monitoring (stockout alerts)
- Cutting recommendations (biweekly priorities)
- Reorder alerts (Bullseye orders)
- Seasonal deadline tracking (Holly Berry Red June 30)
- Scenario analysis (what-if questions)

**Example Questions:**
- "What should we cut this week?"
- "Check seasonal deadlines"
- "What products need reordering?"
- "Should I cut this Full Sheet or wait?"

---

## Troubleshooting

**Port 5000 in use?**
- macOS AirPlay Receiver uses port 5000
- Agent Garden defaults to port 5001 (no action needed)
- To use custom port: Set `PORT=5002` in `.env`

**API errors?**
- Check `GOOGLE_API_KEY` in `.env` is valid
- Verify you're using `gemini-2.5-flash` model (Gemini 3.0 Flash)

**Dependencies missing?**
```bash
pip install -r requirements.txt
```

---

## Next Steps

1. **Test the agent** with glass business queries
2. **Build frontend** (Phase 2) - Glassmorphism UI
3. **Deploy to Render** - Production deployment

---

**Documentation:** See [README.md](README.md) for full details
