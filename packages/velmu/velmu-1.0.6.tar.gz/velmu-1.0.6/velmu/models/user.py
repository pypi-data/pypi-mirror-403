"""
velmu.models.user
~~~~~~~~~~~~~~~~~

User and Member models.
"""
from typing import Optional, List, TYPE_CHECKING, Union
from ..abc import Snowflake, Messageable
from ..utils import parse_time

if TYPE_CHECKING:
    from ..state import ConnectionState
    from .guild import Guild

class User(Snowflake, Messageable):
    """Represents a Velmu User."""
    
    __slots__ = ('_state', 'id', 'username', 'avatar_url', 'bot', 'global_name', 'status')
    
    def __init__(self, state: 'ConnectionState', data: dict):
        self._state = state
        self.id = data.get('id')
        self._update(data)

    def _update(self, data: dict):
        self.username = data.get('username')
        # discriminator removed
        self.avatar_url = data.get('avatarUrl')
        self.bot = data.get('bot', False)
        # Support both globalName and displayName
        self.global_name = data.get('globalName') or data.get('displayName')

    @property
    def mention(self) -> str:
        return f'<@{self.id}>'
        
    @property
    def display_name(self) -> str:
        return self.global_name or self.username

    async def _get_channel(self):
        return await self.create_dm()

    async def create_dm(self):
        """Creates a DM channel with this user."""
        data = await self._state.http.create_dm(self.id)
        return self._state.store_channel(data)

    def __repr__(self):
        return f'<User id={self.id} name={self.username!r} bot={self.bot}>'

class Member(User):
    """Represents a Member of a Guild."""
    
    __slots__ = ('guild', 'joined_at', 'nick', 'roles')
    
    def __init__(self, state: 'ConnectionState', data: dict, guild: 'Guild'):
        self.guild = guild
        # data usually contains a 'user' object
        user_data = data.get('user', {})
        super().__init__(state, user_data)
        if self.id is None:
            self.id = data.get('userId')
        self._update_member(data)
        
    def _update_member(self, data: dict):
        self.joined_at = parse_time(data.get('joinedAt'))
        # Check multiple keys for nickname
        self.nick = data.get('nick') or data.get('nickname') or data.get('displayName')
        # Handle cases where roles is a list of dicts (full objects) or strings (IDs)
        raw_roles = data.get('roles', [])
        processed_roles = []
        for r in raw_roles:
            role_id = r if isinstance(r, str) else r.get('id')
            role = self.guild.get_role(role_id)
            if role:
                processed_roles.append(role)
        self.roles = processed_roles

    @property
    def display_name(self) -> str:
        return self.nick or super().display_name

    async def edit(self, *, nick: Optional[str] = None):
        """Edits the member.
        
        Parameters
        -----------
        nick: Optional[str]
            The new nickname for the member.
        """
        payload = {}
        if nick is not None:
             payload['nickname'] = nick
             
        if payload:
            await self._state.http.edit_member(self.guild.id, self.id, **payload)

    async def kick(self, *, reason: Optional[str] = None):
        """Kicks this member from the guild."""
        await self.guild.kick(self, reason=reason)

    async def ban(self, *, reason: Optional[str] = None):
        """Bans this member from the guild."""
        await self.guild.ban(self, reason=reason)

    async def add_roles(self, *roles: Union['Snowflake', str], reason: Optional[str] = None):
        """Adds roles to this member.
        
        Parameters
        -----------
        *roles: Union[Role, str]
            The roles to add. Can be Role objects or role IDs.
        reason: Optional[str]
            The reason for adding these roles.
        """
        for role in roles:
            role_id = role.id if hasattr(role, 'id') else role
            await self._state.http.add_role(self.guild.id, self.id, role_id)

    async def remove_roles(self, *roles: Union['Snowflake', str], reason: Optional[str] = None):
        """Removes roles from this member."""
        for role in roles:
            role_id = role.id if hasattr(role, 'id') else role
            await self._state.http.remove_role(self.guild.id, self.id, role_id)

    def __repr__(self):
        return f'<Member id={self.id} name={self.username!r} guild={self.guild.id!r}>'
