"""
Claude task utilities
Helper functions for task management

Note: Celery scheduling has been replaced with database polling.
The Claude executor polls /AgentGarden/tasks/ready for tasks.
"""

from src.core.database import get_db
from src.core.database_claude_tasks import mark_task_ready
import logging

logger = logging.getLogger(__name__)


def trigger_claude_task(task_id):
    """
    Mark a task as ready for Claude to execute

    This can be called directly or via API endpoint.
    The Claude executor polls for ready tasks every 30 seconds.

    Args:
        task_id: ID of the task in claude_tasks table

    Returns:
        Dictionary with success status and task_id
    """
    try:
        db = get_db()
        if not db:
            logger.error(f"Database not available for task {task_id}")
            return {'success': False, 'error': 'Database not available'}

        # Update task status to 'ready'
        success = mark_task_ready(db, task_id)
        db.close()

        if success:
            logger.info(f"✅ Task {task_id} marked ready for Claude execution")
            return {'success': True, 'task_id': task_id}
        else:
            logger.warning(f"⚠️ Task {task_id} not found or not in pending status")
            return {'success': False, 'error': 'Task not found or not pending'}

    except Exception as e:
        logger.error(f"❌ Error triggering task {task_id}: {e}")
        return {'success': False, 'error': str(e)}


def cleanup_old_claude_tasks():
    """
    Cleanup completed tasks older than 30 days
    Can be triggered manually or via scheduled task

    Returns:
        Dictionary with number of deleted tasks
    """
    try:
        db = get_db()
        if not db:
            logger.error("Database not available for cleanup")
            return {'success': False, 'error': 'Database not available'}

        from datetime import datetime, timedelta

        # Delete completed one-time tasks older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Use raw SQL for simplicity
        result = db.execute(
            """
            DELETE FROM claude_tasks
            WHERE status = 'completed'
            AND completed_at < :cutoff
            AND schedule_cron IS NULL
            """,
            {'cutoff': cutoff_date}
        )
        deleted = result.rowcount
        db.commit()
        db.close()

        logger.info(f"🧹 Cleaned up {deleted} old completed tasks")
        return {'success': True, 'deleted': deleted}

    except Exception as e:
        logger.error(f"❌ Error cleaning up tasks: {e}")
        if db:
            db.rollback()
            db.close()
        return {'success': False, 'error': str(e)}
