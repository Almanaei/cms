from datetime import datetime
from humanize import naturaltime, intcomma

def timeago(dt):
    """Convert a datetime to a human-readable relative time string."""
    if not dt:
        return ''
    if not isinstance(dt, datetime):
        return str(dt)
    return naturaltime(dt)

def number_format(value):
    """Format a number with commas as thousand separators."""
    try:
        return intcomma(value)
    except (ValueError, TypeError):
        return value
