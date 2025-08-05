"""Data conversion utilities."""

from datetime import datetime
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds


def convert_firestore_datetime(data):
    if isinstance(data, (DatetimeWithNanoseconds, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: convert_firestore_datetime(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_firestore_datetime(item) for item in data]
    return data