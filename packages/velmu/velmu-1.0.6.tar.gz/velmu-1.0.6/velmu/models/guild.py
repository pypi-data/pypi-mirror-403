"""
velmu.models.guild
~~~~~~~~~~~~~~~~~~

Guild and Role models.
"""
from typing import Optional, List, Dict, TYPE_CHECKING, Union
from ..abc import Snowflake
from ..utils import parse_time
from .user import Member

if TYPE_CHECKING:
    from ..state import ConnectionState
    from .channel import Channel

class Role(Snowflake):
    """Represents a Guild Role."""
    
    __slots__ = ('_state', 'guild', 'id', 'name', 'color', 'hoist', 'position', 'permissions', 'managed', 'mentionable')
    
    def __init__(self, state: 'ConnectionState', data: dict, guild: 'Guild'):
        self._state = state
        self.guild = guild
        self.id = data.get('id')
        self._update(data)
        
    def _update(self, data: dict):
        self.name = data.get('name')
        self.color = data.get('color')
        self.hoist = data.get('hoist', False)
        self.position = data.get('position', 0)
        
        # Permissions conversion
        perm_value = data.get('permissions', 0)
        
        from ..permissions import Permissions
        
        # Handle list of strings (Velmu Backend format)
        if isinstance(perm_value, list):
            self.permissions = Permissions.from_backend_strings(perm_value)
        # Handle string integer (API sometimes sends strings for large bitfields)
        elif isinstance(perm_value, str):
            self.permissions = Permissions(int(perm_value))
        else:
            self.permissions = Permissions(perm_value)
        
        self.managed = data.get('managed', False)
        self.mentionable = data.get('mentionable', False)

    @property
    def mention(self) -> str:
        return f'<@&{self.id}>'

    async def edit(self, *, name: str = None, color: Union[int, str] = None, permissions: int = None, position: int = None, hoist: bool = None, mentionable: bool = None):
        """Edits the role."""
        payload = {}
        if name is not None: payload['name'] = name
        if color is not None:
             if isinstance(color, int):
                 payload['color'] = f'#{color:06x}'
             else:
                 payload['color'] = color
                 
        if permissions is not None: payload['permissions'] = permissions
        if position is not None: payload['position'] = position
        if hoist is not None: payload['hoist'] = hoist
        if mentionable is not None: payload['mentionable'] = mentionable
        
        await self._state.http.edit_role(self.guild.id, self.id, **payload)

    async def delete(self):
        """Deletes the role."""
        await self._state.http.delete_role(self.guild.id, self.id)

class Guild(Snowflake):
    """Represents a Velmu Guild (Server)."""
    
    __slots__ = (
        '_state', 'id', 'name', 'icon', 'owner_id', 'region', 
        'afk_channel_id', 'afk_timeout', 'member_count', 
        'verification_level', 'default_message_notifications',
        'explicit_content_filter', 'emojis', 'features',
        'mfa_level', 'application_id', 'system_channel_id',
        'rules_channel_id', 'joined_at', 'large', 'unavailable',
        'member_count', '_channels', '_members', '_roles'
    )
    
    def __init__(self, state: 'ConnectionState', data: dict):
        self._state = state
        self.id = data.get('id')
        self._channels: Dict[str, 'Channel'] = {}
        self._members: Dict[str, Member] = {}
        self._roles: Dict[str, Role] = {}
        self._update(data)
        
    def _update(self, data: dict):
        self.name = data.get('name')
        self.icon = data.get('icon')
        self.owner_id = data.get('ownerId')
        self.member_count = data.get('memberCount', 0)
        self.region = data.get('region')
        self.afk_channel_id = data.get('afkChannelId')
        self.afk_timeout = data.get('afkTimeout')
        self.verification_level = data.get('verificationLevel')
        self.default_message_notifications = data.get('defaultMessageNotifications')
        self.explicit_content_filter = data.get('explicitContentFilter')
        self.features = data.get('features', [])
        self.mfa_level = data.get('mfaLevel')
        self.application_id = data.get('applicationId')
        self.system_channel_id = data.get('systemChannelId')
        self.rules_channel_id = data.get('rulesChannelId')
        self.large = data.get('large', False)
        self.unavailable = data.get('unavailable', False)
        
        # Joined At
        if data.get('joinedAt'):
             self.joined_at = parse_time(data.get('joinedAt'))
    
        # Roles
        if 'roles' in data:
            self._roles.clear() 
            for r_data in data['roles']:
                role = Role(self._state, r_data, self)
                self._roles[role.id] = role

    @property
    def icon_url(self) -> Optional[str]:
        if self.icon:
             if self.icon.startswith('http'):
                 return self.icon
             return None 
        return None
        
    @property
    def roles(self) -> List[Role]:
        """Returns a list of roles in the guild."""
        return list(self._roles.values())

    @property
    def channels(self) -> List['Channel']:
        return list(self._channels.values())

    @property
    def members(self) -> List[Member]:
        return list(self._members.values())

    @property
    def text_channels(self) -> List['Channel']:
        """Returns a list of text channels in the guild."""
        return [c for c in self.channels if str(c.type) == 'TEXT']

    @property
    def voice_channels(self) -> List['Channel']:
        """Returns a list of voice channels in the guild."""
        return [c for c in self.channels if str(c.type) == 'AUDIO' or str(c.type) == 'VOICE']

    @property
    def owner(self) -> Optional[Member]:
        return self.get_member(self.owner_id)

    def get_member(self, user_id: str) -> Optional[Member]:
        return self._members.get(user_id)

    async def fetch_member(self, user_id: str) -> Member:
        data = await self._state.http.get_member(self.id, user_id)
        member = Member(self._state, data, self)
        self._members[user_id] = member
        return member

    def get_role(self, role_id: str) -> Optional[Role]:
        return self._roles.get(role_id)
        
    def get_channel(self, channel_id: str) -> Optional['Channel']:
        return self._channels.get(channel_id)

    async def edit(self, *, name: str = None, icon: Optional[bytes] = None):
        """Edits the guild."""
        payload = {}
        if name is not None:
             payload['name'] = name
        
        if payload:
            await self._state.http.edit_guild(self.id, **payload)

    async def create_text_channel(self, name: str, category: Optional[Union['Channel', str]] = None, overwrites: list = None) -> 'Channel':
        """Creates a text channel in the guild."""
        from .channel import Channel, ChannelType
        
        category_id = None
        if category:
            if isinstance(category, str):
                category_id = category
            elif hasattr(category, 'id'):
                category_id = category.id
                
        data = await self._state.http.create_channel(self.id, name, ChannelType.GUILD_TEXT, category_id, overwrites)
        channel = Channel(self._state, data, self)
        self._channels[channel.id] = channel
        return channel

    async def create_voice_channel(self, name: str, category: Optional[Union['Channel', str]] = None) -> 'Channel':
        """Creates a voice channel in the guild."""
        from .channel import Channel, ChannelType
        
        category_id = None
        if category:
            if isinstance(category, str):
                category_id = category
            elif hasattr(category, 'id'):
                category_id = category.id

        data = await self._state.http.create_channel(self.id, name, ChannelType.GUILD_VOICE, category_id)
        channel = Channel(self._state, data, self)
        self._channels[channel.id] = channel
        return channel

    async def create_category(self, name: str) -> 'Channel':
        """Creates a category in the guild."""
        from .channel import Channel
        data = await self._state.http.create_category(self.id, name)
        # Category returns data similar to channel
        channel = Channel(self._state, data, self)
        self._channels[channel.id] = channel
        return channel

    # Moderation
    async def kick(self, user: Snowflake, *, reason: Optional[str] = None):
        """Kicks a user from the guild."""
        await self._state.http.kick_member(self.id, user.id)

    async def ban(self, user: Snowflake, *, reason: Optional[str] = None):
        """Bans a user from the guild."""
        await self._state.http.ban_member(self.id, user.id)

    async def unban(self, user: Snowflake, *, reason: Optional[str] = None):
        """Unbans a user from the guild."""
        await self._state.http.unban_member(self.id, user.id)

    async def bans(self):
        """Returns a list of bans."""
        return await self._state.http.get_bans(self.id)

    async def bans(self):
        """Returns a list of bans."""
        return await self._state.http.get_bans(self.id)

    async def create_role(self, name: str, color: int = 0, permissions=None, hoist=False, mentionable=False):
        """Creates a new role."""
        # Backend creates a default role, so we must edit it immediately
        data = await self._state.http.create_role(self.id, name)
        role = Role(self._state, data, self)
        self._roles[role.id] = role
        
        # Apply parameters
        await role.edit(
            name=name,
            color=color,
            permissions=permissions,
            hoist=hoist,
            mentionable=mentionable
        )
        return role

    def __repr__(self):
        return f'<Guild id={self.id} name={self.name!r} chunked={len(self.members)}/{self.member_count}>'
