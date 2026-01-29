"""Run ID generation utility."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from task_framework.models.schedule import Schedule


def generate_run_id(schedule_id: str, scheduled_for_utc: datetime) -> str:
    """Generate deterministic run_id from schedule_id and UTC timestamp.
    
    Format: {schedule_id}_run_{YYYY-MM-DDTHH:MM:SS.000000Z}
    
    Note: The timestamp is truncated to second precision to ensure determinism
    across multiple workers that may call this at slightly different microseconds.
    
    Args:
        schedule_id: Schedule identifier
        scheduled_for_utc: UTC timestamp of scheduled fire time
    
    Returns:
        Run ID in format: {schedule_id}_run_{YYYY-MM-DDTHH:MM:SS.000000Z}
    """
    # Format timestamp with second precision (microseconds zeroed)
    # This ensures all workers generate the same run_id for the same cron trigger
    # Ensure timestamp is timezone-aware (UTC)
    if scheduled_for_utc.tzinfo is None:
        scheduled_for_utc = scheduled_for_utc.replace(tzinfo=timezone.utc)
    
    # Truncate to second precision for determinism
    truncated = scheduled_for_utc.replace(microsecond=0)
    timestamp_str = truncated.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    
    return f"{schedule_id}_run_{timestamp_str}"


def get_deterministic_scheduled_time(cron: str, tz: str) -> datetime:
    """Get the deterministic scheduled time for a cron trigger.
    
    This returns the current minute's scheduled time, truncated to seconds,
    ensuring all workers generate the same run_id.
    
    Args:
        cron: Cron expression (not used yet, but reserved for future precision)
        tz: Timezone string
    
    Returns:
        UTC datetime truncated to second precision
    """
    now = datetime.now(timezone.utc)
    # Truncate to second precision - all workers within the same second 
    # will generate the same run_id
    return now.replace(microsecond=0)


def get_scheduled_time_local(scheduled_for_utc: datetime, schedule: Schedule) -> datetime:
    """Convert UTC scheduled time to schedule's local timezone.
    
    Args:
        scheduled_for_utc: UTC timestamp
        schedule: Schedule instance with timezone
        
    Returns:
        Local datetime in schedule's timezone
    """
    # Convert UTC to schedule timezone
    tz = ZoneInfo(schedule.timezone)
    return scheduled_for_utc.astimezone(tz)

