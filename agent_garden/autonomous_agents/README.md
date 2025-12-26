# Autonomous Agents Directory

This directory contains all autonomous agent tasks that run on schedules or triggers using Celery.

## 📁 Structure

```
autonomous_agents/
├── __init__.py                    # Auto-discovery & utility exports
├── base.py                        # Shared utilities and helper functions
├── inventory_intelligence.py      # Inventory monitoring tasks
└── README.md                      # This file
```

## 🚀 Adding a New Agent

To add a new autonomous agent (e.g., Sales Analytics):

### 1. Create a new file

Create `sales_analytics.py` in this directory:

```python
"""
Sales Analytics Agent - Scheduled Tasks
Automated sales monitoring and reporting
"""

from datetime import datetime
from celery_app import celery_app
from autonomous_agents.base import run_autonomous_agent, logger


@celery_app.task(name='autonomous_agents.daily_sales_report')
def daily_sales_report():
    """
    Runs daily at 6:00 PM
    Generates daily sales summary
    """
    logger.info("📊 Starting Daily Sales Report...")

    prompt = """Generate a daily sales report with:
    1. Total sales today
    2. Best selling products
    3. Sales trends
    """

    try:
        run_autonomous_agent(
            agent_type='sales_analytics',
            prompt=prompt,
            run_type='scheduled',
            trigger='cron:daily_6pm',
            report_type='daily_sales',
            report_title=f"Daily Sales - {datetime.now().strftime('%B %d, %Y')}"
        )
    except Exception as e:
        logger.error(f"❌ Daily Sales Report failed: {str(e)}")
        raise
```

### 2. Import the new module

Edit `__init__.py` and add your import:

```python
from autonomous_agents import inventory_intelligence
from autonomous_agents import sales_analytics  # Add this line
```

Update the `get_agent_info()` modules list:

```python
'modules': [
    'inventory_intelligence',
    'sales_analytics',  # Add this line
]
```

### 3. Add schedule to database

Use the Flask admin UI or database tools to add a schedule entry for your new task.

### 4. Restart Celery

```bash
# Stop current workers
pkill -f "celery worker"
pkill -f "celery beat"

# Start again
./start_celery_worker.sh
./start_celery_beat.sh
```

That's it! Celery will auto-discover your new tasks.

## 🔧 Utility Functions

### `run_autonomous_agent()`

Generic function to run any agent with full lifecycle management (database logging, error handling):

```python
from autonomous_agents.base import run_autonomous_agent

report = run_autonomous_agent(
    agent_type='my_agent',
    prompt='Do something',
    run_type='manual',
    trigger='manual:user',
    report_type='custom',
    report_title='My Report'
)
```

### `trigger_task_now()`

Manually trigger a scheduled task immediately:

```python
from autonomous_agents import trigger_task_now

result = trigger_task_now('morning_intelligence_report')
```

### `get_task_status()`

Check status of a running task:

```python
from autonomous_agents import get_task_status

status = get_task_status(task_id)
print(status['state'])  # PENDING, STARTED, SUCCESS, FAILURE
```

## 📋 Best Practices

1. **One agent type per file** - Keep related tasks together
2. **Use descriptive task names** - Start with `autonomous_agents.`
3. **Always use base utilities** - Don't duplicate database/logging code
4. **Handle exceptions** - Wrap execution in try/except
5. **Log appropriately** - Use logger from base module
6. **Add docstrings** - Explain what each task does and when it runs

## 🧪 Testing

Test a task manually without Celery:

```python
from autonomous_agents import run_agent_now

report = run_agent_now('inventory_intelligence', 'Your prompt here')
print(report)
```

## 📊 Monitoring

View registered tasks:

```python
from autonomous_agents import get_agent_info

info = get_agent_info()
print(f"Total agents: {info['total_agents']}")
print(f"Tasks: {info['registered_tasks']}")
```

## 🔄 Migration Notes

The original `autonomous_agents.py` has been refactored into this package structure for better scalability and maintainability. A backup exists at `autonomous_agents.py.backup`.
