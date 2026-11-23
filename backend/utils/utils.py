"""Common utility functions"""
from datetime import datetime

def get_current_timestamp()->str:
    """Returns current time"""
    curr = datetime.now().isoformat()
    return str(curr)
