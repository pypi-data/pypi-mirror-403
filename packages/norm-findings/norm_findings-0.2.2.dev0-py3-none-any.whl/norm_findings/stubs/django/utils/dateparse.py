from datetime import datetime

def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except:
        return None

def parse_date(value):
    try:
        return datetime.fromisoformat(value).date()
    except:
        return None
