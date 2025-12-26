"""
Custom Database Scheduler for Celery Beat
Reads schedules dynamically from the database without requiring restarts
"""

from celery.beat import Scheduler, ScheduleEntry
from celery.schedules import crontab, schedule as celery_schedule
from datetime import datetime
from src.scheduling.schedule_loader import load_schedules_from_db
from src.core.database import get_timezone
import logging

logger = logging.getLogger(__name__)


class DatabaseScheduler(Scheduler):
    """
    Custom scheduler that reads schedules from the database.

    Unlike PersistentScheduler which caches to a file, this scheduler
    reads fresh schedule data from the database on each tick.

    Benefits:
    - Schedule changes take effect within max_interval (default 5 minutes)
    - No need to restart Celery Beat after schedule updates
    - No stale cache files
    """

    def __init__(self, *args, **kwargs):
        # How often to check for schedule changes (in seconds)
        # Default is 30 seconds for faster updates
        self.schedule_refresh_interval = kwargs.pop('schedule_refresh_interval', 30)
        self._last_schedule_refresh = None
        self._schedule = {}

        super().__init__(*args, **kwargs)

        logger.info(f"🔄 DatabaseScheduler initialized (refresh interval: {self.schedule_refresh_interval}s)")

    def setup_schedule(self):
        """
        Called on startup to load initial schedules
        """
        logger.info("📅 Loading initial schedules from database...")
        self._refresh_schedule()

    def _refresh_schedule(self):
        """
        Reload schedules from database
        """
        try:
            # Load schedules from database
            beat_schedule = load_schedules_from_db()

            # Convert to ScheduleEntry objects
            self._schedule = {}
            for name, entry in beat_schedule.items():
                self._schedule[name] = self.Entry(
                    name=name,
                    task=entry['task'],
                    schedule=entry['schedule'],
                    options=entry.get('options', {}),
                    app=self.app
                )

            self._last_schedule_refresh = datetime.now()

            logger.info(f"✅ Loaded {len(self._schedule)} schedules from database")

        except Exception as e:
            logger.error(f"❌ Error refreshing schedules from database: {e}")
            # Keep existing schedule if refresh fails

    def _should_refresh_schedule(self):
        """
        Check if we should refresh the schedule from the database
        """
        if self._last_schedule_refresh is None:
            return True

        elapsed = (datetime.now() - self._last_schedule_refresh).total_seconds()
        return elapsed >= self.schedule_refresh_interval

    @property
    def schedule(self):
        """
        Return current schedule, refreshing from database if needed
        """
        if self._should_refresh_schedule():
            logger.info("🔄 Refreshing schedules from database...")
            self._refresh_schedule()

        return self._schedule

    def sync(self):
        """
        Called periodically by Celery Beat
        We don't need to persist to disk since we read from database
        """
        # Check if we should refresh
        if self._should_refresh_schedule():
            self._refresh_schedule()

    def close(self):
        """
        Called when scheduler is shutting down
        """
        logger.info("🛑 DatabaseScheduler shutting down")
        super().close()

    # The Entry class from Scheduler is used as-is
    # It handles individual schedule entries
    class Entry(ScheduleEntry):
        """Schedule entry for database-backed scheduler"""

        def __init__(self, name, task, schedule, options, app):
            self.name = name
            self.task = task
            self.schedule = schedule
            self.options = options
            self.app = app

            # Track when this entry was last run
            self.last_run_at = self.default_now()

        def is_due(self):
            """
            Check if this task is due to run
            Returns: (is_due, next_time_to_run)
            """
            return self.schedule.is_due(self.last_run_at)

        def __next__(self):
            """Update last_run_at and return next instance"""
            self.last_run_at = self.default_now()
            return self.__class__(**self._default_kwargs)

        next = __next__  # for Python 2/3 compatibility

        @property
        def _default_kwargs(self):
            return {
                'name': self.name,
                'task': self.task,
                'schedule': self.schedule,
                'options': self.options,
                'app': self.app
            }

        def __repr__(self):
            return f'<{self.name}: {self.schedule}>'
