# Quick Start Guide - Schedule Management

## 🚀 Getting Started

Your Agent Garden now has **smart schedule management** that automatically syncs with the database!

## ✅ What's Fixed

- ✅ Schedules now update without restarting Celery Beat
- ✅ Changes take effect within 60 seconds
- ✅ Single source of truth (database)
- ✅ No more cache issues

## 📋 Current Schedules

| Task | Schedule | Time |
|------|----------|------|
| Morning Intelligence Report | Daily | **9:15 AM** |
| Inventory Health Check | Every 6 hours | Continuous |
| Weekly Summary Report | Monday | 8:00 AM |

Timezone: **Asia/Ho_Chi_Minh (UTC+7)**

## 🎯 Quick Commands

### Start Celery Beat
```bash
./start_celery_beat.sh
```

### View All Schedules
```bash
python update_schedule_cli.py --list
```

### Test Configuration
```bash
python test_scheduler.py
```

### Update a Schedule
```bash
# Change morning report to 7:30 AM
python update_schedule_cli.py morning_intelligence_report --hour 7 --minute 30

# Change inventory check to every 4 hours (14400 seconds)
python update_schedule_cli.py inventory_health_check --interval 14400

# Disable a schedule
python update_schedule_cli.py weekly_summary_report --disable
```

## 🌐 Via Web UI

1. Open Agent Garden dashboard
2. Go to Settings → Schedules
3. Edit the schedule
4. Click Save
5. **Wait 60 seconds** - changes auto-apply!

## 📊 Via API

```bash
# Update schedule
curl -X POST http://localhost:5000/update_schedule/morning_intelligence_report \
  -H "Content-Type: application/json" \
  -d '{"hour": 8, "minute": 0}'

# View schedules
curl http://localhost:5000/get_schedules
```

## ⚡ How Fast Do Changes Apply?

- **Update schedule**: Instant (saves to database)
- **Celery Beat picks up change**: Within 60 seconds
- **Next execution**: At the new scheduled time

**No restart needed!** The DatabaseScheduler automatically refreshes every 60 seconds.

## 🔍 Verify Schedule is Working

### 1. Check what's in the database
```bash
python -c "from database import get_schedule; import json; print(json.dumps(get_schedule('morning_intelligence_report'), indent=2))"
```

### 2. Check what Celery Beat is using
```bash
grep "Loaded.*schedules" celery_beat.log
```

### 3. Watch for schedule refresh
```bash
# Look for this message every 60 seconds
grep "Refreshing schedules from database" celery_beat.log
```

## 🚨 Troubleshooting

### "Schedule didn't change!"

**Wait 60 seconds** - Auto-refresh happens every minute, not instantly

### "Wrong time showing in logs"

Check your timezone:
```bash
python -c "from database import get_timezone; print(get_timezone())"
```

Should show: `Asia/Ho_Chi_Minh`

### "Celery Beat won't start"

Test the scheduler:
```bash
python test_scheduler.py
```

If all tests pass, you're good to go!

## 📚 More Information

- **Full Documentation**: `SCHEDULE_MANAGEMENT.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Troubleshooting**: `SCHEDULE_MANAGEMENT.md` → Troubleshooting section

## 💡 Tips

1. **Use the CLI for quick changes** - Faster than opening the UI
2. **Test after updates** - Check logs to verify schedule picked up
3. **Set reasonable intervals** - Don't go below 5 minutes for heavy tasks
4. **Disable instead of delete** - You can re-enable later

## 🎉 You're All Set!

The schedule management system is ready to use. No more manual restarts, no more cache issues, just smooth automatic updates!

**Next Step**: Start Celery Beat and enjoy hassle-free scheduling!

```bash
./start_celery_beat.sh
```
