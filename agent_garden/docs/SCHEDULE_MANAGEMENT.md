# Schedule Management Guide

## Overview

Agent Garden uses a **database-driven scheduling system** that allows you to update task schedules at runtime without restarting Celery Beat.

## Architecture

### Components

1. **Database (PostgreSQL/Neon)**
   - Table: `schedule_configs`
   - Stores all schedule definitions (time, interval, enabled status)
   - Single source of truth for all schedules

2. **DatabaseScheduler (custom_scheduler.py)**
   - Custom Celery Beat scheduler
   - Reads schedules directly from database
   - Auto-refreshes every 60 seconds
   - No persistent cache files

3. **Schedule Loader (schedule_loader.py)**
   - Loads schedules from database
   - Converts to Celery Beat format (crontab/interval)

4. **Web API (app.py)**
   - `/get_schedules` - View all schedules
   - `/get_schedule/<task_name>` - View specific schedule
   - `/update_schedule/<task_name>` - Update schedule

## How It Works

```
┌─────────────┐
│   Database  │ ← Single source of truth
│  (schedule_ │
│   configs)  │
└──────┬──────┘
       │
       ↓ (reads every 60s)
┌─────────────────┐
│ DatabaseScheduler│ ← Custom Celery Beat scheduler
└──────┬──────────┘
       │
       ↓ (executes tasks)
┌─────────────┐
│ Celery Worker│
└─────────────┘
```

## Default Schedules

| Task | Schedule | Description |
|------|----------|-------------|
| Morning Intelligence Report | Daily at 9:15 AM | Comprehensive morning briefing |
| Inventory Health Check | Every 6 hours | Quick inventory status check |
| Weekly Summary Report | Monday at 8:00 AM | Week-over-week analysis |

## Updating Schedules

### Via Web UI

1. Open the Agent Garden dashboard
2. Navigate to Settings → Schedules
3. Edit the schedule time
4. Click "Save"
5. **Changes take effect within 60 seconds** (no restart needed!)

### Via API

```bash
# Update morning report to 7:30 AM
curl -X POST http://localhost:5000/update_schedule/morning_intelligence_report \
  -H "Content-Type: application/json" \
  -d '{"hour": 7, "minute": 30}'

# Change inventory check to every 4 hours
curl -X POST http://localhost:5000/update_schedule/inventory_health_check \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 14400}'

# Disable a schedule
curl -X POST http://localhost:5000/update_schedule/weekly_summary_report \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Via Database

```python
from database import update_schedule

# Update morning report to 8:00 AM
update_schedule('morning_intelligence_report', {
    'hour': 8,
    'minute': 0
})
```

## Schedule Format

### Cron Schedules (Specific Times)

```python
{
    "schedule_type": "cron",
    "hour": 9,           # 0-23 (24-hour format)
    "minute": 15,        # 0-59
    "day_of_week": null  # 0-6 (Monday=0) or null for every day
}
```

### Interval Schedules (Recurring)

```python
{
    "schedule_type": "interval",
    "interval_seconds": 21600  # Every 6 hours (6 * 60 * 60)
}
```

## Timezone Configuration

The system uses the timezone configured in the database (default: Asia/Ho_Chi_Minh).

### Check Current Timezone

```bash
curl http://localhost:5000/get_system_settings
```

### Update Timezone

```bash
curl -X POST http://localhost:5000/update_timezone \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Asia/Singapore"}'
```

## Monitoring

### View Active Schedules

```bash
# Via API
curl http://localhost:5000/get_schedules

# Via command line
python -c "from schedule_loader import get_schedule_summary; import json; print(json.dumps(get_schedule_summary(), indent=2))"
```

### Check Celery Beat Logs

```bash
# Look for schedule refresh messages
grep "Refreshing schedules" celery_beat.log

# Verify schedule execution
grep "Scheduler: Sending due task" celery_beat.log
```

## Troubleshooting

### Problem: Schedule changes not taking effect

**Solution 1: Wait up to 60 seconds**
- The DatabaseScheduler refreshes every 60 seconds
- Changes are NOT instant but should appear within 1 minute

**Solution 2: Check database**
```bash
python -c "from database import get_schedule; import json; print(json.dumps(get_schedule('morning_intelligence_report'), indent=2))"
```

**Solution 3: Restart Celery Beat (last resort)**
```bash
# Stop Celery Beat (Ctrl+C)
# Start again
./start_celery_beat.sh
```

### Problem: Old cache file causing issues

If you see a `celerybeat-schedule.db` file, delete it:
```bash
rm celerybeat-schedule.db
```

This file is from the old PersistentScheduler and is no longer needed.

### Problem: Task running at wrong time

**Check timezone mismatch:**
```bash
# Check system timezone
python -c "from database import get_timezone; print(get_timezone())"

# Check if schedule is in correct timezone
# Example: 9:15 AM in Asia/Ho_Chi_Minh = 9:15 AM local time
```

### Problem: DatabaseScheduler not loading

**Check imports:**
```bash
python -c "from custom_scheduler import DatabaseScheduler; print('✅ OK')"
```

**Check start command:**
```bash
# Ensure start_celery_beat.sh uses:
celery -A celery_app beat -S custom_scheduler:DatabaseScheduler --max-interval 60
```

## Migration from Old System

If you were using the old PersistentScheduler with `celeryconfig.py`:

1. ✅ Hardcoded schedules removed from `celeryconfig.py`
2. ✅ All schedules now in database
3. ✅ DatabaseScheduler automatically loads from database
4. ✅ No manual restarts needed

### What Changed

**Before:**
- Schedules hardcoded in `celeryconfig.py`
- Changes required code edit + restart
- Cache file caused stale schedules

**After:**
- Schedules in database (editable via UI)
- Changes take effect in ~60 seconds
- No cache file, always fresh data

## Best Practices

1. **Use the Web UI** for schedule changes (safer than direct DB edits)
2. **Test changes** by checking logs after 1-2 minutes
3. **Set reasonable intervals** (avoid intervals < 5 minutes for heavy tasks)
4. **Monitor database** for schedule_configs table size
5. **Use disable flag** instead of deleting schedules

## Technical Details

### Refresh Interval

The DatabaseScheduler refreshes every 60 seconds by default. You can change this in `start_celery_beat.sh`:

```bash
celery -A celery_app beat \
    -S custom_scheduler:DatabaseScheduler \
    --max-interval 30  # ← Change to 30 seconds for faster updates
```

**Trade-off:**
- Lower interval = faster updates, more database queries
- Higher interval = slower updates, fewer database queries

### Schedule Entry Lifecycle

1. **Database Update** - Schedule changed via API/UI
2. **Wait Period** - Up to 60 seconds
3. **Scheduler Refresh** - DatabaseScheduler reads from DB
4. **Schedule Active** - New schedule takes effect
5. **Task Execution** - Task runs at new time

### Database Schema

```sql
CREATE TABLE schedule_configs (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL,  -- 'cron' or 'interval'
    hour INT,                             -- For cron: 0-23
    minute INT,                           -- For cron: 0-59
    day_of_week INT,                      -- For cron: 0-6 (Mon-Sun)
    interval_seconds INT,                 -- For interval
    enabled INT DEFAULT 1,                -- 1=enabled, 0=disabled
    description TEXT,
    last_modified TIMESTAMP,
    created_at TIMESTAMP
);
```

## Support

If you encounter issues:

1. Check logs: `celery_beat.log` and `celery_worker.log`
2. Verify database: `python -c "from database import get_all_schedules; print(get_all_schedules())"`
3. Test scheduler: `python -c "from custom_scheduler import DatabaseScheduler; print('OK')"`
4. Restart as last resort: Stop Celery Beat → Delete cache → Restart

## Version History

- **v2.0** - DatabaseScheduler with auto-refresh (current)
- **v1.0** - PersistentScheduler with hardcoded schedules (deprecated)
