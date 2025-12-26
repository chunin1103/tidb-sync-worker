"""
Base utilities for autonomous agents
Shared functions for logging, database operations, and agent execution
"""

import logging
from datetime import datetime
from typing import Optional, Generator
from src.core.database import (
    save_agent_run,
    complete_agent_run,
    save_agent_report,
    USE_DATABASE
)
from src.core.agent_backend import execute_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_autonomous_agent(
    agent_type: str,
    prompt: str,
    run_type: str,
    trigger: str,
    report_type: str,
    report_title: str
) -> str:
    """
    Generic function to run an autonomous agent with full lifecycle management

    Args:
        agent_type: Type of agent to run (e.g., 'inventory_intelligence')
        prompt: The prompt to send to the agent
        run_type: Type of run ('scheduled', 'manual', 'triggered')
        trigger: What triggered this run (e.g., 'cron:daily_7am', 'manual:user')
        report_type: Type of report being generated
        report_title: Title for the report

    Returns:
        The full report content as a string

    Raises:
        Exception if agent execution fails
    """
    logger.info(f"🚀 Starting {agent_type} agent: {report_title}")

    # Save agent run to database
    run_id = None
    if USE_DATABASE:
        run_id = save_agent_run(
            agent_type=agent_type,
            run_type=run_type,
            trigger=trigger
        )

    try:
        # Generate unique session ID
        session_id = f"auto_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Execute agent and collect response
        report_parts = []
        for chunk in execute_agent(agent_type, prompt, session_id):
            report_parts.append(chunk)

        full_report = "".join(report_parts)

        # Save report to database
        if USE_DATABASE and run_id:
            save_agent_report(
                agent_run_id=run_id,
                agent_type=agent_type,
                report_type=report_type,
                title=report_title,
                content=full_report
            )

            # Mark run as completed
            summary = full_report[:200] + "..." if len(full_report) > 200 else full_report
            complete_agent_run(
                run_id=run_id,
                status='completed',
                output_summary=summary
            )

        logger.info(f"✅ {report_title} completed! ({len(full_report)} chars)")
        return full_report

    except Exception as e:
        logger.error(f"❌ {report_title} failed: {str(e)}")

        if USE_DATABASE and run_id:
            complete_agent_run(
                run_id=run_id,
                status='failed',
                error_message=str(e)
            )

        raise


def create_session_id(prefix: str) -> str:
    """
    Create a unique session ID with timestamp

    Args:
        prefix: Prefix for the session ID

    Returns:
        Session ID string
    """
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# Export logger for use in agent modules
__all__ = ['run_autonomous_agent', 'create_session_id', 'logger']
