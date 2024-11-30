from datetime import datetime
from humanize import naturaltime

def timeago(dt):
    """Convert a datetime to a human-readable relative time string."""
    if not dt:
        return ''
    if not isinstance(dt, datetime):
        return str(dt)
    return naturaltime(dt)
