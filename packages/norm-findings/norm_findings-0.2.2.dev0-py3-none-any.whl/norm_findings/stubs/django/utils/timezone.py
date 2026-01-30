from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc)

def make_aware(value):
    return value.replace(tzinfo=timezone.utc)

def is_aware(value):
    return value.tzinfo is not None

def get_current_timezone():
    return timezone.utc
