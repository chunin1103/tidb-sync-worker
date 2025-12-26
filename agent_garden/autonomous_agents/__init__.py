"""
Autonomous Agents Package
Auto-discovers and registers all agent tasks with Celery

To add a new agent:
1. Create a new file in this directory (e.g., sales_analytics.py)
2. Import celery_app from celery_app
3. Define tasks with @celery_app.task decorator
4. Restart Celery worker and beat - tasks will auto-discover
"""

from datetime import datetime
import logging
from typing import Optional

# Import base utilities (no celery_app dependency)
from autonomous_agents.base import run_autonomous_agent, create_session_id, logger

# Import all agent modules to register their tasks
# Add new agent imports here as you create them
from autonomous_agents import inventory_intelligence

# Import celery_app after agent modules to avoid circular import
from src.scheduling.celery_app import celery_app

# Re-export commonly used utilities for convenience
__all__ = [
    'run_autonomous_agent',
    'create_session_id',
    'logger',
    'trigger_task_now',
    'get_task_status',
    'run_agent_now'
]


# ============================================================================
# CELERY TASK MANAGEMENT
# ============================================================================

def trigger_task_now(task_name: str):
    """
    Manually trigger a Celery task immediately

    Args:
        task_name: Name of the task (e.g., 'morning_intelligence_report')

    Returns:
        Celery AsyncResult object or None if task not found
    """
    # Map of task short names to full task names
    task_map = {
        'morning_intelligence_report': 'autonomous_agents.morning_intelligence_report',
        'inventory_health_check': 'autonomous_agents.inventory_health_check',
        'weekly_summary_report': 'autonomous_agents.weekly_summary_report'
    }

    # Support both short names and full task names
    full_task_name = task_map.get(task_name, task_name)

    try:
        logger.info(f"🚀 Manually triggering task: {full_task_name}")
        return celery_app.send_task(full_task_name)
    except Exception as e:
        logger.error(f"❌ Failed to trigger task {full_task_name}: {str(e)}")
        return None


def get_task_status(task_id: str):
    """
    Check the status of a Celery task

    Args:
        task_id: Celery task ID

    Returns:
        Dictionary with task status information
    """
    from celery.result import AsyncResult
    result = AsyncResult(task_id, app=celery_app)

    return {
        'task_id': task_id,
        'state': result.state,
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None,
        'result': result.result if result.ready() else None
    }


def run_agent_now(agent_type: str, prompt: str) -> str:
    """
    Manually trigger an agent run (non-Celery, synchronous)
    Useful for testing or on-demand reports

    Args:
        agent_type: Type of agent to run (e.g., 'inventory_intelligence')
        prompt: The prompt to send to the agent

    Returns:
        The full report content

    Raises:
        Exception if agent execution fails
    """
    logger.info(f"▶️  Manual agent run: {agent_type}")

    return run_autonomous_agent(
        agent_type=agent_type,
        prompt=prompt,
        run_type='manual',
        trigger='manual:user_triggered',
        report_type='manual',
        report_title=f"Manual Report - {datetime.now().strftime('%I:%M %p')}"
    )


# ============================================================================
# AVAILABLE AGENTS REGISTRY (for introspection)
# ============================================================================

def get_registered_tasks():
    """
    Get a list of all registered autonomous agent tasks

    Returns:
        List of task names
    """
    # Get all tasks that start with 'autonomous_agents.'
    return [
        task_name for task_name in celery_app.tasks.keys()
        if task_name.startswith('autonomous_agents.')
    ]


def get_agent_info():
    """
    Get information about all registered agents

    Returns:
        Dictionary with agent information
    """
    tasks = get_registered_tasks()

    return {
        'total_agents': len(tasks),
        'registered_tasks': tasks,
        'modules': [
            'inventory_intelligence',
            # Add new agent modules here as they're created
        ]
    }
