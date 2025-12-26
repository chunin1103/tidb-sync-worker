# Timezone Configuration Guide

**Feature Added:** December 24, 2024

## Overview

Agent Garden now supports **customizable timezones** for all scheduled tasks. You can set your timezone through the UI, and all autonomous agents will run according to your local time.

## 🌍 Supported Timezones

### Asia
- Malaysia (Kuala Lumpur) - UTC+8
- Singapore - UTC+8
- Thailand (Bangkok) - UTC+7
- Vietnam (Ho Chi Minh) - UTC+7
- Indonesia (Jakarta) - UTC+7
- Philippines (Manila) - UTC+8
- Hong Kong - UTC+8
- China (Shanghai) - UTC+8
- Japan (Tokyo) - UTC+9
- South Korea (Seoul) - UTC+9
- India (Kolkata) - UTC+5:30
- UAE (Dubai) - UTC+4

### Europe
- United Kingdom (London) - UTC+0/+1
- France (Paris) - UTC+1/+2
- Germany (Berlin) - UTC+1/+2
- Netherlands (Amsterdam) - UTC+1/+2
- Spain (Madrid) - UTC+1/+2
- Italy (Rome) - UTC+1/+2
- Russia (Moscow) - UTC+3

### America
- USA (New York/Eastern) - UTC-5/-4
- USA (Chicago/Central) - UTC-6/-5
- USA (Denver/Mountain) - UTC-7/-6
- USA (Los Angeles/Pacific) - UTC-8/-7
- Canada (Toronto) - UTC-5/-4
- Canada (Vancouver) - UTC-8/-7
- Mexico (Mexico City) - UTC-6/-5
- Brazil (São Paulo) - UTC-3

### Pacific
- Australia (Sydney) - UTC+10/+11
- Australia (Melbourne) - UTC+10/+11
- New Zealand (Auckland) - UTC+12/+13

### Africa
- Egypt (Cairo) - UTC+2
- South Africa (Johannesburg) - UTC+2

## 🎯 How to Change Timezone

### Via Web UI (Recommended)

1. **Open Settings**
   - Click the ⚙️ Settings button in the chat interface
   - Or access from the main navigation

2. **Select Your Timezone**
   - Choose your timezone from the dropdown
   - Timezones are organized by region for easy browsing
   - Current timezone is displayed for reference

3. **Save Changes**
   - Click "SAVE SETTINGS"
   - Wait for confirmation message

4. **Restart Celery Beat**
   - Click the "RESTART NOW" button in the restart notice
   - Or manually restart using the scripts (see below)

### Via API

```bash
# Get current settings
curl http://localhost:5000/get_settings

# Update timezone
curl -X POST http://localhost:5000/update_timezone \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Asia/Kuala_Lumpur"}'

# Get available timezones
curl http://localhost:5000/get_timezones
```

### Via Python

```python
from database import update_timezone, get_timezone

# Update timezone
update_timezone('Asia/Bangkok')

# Verify change
current_tz = get_timezone()
print(f"Timezone: {current_tz}")
```

## 🔄 Applying Timezone Changes

After changing the timezone, you **MUST restart Celery Beat** for changes to take effect.

### Option 1: UI Restart (Easiest)

Click the "RESTART NOW" button that appears after saving settings.

### Option 2: Manual Restart

```bash
# Stop Celery Beat
pkill -f "celery.*beat"

# Start Celery Beat again
./start_celery_beat.sh
```

### Option 3: Restart Both Worker and Beat

```bash
# Stop all Celery processes
pkill -f "celery worker"
pkill -f "celery beat"

# Start them again
./start_celery_worker.sh
./start_celery_beat.sh
```

## 📋 How It Works

### Architecture

1. **Database Storage**
   - Timezone is stored in `system_settings` table
   - Single row (ID=1) contains application-wide timezone
   - Default: `America/Los_Angeles`

2. **Celery Integration**
   - `celery_app.py` reads timezone from database on startup
   - All schedules use this timezone
   - When you change timezone, Celery Beat must be restarted

3. **UI Integration**
   - Settings modal allows timezone selection
   - Timezone indicator shows current timezone in dashboard
   - All schedule times are displayed in the configured timezone

### Database Schema

```python
class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    timezone = Column(String(100), default='America/Los_Angeles')
    updated_at = Column(DateTime)
    created_at = Column(DateTime)
```

## 🧪 Testing Your Timezone

### Test 1: Verify Database Setting

```python
from database import get_timezone
print(f"Current timezone: {get_timezone()}")
```

### Test 2: Verify Celery Configuration

```python
from celery_app import celery_app
print(f"Celery timezone: {celery_app.conf.timezone}")
```

### Test 3: Verify UI Display

1. Open Autonomous Agents Dashboard
2. Check timezone indicator: `🌍 [Your City]`
3. Hover over it to see full timezone name

### Test 4: Trigger a Test Task

```python
from autonomous_agents import trigger_task_now

# Trigger a task and check the timestamp
result = trigger_task_now('morning_intelligence_report')
print(f"Task ID: {result.id}")
```

## 📊 Examples

### Example 1: Switch from US to Malaysia

```bash
# Current: America/Los_Angeles (UTC-8)
# Schedule: Morning Report at 7:00 AM PST

# Change to: Asia/Kuala_Lumpur (UTC+8)
curl -X POST http://localhost:5000/update_timezone \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Asia/Kuala_Lumpur"}'

# Restart Celery Beat
pkill -f "celery.*beat"
./start_celery_beat.sh

# Now: Morning Report will run at 7:00 AM MYT
```

### Example 2: Multi-Region Team

**Scenario:** Team in Thailand wants reports at 9:00 AM Bangkok time

```bash
# Set timezone to Bangkok
curl -X POST http://localhost:5000/update_timezone \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Asia/Bangkok"}'

# Update schedule to 9:00 AM
curl -X POST http://localhost:5000/update_schedule/morning_intelligence_report \
  -H "Content-Type: application/json" \
  -d '{"hour": 9, "minute": 0}'

# Restart Celery Beat
./start_celery_beat.sh
```

## ⚠️ Important Notes

### Daylight Saving Time (DST)

- Timezones that observe DST (like `America/New_York`) automatically adjust
- No manual intervention needed during DST transitions
- Uses Python's `pytz` library for accurate timezone handling

### Single Timezone Only

- **Current implementation:** One timezone for the entire application
- All users see tasks in the same timezone
- **Best for:** Single team/business in one timezone
- **Future:** Per-user timezone display (if needed)

### Restart Required

- Timezone changes do NOT apply automatically
- You MUST restart Celery Beat after changing timezone
- Worker processes don't need restart (only Beat)

### Schedule Times

- All schedule times are stored as hour/minute (e.g., 7:00)
- Time interpretation changes when timezone changes
- Example: "7:00 AM" means 7:00 AM in the configured timezone

## 🔧 Troubleshooting

### Problem: Timezone not changing

**Solution:**
```bash
# Ensure Celery Beat is restarted
pkill -f "celery.*beat"
./start_celery_beat.sh

# Verify timezone
python3 -c "from celery_app import celery_app; print(celery_app.conf.timezone)"
```

### Problem: Tasks running at wrong time

**Check:**
1. Database timezone: `python3 -c "from database import get_timezone; print(get_timezone())"`
2. Celery timezone: `python3 -c "from celery_app import celery_app; print(celery_app.conf.timezone)"`
3. They should match! If not, restart Celery Beat.

### Problem: UI shows wrong timezone

**Solution:**
```bash
# Clear browser cache and reload
# Or force reload: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
```

### Problem: Database error when saving

**Check:**
```python
from database import USE_DATABASE
print(f"Database enabled: {USE_DATABASE}")

# If False, check your DATABASE_URL in .env
```

## 📝 Developer Notes

### Adding New Timezones

Edit `database.py:831` in the `get_available_timezones()` function:

```python
timezones = [
    {'value': 'Asia/Taipei', 'label': 'Taiwan (Taipei) - UTC+8', 'region': 'Asia'},
    # Add your timezone here
]
```

### Programmatic Access

```python
# Get all timezone functions
from database import (
    get_system_settings,
    get_timezone,
    update_timezone,
    get_available_timezones
)

# API endpoints
# GET  /get_settings     - Get current settings
# GET  /get_timezones    - Get available timezones
# POST /update_timezone  - Update timezone
```

---

## Summary

✅ **Supported:** 32 timezones across 5 regions
✅ **UI Control:** Easy settings modal
✅ **API Access:** Full REST API support
✅ **Auto DST:** Automatic daylight saving time handling
✅ **Production Ready:** Tested and documented

**Default Timezone:** `America/Los_Angeles` (UTC-8/-7)

For additional timezone requests or issues, please file an issue on GitHub!
