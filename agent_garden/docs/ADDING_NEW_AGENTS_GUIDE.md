# Quick Guide: Adding New Autonomous Agents

## 🚀 Quick Start (3 Steps)

### Step 1: Create Your Agent File

```bash
cd autonomous_agents/
cp example_new_agent.py.template sales_analytics.py
```

Edit `sales_analytics.py`:

```python
from datetime import datetime
from celery_app import celery_app
from autonomous_agents.base import run_autonomous_agent, logger


@celery_app.task(name='autonomous_agents.daily_sales_report')
def daily_sales_report():
    """Runs daily at 6:00 PM - Sales summary"""
    logger.info("📊 Starting Daily Sales Report...")

    prompt = """Generate daily sales report:
    1. Total sales today
    2. Top selling products
    3. Sales vs target"""

    try:
        run_autonomous_agent(
            agent_type='sales_analytics',
            prompt=prompt,
            run_type='scheduled',
            trigger='cron:daily_6pm',
            report_type='daily_sales',
            report_title=f"Sales Report - {datetime.now().strftime('%B %d, %Y')}"
        )
    except Exception as e:
        logger.error(f"❌ Sales Report failed: {str(e)}")
        raise
```

### Step 2: Register Your Agent

Edit `autonomous_agents/__init__.py`:

```python
# Add this line after other imports
from autonomous_agents import sales_analytics

# Add to modules list in get_agent_info()
'modules': [
    'inventory_intelligence',
    'sales_analytics',  # Add this
]
```

### Step 3: Add Schedule & Restart

**Option A: Use Flask Admin UI**
1. Go to http://localhost:5000/admin/schedules
2. Click "Create Schedule"
3. Fill in:
   - Task Name: `autonomous_agents.daily_sales_report`
   - Schedule Type: `cron`
   - Cron Expression: `0 18 * * *` (6 PM daily)
   - Enabled: ✅

**Option B: Add to Database Directly**

```python
from database import create_schedule

create_schedule(
    task_name='autonomous_agents.daily_sales_report',
    schedule_type='cron',
    cron_expression='0 18 * * *',
    enabled=True,
    description='Daily sales report at 6 PM'
)
```

**Restart Celery:**

```bash
pkill -f "celery worker"
pkill -f "celery beat"
./start_celery_worker.sh
./start_celery_beat.sh
```

Done! ✅

---

## 📋 Complete Example: Customer Support Agent

### 1. Create File: `autonomous_agents/customer_support.py`

```python
"""
Customer Support Agent - Automated Ticket Monitoring
Monitors support tickets and generates alerts
"""

from datetime import datetime
from celery_app import celery_app
from autonomous_agents.base import run_autonomous_agent, logger


@celery_app.task(name='autonomous_agents.urgent_tickets_check')
def urgent_tickets_check():
    """Every 30 minutes - Check for urgent tickets"""
    logger.info("🎫 Checking urgent tickets...")

    prompt = """Check support system for:
    1. Tickets marked URGENT with no response >1 hour
    2. High-priority customers waiting >2 hours
    3. Escalation needed situations

    List ticket IDs and brief description."""

    try:
        run_autonomous_agent(
            agent_type='customer_support',
            prompt=prompt,
            run_type='scheduled',
            trigger='interval:30_minutes',
            report_type='urgent_check',
            report_title=f"Urgent Tickets - {datetime.now().strftime('%I:%M %p')}"
        )
    except Exception as e:
        logger.error(f"❌ Urgent tickets check failed: {str(e)}")
        raise


@celery_app.task(name='autonomous_agents.customer_satisfaction_daily')
def customer_satisfaction_daily():
    """Daily at 7 PM - Customer satisfaction summary"""
    logger.info("😊 Generating customer satisfaction report...")

    prompt = """Analyze today's customer interactions:
    1. CSAT scores and feedback
    2. Common complaints or issues
    3. Positive feedback highlights
    4. Recommendations for improvement"""

    try:
        run_autonomous_agent(
            agent_type='customer_support',
            prompt=prompt,
            run_type='scheduled',
            trigger='cron:daily_7pm',
            report_type='satisfaction',
            report_title=f"Customer Satisfaction - {datetime.now().strftime('%B %d, %Y')}"
        )
    except Exception as e:
        logger.error(f"❌ Customer satisfaction report failed: {str(e)}")
        raise
```

### 2. Register in `__init__.py`

```python
from autonomous_agents import customer_support

'modules': [
    'inventory_intelligence',
    'customer_support',
]
```

### 3. Add Two Schedules

**Schedule 1:** Urgent tickets check (every 30 min)
```
Task: autonomous_agents.urgent_tickets_check
Type: interval
Interval: 1800 (seconds = 30 minutes)
```

**Schedule 2:** Daily satisfaction report (7 PM)
```
Task: autonomous_agents.customer_satisfaction_daily
Type: cron
Cron: 0 19 * * *
```

### 4. Test Before Deploying

```python
from autonomous_agents import trigger_task_now

# Test urgent check
result = trigger_task_now('urgent_tickets_check')
print(f"Task ID: {result.id}")

# Check status after a few seconds
from autonomous_agents import get_task_status
status = get_task_status(result.id)
print(status)
```

---

## 🎯 Common Schedule Patterns

### Daily Schedules
```python
# Morning report (7 AM)
trigger='cron:daily_7am'
cron='0 7 * * *'

# End of day (6 PM)
trigger='cron:daily_6pm'
cron='0 18 * * *'

# Midnight
trigger='cron:daily_midnight'
cron='0 0 * * *'
```

### Weekly Schedules
```python
# Monday morning (8 AM)
trigger='cron:monday_8am'
cron='0 8 * * 1'

# Friday afternoon (5 PM)
trigger='cron:friday_5pm'
cron='0 17 * * 5'
```

### Interval Schedules
```python
# Every hour
trigger='interval:1_hour'
interval=3600

# Every 6 hours
trigger='interval:6_hours'
interval=21600

# Every 30 minutes
trigger='interval:30_minutes'
interval=1800
```

---

## ✅ Testing Checklist

Before deploying a new agent:

- [ ] Agent file created in `autonomous_agents/`
- [ ] Tasks use `@celery_app.task` decorator
- [ ] Task names start with `autonomous_agents.`
- [ ] Imported in `__init__.py`
- [ ] Schedule added to database
- [ ] Tested with `trigger_task_now()`
- [ ] Verified output looks correct
- [ ] Error handling works (try invalid prompt)
- [ ] Celery worker and beat restarted
- [ ] Monitoring logs for first few runs

---

## 🐛 Troubleshooting

### Task not showing up?
```python
from autonomous_agents import get_agent_info
info = get_agent_info()
print(info['registered_tasks'])
# Should see your new task
```

### Task won't run?
1. Check schedule is enabled in database
2. Check Celery beat is running: `ps aux | grep celery`
3. Check logs: `tail -f celery_worker.log`

### Import errors?
```bash
# Test import manually
python3 -c "from autonomous_agents import your_module"
```

### Schedule not triggering?
```python
from schedule_loader import get_schedule_summary
summary = get_schedule_summary()
print(summary)  # Should show your schedule
```

---

## 📚 Reference Files

- **Template:** `autonomous_agents/example_new_agent.py.template`
- **Example:** `autonomous_agents/inventory_intelligence.py`
- **Docs:** `autonomous_agents/README.md`
- **Summary:** `AGENT_REFACTORING_SUMMARY.md`
