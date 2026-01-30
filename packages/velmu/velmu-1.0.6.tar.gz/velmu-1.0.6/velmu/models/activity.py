from enum import Enum
from typing import Optional

class ActivityType(Enum):
    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

class Activity:
    """Represents an activity in Velmu.

    Attributes
    ----------
    name: :class:`str`
        The name of the activity.
    type: :class:`ActivityType`
        The type of activity.
    url: Optional[:class:`str`]
        The URL for the activity (mostly for streaming).
    """

    def __init__(self, *, name: str, type: ActivityType = ActivityType.playing, url: Optional[str] = None):
        self.name = name
        self.type = type
        self.url = url

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.type.value,
            'url': self.url
        }

    def __repr__(self):
        return f'<Activity name={self.name!r} type={self.type!r} url={self.url!r}>'
