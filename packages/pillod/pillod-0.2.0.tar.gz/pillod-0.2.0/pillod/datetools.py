from datetime import datetime, timedelta
import time


def current_timestamp():
    """Get the current Unix timestamp."""
    return int(time.time())


def current_datetime():
    """Get the current datetime as a string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def current_date():
    """Get the current date as a string."""
    return datetime.now().strftime('%Y-%m-%d')


def current_time():
    """Get the current time as a string."""
    return datetime.now().strftime('%H:%M:%S')


def format_datetime(dt, fmt='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object as a string.
    
    Args:
        dt: datetime object
        fmt: Format string (default: 'YYYY-MM-DD HH:MM:SS')
    """
    return dt.strftime(fmt)


def parse_datetime(date_string, fmt='%Y-%m-%d %H:%M:%S'):
    """Parse a string into a datetime object.
    
    Args:
        date_string: Date string to parse
        fmt: Format string (default: 'YYYY-MM-DD HH:MM:SS')
    """
    return datetime.strptime(date_string, fmt)


def add_days(dt, days):
    """Add days to a datetime object."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt + timedelta(days=days)


def add_hours(dt, hours):
    """Add hours to a datetime object."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt + timedelta(hours=hours)


def add_minutes(dt, minutes):
    """Add minutes to a datetime object."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt + timedelta(minutes=minutes)


def days_between(date1, date2):
    """Calculate the number of days between two dates."""
    if isinstance(date1, str):
        date1 = parse_datetime(date1, '%Y-%m-%d')
    if isinstance(date2, str):
        date2 = parse_datetime(date2, '%Y-%m-%d')
    
    return abs((date2 - date1).days)


def is_weekend(dt):
    """Check if a date falls on a weekend."""
    if isinstance(dt, str):
        dt = parse_datetime(dt, '%Y-%m-%d')
    return dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday


def is_leap_year(year):
    """Check if a year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def get_day_of_week(dt):
    """Get the day of the week (Monday=0, Sunday=6)."""
    if isinstance(dt, str):
        dt = parse_datetime(dt, '%Y-%m-%d')
    return dt.weekday()


def get_day_name(dt):
    """Get the name of the day of the week."""
    if isinstance(dt, str):
        dt = parse_datetime(dt, '%Y-%m-%d')
    return dt.strftime('%A')


def get_month_name(dt):
    """Get the name of the month."""
    if isinstance(dt, str):
        dt = parse_datetime(dt, '%Y-%m-%d')
    return dt.strftime('%B')


def start_of_day(dt):
    """Get the start of the day (midnight) for a given datetime."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt):
    """Get the end of the day (23:59:59) for a given datetime."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def time_ago(dt):
    """Get a human-readable representation of how long ago a datetime was."""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    elif seconds < 604800:
        return f"{int(seconds / 86400)} days ago"
    elif seconds < 2592000:
        return f"{int(seconds / 604800)} weeks ago"
    elif seconds < 31536000:
        return f"{int(seconds / 2592000)} months ago"
    else:
        return f"{int(seconds / 31536000)} years ago"
