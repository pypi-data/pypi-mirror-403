"""
velmu.models.invite
~~~~~~~~~~~~~~~~~~~

Invite model.
"""
from typing import Optional, TYPE_CHECKING
from .base import BaseModel
from .user import User
from ..utils import parse_time

if TYPE_CHECKING:
    from ..state import ConnectionState
    from .guild import Guild
    from .channel import Channel

class Invite(BaseModel):
    """Represents a Velmu Invite."""
    
    __slots__ = ('_state', 'code', 'guild', 'channel', 'url', 'inviter', 'uses', 'max_uses', 'max_age', 'temporary', 'created_at')
    
    def __init__(self, state: 'ConnectionState', data: dict):
        self._state = state
        self.code = data.get('code')
        self.url = data.get('url')
        self._update(data)
        
    def _update(self, data: dict):
        self.uses = data.get('uses')
        self.max_uses = data.get('maxUses')
        self.max_age = data.get('maxAge')
        self.temporary = data.get('temporary', False)
        self.created_at = parse_time(data.get('createdAt'))
        
        inviter_data = data.get('inviter')
        self.inviter = User(self._state, inviter_data) if inviter_data else None
        
        # Guild/Channel might be partial or full depending on payload
        # For now we don't deeply parse them unless needed
        self.guild = data.get('guild') # TODO: parse properly if needed
        self.channel = data.get('channel') 
