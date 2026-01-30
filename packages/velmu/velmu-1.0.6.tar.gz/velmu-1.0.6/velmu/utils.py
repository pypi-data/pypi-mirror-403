"""
velmu.utils
~~~~~~~~~~~

Helper functions and utilities.
"""
import datetime
import warnings

def parse_time(timestamp: str) -> datetime.datetime:
    """Parses an ISO 8601 timestamp."""
    if timestamp:
        return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return datetime.datetime.utcnow()

def snowflake_time(id: int) -> datetime.datetime:
    """(Placeholder) Returns creation time from a Velmu Snowflake."""
    # Velmu uses UUIDs currently, but if we migrate to Snowflakes:
    # return datetime.datetime.utcfromtimestamp(((id >> 22) + 1420070400000) / 1000)
    return datetime.datetime.utcnow()

def get(iterable, **attrs):
    """A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``.

    Args:
        iterable (Iterable): The iterable to search through.
        **attrs (Any): Keyword arguments that denote attributes to search with.
    """
    for item in iterable:
        if all(getattr(item, attr) == value for attr, value in attrs.items()):
            return item
    return None

def find(predicate, iterable):
    """A helper to return the first element in the iterable that satisfies
    the predicate.

    Args:
        predicate (Callable): A callable that returns a boolean.
        iterable (Iterable): The iterable to search through.
    """
    for element in iterable:
        if predicate(element):
            return element
    return None
