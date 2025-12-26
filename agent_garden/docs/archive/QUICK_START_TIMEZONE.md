# Quick Start: Timezone Setup

**For users in Malaysia, Thailand, Vietnam, Singapore, etc.**

## 🚀 3 Steps to Change Timezone

### Step 1: Open Settings

1. Start your Agent Garden application
2. Click the **⚙️ Settings** button (top right of chat interface)

### Step 2: Select Your Timezone

1. In the settings modal, find the **Timezone** dropdown
2. Select your timezone:
   - **Malaysia:** `Malaysia (Kuala Lumpur) - UTC+8`
   - **Thailand:** `Thailand (Bangkok) - UTC+7`
   - **Vietnam:** `Vietnam (Ho Chi Minh) - UTC+7`
   - **Singapore:** `Singapore - UTC+8`
   - **London:** `United Kingdom (London) - UTC+0/+1`
3. Click **SAVE SETTINGS**

### Step 3: Restart Celery

1. After saving, a yellow notice appears: "⚠️ Restart Required"
2. Click the **RESTART NOW** button
3. Wait 5-10 seconds for Celery Beat to restart

**Done!** ✅ Your schedules now run in your local timezone!

---

## 📅 What This Changes

### Before (Default: Los Angeles Time)
```
Morning Report: 7:00 AM PST (Pacific Time)
Health Check: Every 6 hours
Weekly Report: Monday 8:00 AM PST
```

### After (Example: Malaysia Time)
```
Morning Report: 7:00 AM MYT (Malaysia Time)
Health Check: Every 6 hours
Weekly Report: Monday 8:00 AM MYT
```

**All times shift to your local timezone automatically!**

---

## 🔍 Verify It's Working

1. **Check Dashboard Indicator**
   - Open Autonomous Agents Dashboard
   - Look for: `🌍 Kuala Lumpur` (or your city)
   - Hover over it to see full timezone name

2. **Check Settings Modal**
   - Open Settings again
   - "Current Timezone" should show your selection

3. **Monitor Next Task Run**
   - Tasks will now trigger at the time shown in YOUR timezone
   - Example: "7:00 AM" means 7:00 AM in Malaysia, not LA!

---

## ⚠️ Important Notes

### Must Restart Celery Beat
- **Timezone changes DO NOT apply until restart**
- Always click "RESTART NOW" after changing timezone
- The restart takes 5-10 seconds

### All Users See Same Timezone
- This is a system-wide setting
- All users see schedules in the same timezone
- Perfect for teams in one location
- If you have global team members, consider using UTC

### Daylight Saving Time
- Automatically handled by the system
- No manual adjustments needed
- Timezones like London (UTC+0/+1) adjust automatically

---

## 🌏 Most Common Timezones

| Region | Timezone | UTC Offset |
|--------|----------|------------|
| **Malaysia** | Asia/Kuala_Lumpur | UTC+8 |
| **Singapore** | Asia/Singapore | UTC+8 |
| **Thailand** | Asia/Bangkok | UTC+7 |
| **Vietnam** | Asia/Ho_Chi_Minh | UTC+7 |
| **Indonesia** | Asia/Jakarta | UTC+7 |
| **Philippines** | Asia/Manila | UTC+8 |
| **Hong Kong** | Asia/Hong_Kong | UTC+8 |
| **India** | Asia/Kolkata | UTC+5:30 |
| **Dubai** | Asia/Dubai | UTC+4 |
| **London** | Europe/London | UTC+0/+1 |

---

## 🆘 Troubleshooting

### Problem: Setting button doesn't open
**Solution:** Refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

### Problem: Timezone not saved
**Solution:**
1. Check database connection in `.env`
2. Verify `DATABASE_URL` is set
3. Run: `python3 init_db.py`

### Problem: Tasks still running at wrong time
**Solution:**
1. Make sure you clicked "RESTART NOW"
2. Check Celery Beat is running: `ps aux | grep celery`
3. Manually restart if needed: `./start_celery_beat.sh`

### Problem: "Error loading timezones"
**Solution:**
1. Check Flask server is running
2. Verify database connection
3. Restart Flask: `python3 app.py`

---

## 🎯 Example: Switching to Malaysia Time

**Current Setup:**
- Timezone: America/Los_Angeles (default)
- Morning Report: 7:00 AM PST

**Goal:**
- Change to Malaysia Time (UTC+8)
- Morning Report at 7:00 AM MYT

**Steps:**
1. Click ⚙️ Settings
2. Select "Malaysia (Kuala Lumpur) - UTC+8"
3. Click SAVE SETTINGS
4. Click RESTART NOW
5. Verify: Dashboard shows "🌍 Kuala Lumpur"

**Result:**
- Morning Report now runs at 7:00 AM Malaysia Time
- 16-hour difference from LA time
- All other schedules also in Malaysia Time

---

## 📞 Need Help?

**Check Documentation:**
- Full Guide: `TIMEZONE_GUIDE.md`
- Implementation Details: `TIMEZONE_IMPLEMENTATION_SUMMARY.md`

**Common Commands:**
```bash
# Restart Celery Beat manually
pkill -f "celery.*beat"
./start_celery_beat.sh

# Check current timezone
python3 -c "from database import get_timezone; print(get_timezone())"

# Verify Celery timezone
python3 -c "from celery_app import celery_app; print(celery_app.conf.timezone)"
```

---

## ✅ Success Checklist

After changing timezone, verify:

- [ ] Settings modal shows new timezone as "Current Timezone"
- [ ] Dashboard shows correct city in timezone indicator (🌍)
- [ ] Celery Beat has been restarted (click RESTART NOW)
- [ ] No errors in Flask server logs
- [ ] Schedule times make sense for your timezone

If all checked ✅, you're all set!

---

**Last Updated:** December 24, 2024
**Feature Version:** 1.0
**Status:** Production Ready ✅
