"""
Schedule Loader - Dynamic Schedule Configuration
Loads agent schedules from database for Celery Beat
"""

from celery.schedules import crontab, schedule
from typing import Dict, Any
from src.core.database import get_all_schedules
import logging

logger = logging.getLogger(__name__)

def load_schedules_from_db() -> Dict[str, Dict[str, Any]]:
    """
    Load all enabled schedules from database and convert to Celery beat_schedule format

    Returns:
        Dict: Celery beat_schedule dictionary with task configurations

    Example output:
        {
            'morning_intelligence_report': {
                'task': 'autonomous_agents.morning_intelligence_report',
                'schedule': crontab(hour=7, minute=0),
                'options': {'queue': 'agent_tasks'}
            },
            ...
        }
    """
    try:
        # Get all schedules from database
        schedules_data = get_all_schedules()

        if not schedules_data:
            logger.warning("No schedules found in database. Using empty schedule.")
            return {}

        # Convert to Celery beat_schedule format
        beat_schedule = {}

        for sched in schedules_data:
            # Skip disabled schedules
            if not sched.get('enabled', True):
                logger.info(f"Skipping disabled schedule: {sched['task_name']}")
                continue

            task_name = sched['task_name']
            schedule_type = sched['schedule_type']

            # Create schedule object based on type
            if schedule_type == 'cron':
                # Cron schedule (specific times)
                day_of_week = sched.get('day_of_week')
                if day_of_week is None or day_of_week == '*':
                    day_of_week = '*'  # Every day

                schedule_obj = crontab(
                    hour=sched.get('hour', 0),
                    minute=sched.get('minute', 0),
                    day_of_week=day_of_week
                )
            elif schedule_type == 'interval':
                # Interval schedule (every X seconds)
                interval_seconds = sched.get('interval_seconds', 3600)
                schedule_obj = schedule(run_every=interval_seconds)
            else:
                logger.error(f"Unknown schedule_type '{schedule_type}' for task {task_name}")
                continue

            # Build the beat schedule entry
            beat_schedule[task_name] = {
                'task': f'autonomous_agents.{task_name}',
                'schedule': schedule_obj,
                'options': {'queue': 'agent_tasks'}
            }

            logger.info(f"Loaded schedule: {task_name} ({schedule_type})")

        logger.info(f"Successfully loaded {len(beat_schedule)} schedules from database")
        return beat_schedule

    except Exception as e:
        logger.error(f"Error loading schedules from database: {e}")
        # Return empty schedule on error - prevents Celery Beat from crashing
        return {}


def initialize_default_schedules():
    """
    Initialize default schedules in database if they don't exist
    Should be called on app startup
    """
    from src.core.database import init_default_schedules

    try:
        logger.info("Initializing default schedules in database...")
        init_default_schedules()
        logger.info("Default schedules initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing default schedules: {e}")


def get_schedule_summary() -> Dict[str, Any]:
    """
    Get a summary of all loaded schedules for debugging/monitoring

    Returns:
        Dict: Summary with schedule count and details
    """
    try:
        schedules = get_all_schedules()

        enabled_count = sum(1 for s in schedules if s.get('enabled', True))
        disabled_count = len(schedules) - enabled_count

        summary = {
            'total_schedules': len(schedules),
            'enabled': enabled_count,
            'disabled': disabled_count,
            'schedules': []
        }

        for sched in schedules:
            schedule_info = {
                'task_name': sched['task_name'],
                'display_name': sched['display_name'],
                'enabled': bool(sched.get('enabled', True)),
                'schedule_type': sched['schedule_type']
            }

            if sched['schedule_type'] == 'cron':
                schedule_info['schedule'] = f"Cron: {sched['hour']}:{sched['minute']:02d}"
                if sched.get('day_of_week') and sched['day_of_week'] != '*':
                    schedule_info['schedule'] += f" on day {sched['day_of_week']}"
            else:
                hours = sched['interval_seconds'] / 3600
                schedule_info['schedule'] = f"Every {hours:.1f} hours"

            summary['schedules'].append(schedule_info)

        return summary

    except Exception as e:
        logger.error(f"Error getting schedule summary: {e}")
        return {'error': str(e)}


# For testing/debugging
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Schedule Loader Test ===\n")

    # Initialize defaults
    print("1. Initializing default schedules...")
    initialize_default_schedules()

    # Load schedules
    print("\n2. Loading schedules from database...")
    beat_schedule = load_schedules_from_db()

    print(f"\n3. Loaded {len(beat_schedule)} schedules:")
    for task_name, config in beat_schedule.items():
        print(f"   - {task_name}: {config['schedule']}")

    # Get summary
    print("\n4. Schedule summary:")
    summary = get_schedule_summary()
    print(f"   Total: {summary['total_schedules']}")
    print(f"   Enabled: {summary['enabled']}")
    print(f"   Disabled: {summary['disabled']}")

    print("\n=== Test Complete ===")
