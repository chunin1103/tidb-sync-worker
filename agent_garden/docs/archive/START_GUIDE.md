# Agent Garden - Quick Start Guide

## Starting the Server

### Option 1: Automatic Port Management (Recommended)

The app now automatically finds an available port if the default port (5001) is in use.

```bash
python app.py
```

The server will:
- Try port 5001 first
- If busy, automatically find the next available port (5002, 5003, etc.)
- Display the URL in the console: `Access at: http://localhost:XXXX`

### Option 2: Smart Startup Script

Use the interactive startup script for more control:

```bash
./start.sh
```

If port 5001 is in use, you'll be asked to:
- **(k)** Kill the existing process and use port 5001
- **(f)** Find a new available port automatically

### Option 3: Specify Custom Port

Set a custom port via environment variable:

```bash
PORT=3000 python app.py
```

---

## Port Conflict Solutions

### Problem: "Address already in use"

This happens when another Flask instance or application is using the port.

### Solutions:

1. **Let the app handle it** (easiest):
   ```bash
   python app.py
   ```
   It will automatically use the next available port.

2. **Kill the process manually**:
   ```bash
   lsof -ti:5001 | xargs kill -9
   python app.py
   ```

3. **Use a different port**:
   ```bash
   PORT=8080 python app.py
   ```

---

## New Features: Chat History Sidebar

The app now includes a persistent chat history sidebar with:

- ✅ **Session List**: View all past conversations
- ✅ **Session Preview**: See the first message of each chat
- ✅ **Time Stamps**: "Just now", "5m ago", "2h ago", etc.
- ✅ **Switch Sessions**: Click any session to load it
- ✅ **Delete Sessions**: Hover and click × to delete
- ✅ **New Chat**: Click + to start a fresh conversation
- ✅ **Collapsible**: Click ◀ to hide/show the sidebar
- ✅ **Glassmorphism Design**: Matches the Agent Garden aesthetic

### How to Use:

1. **Open Agent**: Click "OPEN INTERFACE" on any agent card
2. **Sidebar loads**: All past sessions appear on the left
3. **Start chatting**: Current session is highlighted in green
4. **Switch sessions**: Click any past chat to reload it
5. **New chat**: Click the + button to start fresh
6. **Delete chat**: Hover over a session → click × button

---

## Database Connection

The chat history is stored in **Neon PostgreSQL**. Sessions persist across server restarts.

Check connection status:
```bash
python -c "from database import USE_DATABASE; print(f'Database connected: {USE_DATABASE}')"
```

---

## Troubleshooting

### Sidebar not loading sessions?

Check database connection:
```bash
# Should show "Database connected: True"
python -c "from database import USE_DATABASE; print(f'Database: {USE_DATABASE}')"
```

If False, add `DATABASE_URL` to `.env` file.

### Can't start server?

1. Check if port is available: `lsof -i:5001`
2. Use the automatic port finder: `python app.py`
3. Or kill the process: `lsof -ti:5001 | xargs kill -9`

### Sessions not appearing?

1. Make sure `DATABASE_URL` is set in `.env`
2. Run `python init_db.py` to create tables
3. Check browser console for JavaScript errors (F12)

---

## Development Notes

- **Default Port**: 5001 (avoids macOS AirPlay on 5000)
- **Port Range**: Searches 5001-5010 for available port
- **Auto-reload**: Debug mode enabled by default
- **Database**: Neon PostgreSQL (persistent storage)
- **Fallback**: In-memory storage if DATABASE_URL not set

---

## Deployment

For production deployment to Render:

1. Set `DATABASE_URL` environment variable in Render dashboard
2. Deploy normally - no code changes needed
3. The app will use the first available port Render provides

---

**Built with Flask + Google Gemini 3.0 Flash + Neon PostgreSQL**
