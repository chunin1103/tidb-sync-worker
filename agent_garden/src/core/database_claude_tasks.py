"""
Claude Task Database Operations
Helper functions for managing Claude task queue
"""

import json
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session


def create_claude_task(db: Session, task_type: str, task_json: dict, schedule_cron: str = None, created_by: str = 'gemini', output_format: str = 'md') -> Optional[int]:
    """
    Create a new Claude task

    Args:
        db: Database session
        task_type: Type of task ('report', 'query', 'calculation', etc.)
        task_json: Full task details as dictionary
        schedule_cron: Optional cron schedule (e.g., "0 7 * * *")
        created_by: Who created the task
        output_format: Output format ('md', 'csv', 'xlsx', 'json', 'multi')

    Returns:
        Task ID if successful, None otherwise
    """
    from .database import ClaudeTask

    try:
        # Determine initial status
        status = 'ready' if not schedule_cron else 'pending'

        task = ClaudeTask(
            task_type=task_type,
            task_json=json.dumps(task_json),
            schedule_cron=schedule_cron,
            output_format=output_format,
            status=status,
            created_by=created_by
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return task.id

    except Exception as e:
        db.rollback()
        print(f"Error creating Claude task: {e}")
        return None


def get_ready_tasks(db: Session) -> List[Dict]:
    """
    Get all tasks with status='ready' for Claude to execute

    Args:
        db: Database session

    Returns:
        List of task dictionaries
    """
    from .database import ClaudeTask

    try:
        tasks = db.query(ClaudeTask).filter(ClaudeTask.status == 'ready').order_by(ClaudeTask.created_at).all()

        return [{
            'id': task.id,
            'task_type': task.task_type,
            'task_json': json.loads(task.task_json),
            'output_format': task.output_format or 'md',
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'created_by': task.created_by
        } for task in tasks]

    except Exception as e:
        print(f"Error getting ready tasks: {e}")
        return []


def start_claude_task(db: Session, task_id: int) -> bool:
    """
    Mark a task as in_progress when Claude starts executing

    Args:
        db: Database session
        task_id: ID of the task

    Returns:
        True if successful, False otherwise
    """
    from .database import ClaudeTask

    try:
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if task:
            task.status = 'in_progress'
            task.started_at = datetime.utcnow()
            db.commit()
            return True
        return False

    except Exception as e:
        db.rollback()
        print(f"Error starting Claude task {task_id}: {e}")
        return False


def complete_claude_task(db: Session, task_id: int, result_path: str = None, result_summary: str = None, tool_usage: str = None) -> bool:
    """
    Mark a task as completed

    Args:
        db: Database session
        task_id: ID of the task
        result_path: Path to result file in OneDrive
        result_summary: Brief summary of the result
        tool_usage: JSON string of tools used (e.g., '["Write", "Bash"]')

    Returns:
        True if successful, False otherwise
    """
    from .database import ClaudeTask, TaskExecutionHistory

    try:
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if not task:
            return False

        # Check if recurring
        is_recurring = task.schedule_cron is not None

        # Save to execution history
        history = TaskExecutionHistory(
            task_id=task_id,
            started_at=task.started_at or datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status='completed',
            result_path=result_path,
            execution_time_seconds=int((datetime.utcnow() - (task.started_at or datetime.utcnow())).total_seconds())
        )
        db.add(history)

        # Update task
        if is_recurring:
            # Reset to pending for next run
            task.status = 'pending'
        else:
            # One-time task - mark as completed
            task.status = 'completed'
            task.completed_at = datetime.utcnow()

        task.result_path = result_path
        task.result_summary = result_summary
        task.tool_usage = tool_usage
        task.execution_count += 1
        task.last_execution_at = datetime.utcnow()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error completing Claude task {task_id}: {e}")
        return False


def fail_claude_task(db: Session, task_id: int, error_log: str) -> bool:
    """
    Mark a task as failed

    Args:
        db: Database session
        task_id: ID of the task
        error_log: Error message/traceback

    Returns:
        True if successful, False otherwise
    """
    from .database import ClaudeTask, TaskExecutionHistory

    try:
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if not task:
            return False

        # Save to execution history
        history = TaskExecutionHistory(
            task_id=task_id,
            started_at=task.started_at or datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status='failed',
            error_log=error_log,
            execution_time_seconds=int((datetime.utcnow() - (task.started_at or datetime.utcnow())).total_seconds())
        )
        db.add(history)

        # Update task
        task.status = 'failed'
        task.error_log = error_log
        task.last_execution_at = datetime.utcnow()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error failing Claude task {task_id}: {e}")
        return False


def mark_task_ready(db: Session, task_id: int) -> bool:
    """
    Mark a task as ready for execution (called by Celery at scheduled time)

    Args:
        db: Database session
        task_id: ID of the task

    Returns:
        True if successful, False otherwise
    """
    from .database import ClaudeTask

    try:
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if task and task.status == 'pending':
            task.status = 'ready'
            db.commit()
            return True
        return False

    except Exception as e:
        db.rollback()
        print(f"Error marking task {task_id} as ready: {e}")
        return False


def get_claude_task(db: Session, task_id: int) -> Optional[Dict]:
    """
    Get details of a specific Claude task

    Args:
        db: Database session
        task_id: ID of the task

    Returns:
        Task dictionary or None
    """
    from .database import ClaudeTask

    try:
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if not task:
            return None

        return {
            'id': task.id,
            'task_type': task.task_type,
            'task_json': json.loads(task.task_json),
            'output_format': task.output_format or 'md',
            'schedule_cron': task.schedule_cron,
            'schedule_enabled': bool(task.schedule_enabled),
            'status': task.status,
            'result_path': task.result_path,
            'result_summary': task.result_summary,
            'tool_usage': json.loads(task.tool_usage) if task.tool_usage else None,
            'error_log': task.error_log,
            'created_by': task.created_by,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'execution_count': task.execution_count,
            'last_execution_at': task.last_execution_at.isoformat() if task.last_execution_at else None
        }

    except Exception as e:
        print(f"Error getting Claude task {task_id}: {e}")
        return None


def get_all_claude_tasks(db: Session, status: str = None, task_type: str = None, limit: int = 100) -> List[Dict]:
    """
    Get list of Claude tasks with optional filtering

    Args:
        db: Database session
        status: Filter by status (optional)
        task_type: Filter by task type (optional)
        limit: Maximum number of tasks to return

    Returns:
        List of task dictionaries
    """
    from .database import ClaudeTask

    try:
        query = db.query(ClaudeTask)

        if status:
            query = query.filter(ClaudeTask.status == status)

        if task_type:
            query = query.filter(ClaudeTask.task_type == task_type)

        tasks = query.order_by(ClaudeTask.created_at.desc()).limit(limit).all()

        return [{
            'id': task.id,
            'task_type': task.task_type,
            'task_json': json.loads(task.task_json),
            'output_format': task.output_format or 'md',
            'schedule_cron': task.schedule_cron,
            'status': task.status,
            'result_summary': task.result_summary,
            'tool_usage': json.loads(task.tool_usage) if task.tool_usage else None,
            'created_by': task.created_by,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'execution_count': task.execution_count,
            'last_execution_at': task.last_execution_at.isoformat() if task.last_execution_at else None
        } for task in tasks]

    except Exception as e:
        print(f"Error getting Claude tasks: {e}")
        return []


def get_task_execution_history(db: Session, task_id: int, limit: int = 10) -> List[Dict]:
    """
    Get execution history for a task

    Args:
        db: Database session
        task_id: ID of the task
        limit: Maximum number of history entries to return

    Returns:
        List of execution history dictionaries
    """
    from .database import TaskExecutionHistory

    try:
        history = (
            db.query(TaskExecutionHistory)
            .filter(TaskExecutionHistory.task_id == task_id)
            .order_by(TaskExecutionHistory.started_at.desc())
            .limit(limit)
            .all()
        )

        return [{
            'id': h.id,
            'task_id': h.task_id,
            'started_at': h.started_at.isoformat() if h.started_at else None,
            'completed_at': h.completed_at.isoformat() if h.completed_at else None,
            'status': h.status,
            'result_path': h.result_path,
            'error_log': h.error_log,
            'execution_time_seconds': h.execution_time_seconds
        } for h in history]

    except Exception as e:
        print(f"Error getting task execution history: {e}")
        return []


def delete_task(db: Session, task_id: int) -> bool:
    """
    Delete a Claude task and its execution history

    Args:
        db: Database session
        task_id: ID of the task to delete

    Returns:
        True if successful, False otherwise
    """
    from .database import ClaudeTask, TaskExecutionHistory

    try:
        # Delete execution history first
        db.query(TaskExecutionHistory).filter(TaskExecutionHistory.task_id == task_id).delete()

        # Delete task
        task = db.query(ClaudeTask).filter(ClaudeTask.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False

    except Exception as e:
        db.rollback()
        print(f"Error deleting task {task_id}: {e}")
        return False
