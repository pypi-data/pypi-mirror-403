"""Time utility functions"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def format_duration(ms: float) -> str:
    """Format response time
    
    Args:
        ms: Milliseconds
        
    Returns:
        Formatted string
    """
    if ms < 1:
        return f"{ms * 1000:.0f}µs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        return f"{ms / 60000:.2f}min"


def parse_time_range(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    hours: int = 1
) -> Tuple[datetime, datetime]:
    """Parse time range
    
    Args:
        start_time: Start time
        end_time: End time
        hours: If time not specified, use past N hours
        
    Returns:
        (start_time, end_time) tuple
    """
    now = datetime.now(timezone.utc)
    
    if end_time is None:
        end_time = now
    
    if start_time is None:
        start_time = end_time - timedelta(hours=hours)
    
    return start_time, end_time


def get_time_bucket(
    timestamp: datetime,
    interval_seconds: int = 60
) -> datetime:
    """Get time bucket
    
    Align timestamp to a time bucket of the specified interval.
    
    Args:
        timestamp: Timestamp
        interval_seconds: Interval in seconds
        
    Returns:
        Aligned timestamp
    """
    # Convert to seconds
    ts = timestamp.timestamp()
    
    # Align to interval
    bucket_ts = (ts // interval_seconds) * interval_seconds
    
    return datetime.utcfromtimestamp(bucket_ts)


def time_ago(dt: datetime) -> str:
    """Calculate friendly time difference description
    
    Args:
        dt: Timestamp
        
    Returns:
        Friendly time description, e.g. "5 minutes ago"
    """
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    else:
        return f"{int(seconds / 86400)} days ago"
