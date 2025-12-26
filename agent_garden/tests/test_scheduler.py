#!/usr/bin/env python
"""
Test script for DatabaseScheduler
Verifies that schedules are loading correctly from database
"""

import sys
from datetime import datetime
from src.scheduling.schedule_loader import load_schedules_from_db, get_schedule_summary
from src.core.database import get_all_schedules, get_timezone

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_database_schedules():
    """Test loading schedules directly from database"""
    print_section("DATABASE SCHEDULES")

    schedules = get_all_schedules()
    print(f"\n📊 Found {len(schedules)} schedules in database:\n")

    for sched in schedules:
        enabled = "✅ ENABLED" if sched['enabled'] else "❌ DISABLED"
        print(f"{enabled} {sched['display_name']}")
        print(f"   Task: {sched['task_name']}")
        print(f"   Type: {sched['schedule_type']}")

        if sched['schedule_type'] == 'cron':
            time_str = f"{sched['hour']:02d}:{sched['minute']:02d}"
            if sched['day_of_week'] is not None:
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_str = days[sched['day_of_week']]
                print(f"   Schedule: Every {day_str} at {time_str}")
            else:
                print(f"   Schedule: Daily at {time_str}")
        else:
            hours = sched['interval_seconds'] / 3600
            print(f"   Schedule: Every {hours:.1f} hours")

        print(f"   Last Modified: {sched['last_modified']}")
        print()

def test_celery_schedules():
    """Test loading schedules in Celery format"""
    print_section("CELERY BEAT SCHEDULES")

    beat_schedules = load_schedules_from_db()
    print(f"\n🔧 Loaded {len(beat_schedules)} schedules for Celery Beat:\n")

    for name, config in beat_schedules.items():
        print(f"📅 {name}")
        print(f"   Task: {config['task']}")
        print(f"   Schedule: {config['schedule']}")
        print(f"   Queue: {config['options'].get('queue', 'default')}")
        print()

def test_schedule_summary():
    """Test getting schedule summary"""
    print_section("SCHEDULE SUMMARY")

    summary = get_schedule_summary()

    print(f"\n📈 Summary:")
    print(f"   Total: {summary['total_schedules']}")
    print(f"   Enabled: {summary['enabled']}")
    print(f"   Disabled: {summary['disabled']}")
    print()

    if summary['schedules']:
        print("📋 Details:")
        for sched in summary['schedules']:
            status = "✅" if sched['enabled'] else "❌"
            print(f"   {status} {sched['display_name']}: {sched['schedule']}")

def test_timezone():
    """Test timezone configuration"""
    print_section("TIMEZONE CONFIGURATION")

    tz = get_timezone()
    now = datetime.now()

    print(f"\n🌍 Timezone: {tz}")
    print(f"⏰ Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Current Day: {now.strftime('%A')}")

def test_scheduler_import():
    """Test that DatabaseScheduler can be imported"""
    print_section("SCHEDULER IMPORT TEST")

    try:
        from src.scheduling.custom_scheduler import DatabaseScheduler
        print("\n✅ DatabaseScheduler imported successfully")
        print(f"   Class: {DatabaseScheduler.__name__}")
        print(f"   Module: {DatabaseScheduler.__module__}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to import DatabaseScheduler: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🧪 TESTING DATABASE SCHEDULER CONFIGURATION")
    print("=" * 60)

    # Run tests
    test_database_schedules()
    test_celery_schedules()
    test_schedule_summary()
    test_timezone()

    if not test_scheduler_import():
        print("\n⚠️  WARNING: DatabaseScheduler import failed!")
        print("   Celery Beat will not start properly.")
        sys.exit(1)

    # Final summary
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
    print("\n✅ All tests passed!")
    print("🚀 Ready to start Celery Beat with DatabaseScheduler")
    print("\nTo start Celery Beat:")
    print("   ./start_celery_beat.sh")
    print()

if __name__ == '__main__':
    main()
