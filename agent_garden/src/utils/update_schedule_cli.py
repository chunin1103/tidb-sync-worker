#!/usr/bin/env python
"""
Command-line tool for updating schedules
Quick way to update schedules without using the web UI

Usage:
    # Update morning report to 7:30 AM
    python update_schedule_cli.py morning_intelligence_report --hour 7 --minute 30

    # Change inventory check to every 4 hours
    python update_schedule_cli.py inventory_health_check --interval 14400

    # Disable weekly report
    python update_schedule_cli.py weekly_summary_report --disable

    # Enable weekly report
    python update_schedule_cli.py weekly_summary_report --enable
"""

import argparse
import sys
from src.core.database import update_schedule, get_schedule, get_all_schedules

def show_schedules():
    """Show all available schedules"""
    schedules = get_all_schedules()

    print("\n📅 Available Schedules:")
    print("=" * 60)

    for sched in schedules:
        enabled = "✅" if sched['enabled'] else "❌"
        print(f"\n{enabled} {sched['display_name']}")
        print(f"   Task Name: {sched['task_name']}")

        if sched['schedule_type'] == 'cron':
            time_str = f"{sched['hour']:02d}:{sched['minute']:02d}"
            if sched['day_of_week'] is not None:
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_str = days[sched['day_of_week']]
                print(f"   Current: Every {day_str} at {time_str}")
            else:
                print(f"   Current: Daily at {time_str}")
        else:
            hours = sched['interval_seconds'] / 3600
            print(f"   Current: Every {hours:.1f} hours ({sched['interval_seconds']} seconds)")

    print("\n" + "=" * 60)

def update_schedule_cli(task_name, hour=None, minute=None, interval=None, enable=None):
    """Update a schedule via CLI"""

    # Get current schedule
    current = get_schedule(task_name)
    if not current:
        print(f"❌ Schedule not found: {task_name}")
        print("\nAvailable schedules:")
        for s in get_all_schedules():
            print(f"  • {s['task_name']}")
        sys.exit(1)

    # Show current schedule
    print(f"\n📋 Current Schedule: {current['display_name']}")
    if current['schedule_type'] == 'cron':
        print(f"   Type: Cron (specific time)")
        print(f"   Time: {current['hour']:02d}:{current['minute']:02d}")
        if current['day_of_week'] is not None:
            print(f"   Day: {current['day_of_week']} (0=Monday)")
    else:
        hours = current['interval_seconds'] / 3600
        print(f"   Type: Interval (recurring)")
        print(f"   Interval: Every {hours:.1f} hours ({current['interval_seconds']} seconds)")
    print(f"   Enabled: {'Yes' if current['enabled'] else 'No'}")

    # Build update data
    update_data = {}

    if hour is not None:
        if not (0 <= hour <= 23):
            print("❌ Hour must be between 0 and 23")
            sys.exit(1)
        update_data['hour'] = hour

    if minute is not None:
        if not (0 <= minute <= 59):
            print("❌ Minute must be between 0 and 59")
            sys.exit(1)
        update_data['minute'] = minute

    if interval is not None:
        if interval < 60:
            print("❌ Interval must be at least 60 seconds (1 minute)")
            sys.exit(1)
        update_data['interval_seconds'] = interval

    if enable is not None:
        update_data['enabled'] = enable

    if not update_data:
        print("\n⚠️  No changes specified")
        print("Use --help to see available options")
        sys.exit(0)

    # Perform update
    print("\n🔄 Updating schedule...")
    success = update_schedule(task_name, update_data)

    if success:
        print("✅ Schedule updated successfully!")

        # Show new schedule
        updated = get_schedule(task_name)
        print(f"\n📋 New Schedule:")
        if updated['schedule_type'] == 'cron':
            print(f"   Time: {updated['hour']:02d}:{updated['minute']:02d}")
        else:
            hours = updated['interval_seconds'] / 3600
            print(f"   Interval: Every {hours:.1f} hours ({updated['interval_seconds']} seconds)")
        print(f"   Enabled: {'Yes' if updated['enabled'] else 'No'}")

        print("\n⏱️  Changes will take effect within 60 seconds")
        print("   (No Celery Beat restart needed!)")
    else:
        print("❌ Failed to update schedule")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Update Agent Garden schedules from command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Update morning report to 7:30 AM
  %(prog)s morning_intelligence_report --hour 7 --minute 30

  # Change inventory check to every 4 hours (14400 seconds)
  %(prog)s inventory_health_check --interval 14400

  # Disable weekly report
  %(prog)s weekly_summary_report --disable

  # Enable and update time
  %(prog)s morning_intelligence_report --enable --hour 8 --minute 0

  # Show all schedules
  %(prog)s --list
        ''')

    parser.add_argument('task_name', nargs='?', help='Task name to update')
    parser.add_argument('--hour', type=int, help='Hour (0-23) for cron schedules')
    parser.add_argument('--minute', type=int, help='Minute (0-59) for cron schedules')
    parser.add_argument('--interval', type=int, help='Interval in seconds for interval schedules')
    parser.add_argument('--enable', action='store_true', help='Enable the schedule')
    parser.add_argument('--disable', action='store_true', help='Disable the schedule')
    parser.add_argument('--list', action='store_true', help='List all schedules')

    args = parser.parse_args()

    # Show schedules if --list or no task name
    if args.list or not args.task_name:
        show_schedules()
        sys.exit(0)

    # Handle enable/disable
    enable_flag = None
    if args.enable and args.disable:
        print("❌ Cannot use both --enable and --disable")
        sys.exit(1)
    elif args.enable:
        enable_flag = True
    elif args.disable:
        enable_flag = False

    # Update schedule
    update_schedule_cli(
        args.task_name,
        hour=args.hour,
        minute=args.minute,
        interval=args.interval,
        enable=enable_flag
    )

if __name__ == '__main__':
    main()
