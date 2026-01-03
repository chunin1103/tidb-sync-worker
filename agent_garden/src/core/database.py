"""
Database models and session management for Agent Garden
Using Neon PostgreSQL for persistent chat history
"""

import os
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
USE_DATABASE = DATABASE_URL is not None

# SQLAlchemy setup
Base = declarative_base()
engine = None
SessionLocal = None

if USE_DATABASE:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# DATABASE MODELS
# ============================================================================

class ChatSession(Base):
    """Stores chat session metadata"""
    __tablename__ = "chat_sessions"

    session_id = Column(String(100), primary_key=True, index=True)
    agent_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """Stores individual messages in chat sessions"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'model'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentRun(Base):
    """Stores autonomous agent execution history"""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False)
    run_type = Column(String(20), nullable=False)  # 'scheduled', 'triggered', 'manual'
    trigger = Column(String(100))  # e.g., 'cron:daily_7am', 'event:zero_inventory'
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default='running')  # 'running', 'completed', 'failed'
    output_summary = Column(Text)
    error_message = Column(Text)


class AgentReport(Base):
    """Stores agent-generated reports"""
    __tablename__ = "agent_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_run_id = Column(Integer, index=True)
    agent_type = Column(String(50), nullable=False)
    report_type = Column(String(50))  # 'morning_intelligence', 'weekly_summary', etc.
    title = Column(String(200))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)


class ScheduleConfig(Base):
    """Stores customizable schedules for autonomous agents"""
    __tablename__ = "schedule_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # 'cron' or 'interval'

    # For cron schedules
    hour = Column(Integer)  # 0-23
    minute = Column(Integer)  # 0-59
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday, None=Every day

    # For interval schedules
    interval_seconds = Column(Integer)

    # Metadata
    enabled = Column(Integer, default=1)  # SQLite doesn't have boolean, use 1/0
    description = Column(Text)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemSettings(Base):
    """Stores system-wide settings (single row table)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)  # Always 1, single row
    timezone = Column(String(100), default='America/Los_Angeles', nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClaudeTask(Base):
    """Stores tasks for Claude to execute (created by Gemini)"""
    __tablename__ = "claude_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)  # 'report', 'query', 'calculation', etc.
    task_json = Column(Text, nullable=False)  # Full task details as JSON string
    schedule_cron = Column(String(100))  # Cron expression for scheduled tasks
    schedule_enabled = Column(Integer, default=1)  # 1=enabled, 0=disabled
    output_format = Column(String(10), default='md')  # 'md', 'csv', 'xlsx', 'json', 'multi'
    status = Column(String(20), default='pending')  # 'pending', 'ready', 'in_progress', 'completed', 'failed'
    result_path = Column(String(500))  # Path to result file in OneDrive
    result_summary = Column(Text)  # Brief summary of the result
    error_log = Column(Text)  # Error message/traceback if failed
    created_by = Column(String(50), default='gemini')  # Who created the task
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)  # When Claude started executing
    completed_at = Column(DateTime)  # When task finished (one-time tasks only)
    execution_count = Column(Integer, default=0)  # Number of times executed
    last_execution_at = Column(DateTime)  # Last execution time (recurring tasks)


class TaskExecutionHistory(Base):
    """Stores execution history for Claude tasks"""
    __tablename__ = "task_execution_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, index=True, nullable=False)  # FK to claude_tasks.id
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # 'completed' or 'failed'
    result_path = Column(String(500))  # Path to result file
    error_log = Column(Text)  # Error message if failed
    execution_time_seconds = Column(Integer)  # How long it took


class ClaudeReport(Base):
    """Stores Claude-generated reports (synced from local OneDrive)"""
    __tablename__ = "claude_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, index=True)  # FK to claude_tasks.id (nullable)
    agent_type = Column(String(50), nullable=False, index=True)  # 'inventory_intelligence', etc.
    report_title = Column(String(200), nullable=False)  # Filename without extension
    report_content = Column(Text, nullable=False)  # Full markdown content
    file_path = Column(String(500))  # Relative path in OneDrive (for reference)
    file_size = Column(Integer)  # File size in bytes
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def init_db():
    """Initialize database tables"""
    if USE_DATABASE and engine:
        Base.metadata.create_all(bind=engine)


def get_db() -> Optional[Session]:
    """Get database session"""
    if USE_DATABASE and SessionLocal:
        return SessionLocal()
    return None


def save_message(session_id: str, agent_type: str, role: str, content: str) -> bool:
    """
    Save a message to the database

    Args:
        session_id: Unique session identifier
        agent_type: Type of agent (e.g., 'inventory_intelligence')
        role: Message role ('user' or 'model')
        content: Message content

    Returns:
        True if saved successfully, False otherwise
    """
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        # Create or update session
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            session = ChatSession(session_id=session_id, agent_type=agent_type)
            db.add(session)
        else:
            session.updated_at = datetime.utcnow()

        # Save message
        message = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(message)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error saving message: {e}")
        return False
    finally:
        db.close()


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """
    Get conversation history for a session

    Args:
        session_id: Unique session identifier

    Returns:
        List of messages in format [{"role": "user", "content": "..."}]
    """
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        return [{"role": msg.role, "content": msg.content} for msg in messages]

    except Exception as e:
        print(f"Error getting session history: {e}")
        return []
    finally:
        db.close()


def clear_session_history(session_id: str) -> bool:
    """
    Clear all messages for a session

    Args:
        session_id: Session to clear

    Returns:
        True if cleared successfully, False otherwise
    """
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        # Delete messages
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()

        # Delete session
        db.query(ChatSession).filter(ChatSession.session_id == session_id).delete()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error clearing session: {e}")
        return False
    finally:
        db.close()


def get_all_sessions() -> List[str]:
    """
    Get list of all active session IDs

    Returns:
        List of session IDs
    """
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        sessions = db.query(ChatSession.session_id).all()
        return [s[0] for s in sessions]

    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []
    finally:
        db.close()


def get_sessions_with_metadata() -> List[Dict]:
    """
    Get all sessions with metadata (id, agent_type, created_at, updated_at, preview)

    Returns:
        List of session dictionaries with metadata
    """
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

        result = []
        for session in sessions:
            # Get first user message as preview
            first_message = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.session_id)
                .filter(ChatMessage.role == 'user')
                .order_by(ChatMessage.created_at)
                .first()
            )

            preview = first_message.content[:60] + "..." if first_message and len(first_message.content) > 60 else (first_message.content if first_message else "New chat")

            result.append({
                'session_id': session.session_id,
                'agent_type': session.agent_type,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                'preview': preview
            })

        return result

    except Exception as e:
        print(f"Error getting sessions with metadata: {e}")
        return []
    finally:
        db.close()


def save_agent_run(agent_type: str, run_type: str, trigger: str) -> Optional[int]:
    """
    Create a new agent run record

    Returns:
        Agent run ID if successful, None otherwise
    """
    if not USE_DATABASE:
        return None

    db = get_db()
    if not db:
        return None

    try:
        agent_run = AgentRun(
            agent_type=agent_type,
            run_type=run_type,
            trigger=trigger,
            status='running'
        )
        db.add(agent_run)
        db.commit()
        run_id = agent_run.id
        return run_id

    except Exception as e:
        db.rollback()
        print(f"Error saving agent run: {e}")
        return None
    finally:
        db.close()


def complete_agent_run(run_id: int, status: str, output_summary: str = None, error_message: str = None) -> bool:
    """Complete an agent run with status and output"""
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        agent_run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if agent_run:
            agent_run.completed_at = datetime.utcnow()
            agent_run.status = status
            agent_run.output_summary = output_summary
            agent_run.error_message = error_message
            db.commit()
            return True
        return False

    except Exception as e:
        db.rollback()
        print(f"Error completing agent run: {e}")
        return False
    finally:
        db.close()


def save_agent_report(agent_run_id: int, agent_type: str, report_type: str, title: str, content: str) -> bool:
    """Save an agent-generated report"""
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        report = AgentReport(
            agent_run_id=agent_run_id,
            agent_type=agent_type,
            report_type=report_type,
            title=title,
            content=content
        )
        db.add(report)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error saving agent report: {e}")
        return False
    finally:
        db.close()


def get_recent_agent_runs(limit: int = 10) -> List[Dict]:
    """Get recent agent runs"""
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        runs = db.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit).all()

        return [{
            'id': run.id,
            'agent_type': run.agent_type,
            'run_type': run.run_type,
            'trigger': run.trigger,
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
            'status': run.status,
            'output_summary': run.output_summary
        } for run in runs]

    except Exception as e:
        print(f"Error getting agent runs: {e}")
        return []
    finally:
        db.close()


def get_agent_reports(limit: int = 10, unread_only: bool = False) -> List[Dict]:
    """Get agent reports"""
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        query = db.query(AgentReport)

        if unread_only:
            query = query.filter(AgentReport.read_at.is_(None))

        reports = query.order_by(AgentReport.created_at.desc()).limit(limit).all()

        return [{
            'id': report.id,
            'agent_run_id': report.agent_run_id,
            'agent_type': report.agent_type,
            'report_type': report.report_type,
            'title': report.title,
            'content': report.content,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'read_at': report.read_at.isoformat() if report.read_at else None,
            'is_unread': report.read_at is None
        } for report in reports]

    except Exception as e:
        print(f"Error getting agent reports: {e}")
        return []
    finally:
        db.close()


def mark_report_as_read(report_id: int) -> bool:
    """Mark a report as read"""
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        report = db.query(AgentReport).filter(AgentReport.id == report_id).first()
        if report:
            report.read_at = datetime.utcnow()
            db.commit()
            return True
        return False

    except Exception as e:
        db.rollback()
        print(f"Error marking report as read: {e}")
        return False
    finally:
        db.close()


def get_session_export_data(session_id: str) -> Optional[Dict]:
    """
    Get complete session data for export (metadata + all messages)

    Args:
        session_id: Session to export

    Returns:
        Dictionary with session metadata and messages, or None if not found
    """
    if not USE_DATABASE:
        return None

    db = get_db()
    if not db:
        return None

    try:
        # Get session metadata
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            return None

        # Get all messages
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        return {
            'session_id': session.session_id,
            'agent_type': session.agent_type,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None,
            'message_count': len(messages),
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        }

    except Exception as e:
        print(f"Error getting session export data: {e}")
        return None
    finally:
        db.close()


# ============================================================================
# CLAUDE REPORTS OPERATIONS
# ============================================================================

def save_claude_report(agent_type: str, report_title: str, report_content: str,
                       file_path: str = None, task_id: int = None) -> Optional[int]:
    """
    Save a Claude-generated report to the database

    Args:
        agent_type: Type of agent that generated the report
        report_title: Title/filename of the report
        report_content: Full markdown content
        file_path: Optional relative path in OneDrive
        task_id: Optional task ID if linked to a ClaudeTask

    Returns:
        Report ID if successful, None otherwise
    """
    if not USE_DATABASE:
        return None

    db = get_db()
    if not db:
        return None

    try:
        # Calculate file size
        file_size = len(report_content.encode('utf-8'))

        # Check if report already exists (by title and agent_type)
        existing = db.query(ClaudeReport).filter(
            ClaudeReport.report_title == report_title,
            ClaudeReport.agent_type == agent_type
        ).first()

        if existing:
            # Update existing report
            existing.report_content = report_content
            existing.file_path = file_path
            existing.file_size = file_size
            existing.task_id = task_id
            existing.updated_at = datetime.utcnow()
            db.commit()
            return existing.id
        else:
            # Create new report
            report = ClaudeReport(
                agent_type=agent_type,
                report_title=report_title,
                report_content=report_content,
                file_path=file_path,
                file_size=file_size,
                task_id=task_id
            )
            db.add(report)
            db.commit()
            return report.id

    except Exception as e:
        db.rollback()
        print(f"Error saving Claude report: {e}")
        return None
    finally:
        db.close()


def get_claude_reports(limit: int = 50, agent_type: str = None) -> List[Dict]:
    """
    Get Claude-generated reports from database

    Args:
        limit: Maximum number of reports to return
        agent_type: Optional filter by agent type

    Returns:
        List of report dictionaries
    """
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        query = db.query(ClaudeReport)

        if agent_type:
            query = query.filter(ClaudeReport.agent_type == agent_type)

        reports = query.order_by(ClaudeReport.created_at.desc()).limit(limit).all()

        return [{
            'id': r.id,
            'path': r.file_path or f'{r.agent_type}/{r.report_title}.md',
            'title': r.report_title,
            'agent_type': r.agent_type,
            'size': r.file_size or 0,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'summary': f'{r.agent_type} report',
            'content': r.report_content
        } for r in reports]

    except Exception as e:
        print(f"Error getting Claude reports: {e}")
        return []
    finally:
        db.close()


def get_claude_report_content(report_id: int) -> Optional[str]:
    """
    Get the full content of a specific Claude report

    Args:
        report_id: ID of the report

    Returns:
        Report content as markdown string, or None if not found
    """
    if not USE_DATABASE:
        return None

    db = get_db()
    if not db:
        return None

    try:
        report = db.query(ClaudeReport).filter(ClaudeReport.id == report_id).first()
        return report.report_content if report else None

    except Exception as e:
        print(f"Error getting Claude report content: {e}")
        return None
    finally:
        db.close()


# ============================================================================
# SCHEDULE CONFIGURATION OPERATIONS
# ============================================================================

def init_default_schedules():
    """Initialize default schedules if they don't exist"""
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        # Check if schedules already exist
        count = db.query(ScheduleConfig).count()
        if count > 0:
            return True  # Already initialized

        # Create default schedules
        default_schedules = [
            ScheduleConfig(
                task_name='morning_intelligence_report',
                display_name='Morning Intelligence Report',
                schedule_type='cron',
                hour=7,
                minute=0,
                day_of_week=None,
                enabled=1,
                description='Comprehensive morning briefing with critical alerts and priorities'
            ),
            ScheduleConfig(
                task_name='inventory_health_check',
                display_name='Inventory Health Check',
                schedule_type='interval',
                interval_seconds=21600,  # 6 hours
                enabled=1,
                description='Quick check for critical inventory issues every 6 hours'
            ),
            ScheduleConfig(
                task_name='weekly_summary_report',
                display_name='Weekly Summary Report',
                schedule_type='cron',
                hour=8,
                minute=0,
                day_of_week=0,  # Monday
                enabled=1,
                description='Week-over-week analysis and upcoming week planning'
            )
        ]

        for schedule in default_schedules:
            db.add(schedule)

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error initializing default schedules: {e}")
        return False
    finally:
        db.close()


def get_all_schedules() -> List[Dict]:
    """Get all schedule configurations"""
    if not USE_DATABASE:
        return []

    db = get_db()
    if not db:
        return []

    try:
        schedules = db.query(ScheduleConfig).order_by(ScheduleConfig.task_name).all()

        return [{
            'id': s.id,
            'task_name': s.task_name,
            'display_name': s.display_name,
            'schedule_type': s.schedule_type,
            'hour': s.hour,
            'minute': s.minute,
            'day_of_week': s.day_of_week,
            'interval_seconds': s.interval_seconds,
            'enabled': bool(s.enabled),
            'description': s.description,
            'last_modified': s.last_modified.isoformat() if s.last_modified else None,
            'created_at': s.created_at.isoformat() if s.created_at else None
        } for s in schedules]

    except Exception as e:
        print(f"Error getting schedules: {e}")
        return []
    finally:
        db.close()


def get_schedule(task_name: str) -> Optional[Dict]:
    """Get a specific schedule configuration"""
    if not USE_DATABASE:
        return None

    db = get_db()
    if not db:
        return None

    try:
        schedule = db.query(ScheduleConfig).filter(ScheduleConfig.task_name == task_name).first()

        if not schedule:
            return None

        return {
            'id': schedule.id,
            'task_name': schedule.task_name,
            'display_name': schedule.display_name,
            'schedule_type': schedule.schedule_type,
            'hour': schedule.hour,
            'minute': schedule.minute,
            'day_of_week': schedule.day_of_week,
            'interval_seconds': schedule.interval_seconds,
            'enabled': bool(schedule.enabled),
            'description': schedule.description,
            'last_modified': schedule.last_modified.isoformat() if schedule.last_modified else None
        }

    except Exception as e:
        print(f"Error getting schedule: {e}")
        return None
    finally:
        db.close()


def update_schedule(task_name: str, schedule_data: Dict) -> bool:
    """Update a schedule configuration"""
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        schedule = db.query(ScheduleConfig).filter(ScheduleConfig.task_name == task_name).first()

        if not schedule:
            return False

        # Update fields
        if 'schedule_type' in schedule_data:
            schedule.schedule_type = schedule_data['schedule_type']

        if 'hour' in schedule_data:
            schedule.hour = schedule_data['hour']

        if 'minute' in schedule_data:
            schedule.minute = schedule_data['minute']

        if 'day_of_week' in schedule_data:
            schedule.day_of_week = schedule_data['day_of_week']

        if 'interval_seconds' in schedule_data:
            schedule.interval_seconds = schedule_data['interval_seconds']

        if 'enabled' in schedule_data:
            schedule.enabled = 1 if schedule_data['enabled'] else 0

        schedule.last_modified = datetime.utcnow()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error updating schedule: {e}")
        return False
    finally:
        db.close()


# ============================================================================
# SYSTEM SETTINGS OPERATIONS
# ============================================================================

def get_system_settings() -> Optional[Dict]:
    """
    Get system settings (creates default if not exists)

    Returns:
        Dictionary with system settings or None if database unavailable
    """
    if not USE_DATABASE:
        return {'timezone': 'America/Los_Angeles'}  # Default fallback

    db = get_db()
    if not db:
        return {'timezone': 'America/Los_Angeles'}

    try:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()

        # Create default settings if not exists
        if not settings:
            settings = SystemSettings(
                id=1,
                timezone='America/Los_Angeles'
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return {
            'timezone': settings.timezone,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }

    except Exception as e:
        print(f"Error getting system settings: {e}")
        return {'timezone': 'America/Los_Angeles'}
    finally:
        db.close()


def get_timezone() -> str:
    """
    Get the configured timezone for the application

    Returns:
        Timezone string (e.g., 'Asia/Kuala_Lumpur')
    """
    settings = get_system_settings()
    return settings.get('timezone', 'America/Los_Angeles')


def update_timezone(timezone: str) -> bool:
    """
    Update the system timezone

    Args:
        timezone: Valid timezone string (e.g., 'Asia/Bangkok')

    Returns:
        True if updated successfully, False otherwise
    """
    if not USE_DATABASE:
        return False

    db = get_db()
    if not db:
        return False

    try:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()

        if not settings:
            # Create if doesn't exist
            settings = SystemSettings(id=1, timezone=timezone)
            db.add(settings)
        else:
            # Update existing
            settings.timezone = timezone
            settings.updated_at = datetime.utcnow()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error updating timezone: {e}")
        return False
    finally:
        db.close()


def get_available_timezones() -> List[Dict[str, str]]:
    """
    Get list of common timezones organized by region

    Returns:
        List of timezone dictionaries with 'value' and 'label'
    """
    timezones = [
        # Asia
        {'value': 'Asia/Kuala_Lumpur', 'label': 'Malaysia (Kuala Lumpur) - UTC+8', 'region': 'Asia'},
        {'value': 'Asia/Singapore', 'label': 'Singapore - UTC+8', 'region': 'Asia'},
        {'value': 'Asia/Bangkok', 'label': 'Thailand (Bangkok) - UTC+7', 'region': 'Asia'},
        {'value': 'Asia/Ho_Chi_Minh', 'label': 'Vietnam (Ho Chi Minh) - UTC+7', 'region': 'Asia'},
        {'value': 'Asia/Jakarta', 'label': 'Indonesia (Jakarta) - UTC+7', 'region': 'Asia'},
        {'value': 'Asia/Manila', 'label': 'Philippines (Manila) - UTC+8', 'region': 'Asia'},
        {'value': 'Asia/Hong_Kong', 'label': 'Hong Kong - UTC+8', 'region': 'Asia'},
        {'value': 'Asia/Shanghai', 'label': 'China (Shanghai) - UTC+8', 'region': 'Asia'},
        {'value': 'Asia/Tokyo', 'label': 'Japan (Tokyo) - UTC+9', 'region': 'Asia'},
        {'value': 'Asia/Seoul', 'label': 'South Korea (Seoul) - UTC+9', 'region': 'Asia'},
        {'value': 'Asia/Kolkata', 'label': 'India (Kolkata) - UTC+5:30', 'region': 'Asia'},
        {'value': 'Asia/Dubai', 'label': 'UAE (Dubai) - UTC+4', 'region': 'Asia'},

        # Europe
        {'value': 'Europe/London', 'label': 'United Kingdom (London) - UTC+0/+1', 'region': 'Europe'},
        {'value': 'Europe/Paris', 'label': 'France (Paris) - UTC+1/+2', 'region': 'Europe'},
        {'value': 'Europe/Berlin', 'label': 'Germany (Berlin) - UTC+1/+2', 'region': 'Europe'},
        {'value': 'Europe/Amsterdam', 'label': 'Netherlands (Amsterdam) - UTC+1/+2', 'region': 'Europe'},
        {'value': 'Europe/Madrid', 'label': 'Spain (Madrid) - UTC+1/+2', 'region': 'Europe'},
        {'value': 'Europe/Rome', 'label': 'Italy (Rome) - UTC+1/+2', 'region': 'Europe'},
        {'value': 'Europe/Moscow', 'label': 'Russia (Moscow) - UTC+3', 'region': 'Europe'},

        # America
        {'value': 'America/New_York', 'label': 'USA (New York/Eastern) - UTC-5/-4', 'region': 'America'},
        {'value': 'America/Chicago', 'label': 'USA (Chicago/Central) - UTC-6/-5', 'region': 'America'},
        {'value': 'America/Denver', 'label': 'USA (Denver/Mountain) - UTC-7/-6', 'region': 'America'},
        {'value': 'America/Los_Angeles', 'label': 'USA (Los Angeles/Pacific) - UTC-8/-7', 'region': 'America'},
        {'value': 'America/Toronto', 'label': 'Canada (Toronto) - UTC-5/-4', 'region': 'America'},
        {'value': 'America/Vancouver', 'label': 'Canada (Vancouver) - UTC-8/-7', 'region': 'America'},
        {'value': 'America/Mexico_City', 'label': 'Mexico (Mexico City) - UTC-6/-5', 'region': 'America'},
        {'value': 'America/Sao_Paulo', 'label': 'Brazil (São Paulo) - UTC-3', 'region': 'America'},

        # Pacific
        {'value': 'Australia/Sydney', 'label': 'Australia (Sydney) - UTC+10/+11', 'region': 'Pacific'},
        {'value': 'Australia/Melbourne', 'label': 'Australia (Melbourne) - UTC+10/+11', 'region': 'Pacific'},
        {'value': 'Pacific/Auckland', 'label': 'New Zealand (Auckland) - UTC+12/+13', 'region': 'Pacific'},

        # Africa
        {'value': 'Africa/Cairo', 'label': 'Egypt (Cairo) - UTC+2', 'region': 'Africa'},
        {'value': 'Africa/Johannesburg', 'label': 'South Africa (Johannesburg) - UTC+2', 'region': 'Africa'},
    ]

    return timezones
