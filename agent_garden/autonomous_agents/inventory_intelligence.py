"""
Inventory Intelligence Agent - Scheduled Tasks
Automated inventory monitoring, reporting, and alerts
"""

from datetime import datetime
from src.scheduling.celery_app import celery_app
from autonomous_agents.base import run_autonomous_agent, logger


# ============================================================================
# SCHEDULED TASKS
# ============================================================================

@celery_app.task(name='autonomous_agents.morning_intelligence_report')
def morning_intelligence_report():
    """
    Runs daily at 7:00 AM
    Generates comprehensive morning intelligence report
    """
    logger.info("🌅 Starting Morning Intelligence Report...")

    prompt = """Generate a comprehensive morning intelligence report using the LIVE DATABASE CONTEXT provided in your system prompt.

⚡ IMPORTANT: Reference specific products, quantities, and metrics from the database context. Use real data, not hypotheticals.

1. **CRITICAL ALERTS** (Products needing immediate attention)
   - Reference the ZERO INVENTORY products from database context
   - Highlight products with < 30 days of stock from sales velocity data
   - Provide urgent reorder recommendations based on actual stock levels

2. **TODAY'S PRIORITIES** (Recommended actions for today)
   - Top 3-5 products to cut today (use real product models from database)
   - Specific cutting recommendations with quantities
   - Expected inventory levels after cuts

3. **INVENTORY HEALTH SUMMARY**
   - Use the database stats section for totals
   - Reference low stock alerts from context
   - Identify overstock from database data

4. **UPCOMING DEADLINES**
   - Seasonal product deadlines (Holly Berry Red, Tekta)
   - Next Bullseye order window
   - Important dates this week

Format the report with clear sections, bullet points, and actionable items. Always cite specific products by model number from the database context."""

    try:
        run_autonomous_agent(
            agent_type='inventory_intelligence',
            prompt=prompt,
            run_type='scheduled',
            trigger='cron:daily_7am',
            report_type='morning_intelligence',
            report_title=f"Morning Intelligence Report - {datetime.now().strftime('%B %d, %Y')}"
        )

        # TODO: Send notifications (Slack, Email)
        # send_slack_notification("#inventory-alerts", full_report)
        # send_email("team@artglasssupplies.com", "Morning Report", full_report)

    except Exception as e:
        logger.error(f"❌ Morning Intelligence Report failed: {str(e)}")
        raise


@celery_app.task(name='autonomous_agents.inventory_health_check')
def inventory_health_check():
    """
    Runs every 6 hours
    Quick check for critical inventory issues
    """
    logger.info("🔍 Running Inventory Health Check...")

    prompt = """Perform a quick inventory health check using the LIVE DATABASE CONTEXT:

⚡ Use the real-time data provided in the database context section of your system prompt.

1. Any products at ZERO inventory (reference the CRITICAL INVENTORY ALERTS section)
2. Any products below 30 days of stock (use sales velocity data from database context)
3. Any unusual patterns in recent orders or bestsellers

Keep it brief - only report issues that need immediate attention. Cite specific product models and quantities from the database."""

    try:
        report = run_autonomous_agent(
            agent_type='inventory_intelligence',
            prompt=prompt,
            run_type='scheduled',
            trigger='interval:6_hours',
            report_type='health_check',
            report_title=f"Health Check - {datetime.now().strftime('%I:%M %p')}"
        )

        # TODO: Send critical alerts only if issues found
        # if "ZERO inventory" in report or "CRITICAL" in report:
        #     send_sms_alert(report)

    except Exception as e:
        logger.error(f"❌ Health Check failed: {str(e)}")
        raise


@celery_app.task(name='autonomous_agents.weekly_summary_report')
def weekly_summary_report():
    """
    Runs every Monday at 8:00 AM
    Generates weekly summary and upcoming week preview
    """
    logger.info("📊 Starting Weekly Summary Report...")

    prompt = """Generate a weekly summary report using the LIVE DATABASE CONTEXT:

⚡ Use real data from the database context provided in your system prompt.

1. **LAST WEEK RECAP**
   - Key inventory changes (reference current stock levels vs expected)
   - Products that were likely cut based on size distributions
   - Any stockout events (check zero inventory section)

2. **THIS WEEK PRIORITIES**
   - Top priorities based on critical alerts and low stock from database
   - Recommended cutting schedule using specific product models
   - Products to monitor (use sales velocity data)

3. **UPCOMING EVENTS**
   - Seasonal deadlines approaching (check current date)
   - Bullseye order timing
   - Important dates

Provide strategic insights based on actual database statistics and sales trends. Reference specific products, quantities, and metrics."""

    try:
        run_autonomous_agent(
            agent_type='inventory_intelligence',
            prompt=prompt,
            run_type='scheduled',
            trigger='cron:monday_8am',
            report_type='weekly_summary',
            report_title=f"Weekly Summary - Week of {datetime.now().strftime('%B %d, %Y')}"
        )

    except Exception as e:
        logger.error(f"❌ Weekly Summary failed: {str(e)}")
        raise
