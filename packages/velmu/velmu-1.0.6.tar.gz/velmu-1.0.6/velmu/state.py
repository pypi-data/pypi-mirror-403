"""
velmu.state
~~~~~~~~~~~

Internal state and cache management.
"""
import asyncio
import logging
from typing import Dict, Optional, TYPE_CHECKING, Deque
from collections import deque
from .models import User, Guild, Channel, Message

if TYPE_CHECKING:
    from .client import Client
    from .api import HTTPClient

_log = logging.getLogger(__name__)

class ConnectionState:
    """Manages the internal state of the client (Caches, HTTP, etc)."""
    
    def __init__(self, dispatch, http: 'HTTPClient', max_messages: int = 1000):
        self.dispatch = dispatch
        self.http = http
        self.max_messages = max_messages
        self.user: Optional[User] = None
        
        # Caches
        self._users: Dict[str, User] = {}
        self._guilds: Dict[str, Guild] = {}
        self._channels: Dict[str, Channel] = {}
        self._messages: Deque[Message] = deque(maxlen=max_messages)
        
        # We can add more caches here (roles, members, etc)

    def clear(self):
        self.user = None
        self._users = {}
        self._guilds = {}
        self._channels = {}

    # --- Cache Methods ---
    
    def store_user(self, data):
        user_id = data.get('id')
        user = self._users.get(user_id)
        if user is None:
            user = User(state=self, data=data)
            self._users[user_id] = user
        else:
            user._update(data)
        return user

    def get_user(self, id: str) -> Optional[User]:
        return self._users.get(id)

    def store_message(self, data) -> Message:
        channel_id = data.get('channelId')
        channel = self.get_channel(channel_id)
        
        message = Message(state=self, data=data, channel=channel)
        self._messages.append(message)
        return message

    def _get_message(self, message_id: str) -> Optional[Message]:
        return next((m for m in self._messages if m.id == message_id), None)

    def store_channel(self, data):
        channel_id = data.get('id')
        guild_id = data.get('guildId') or data.get('serverId')
        
        channel = self._channels.get(channel_id)
        if channel is None:
            channel = Channel(state=self, data=data)
            self._channels[channel_id] = channel
        else:
            channel._update(data)
            
        # Link to Guild
        if guild_id:
            guild = self._guilds.get(guild_id)
            if guild:
                guild._channels[channel_id] = channel
                
        return channel

    def store_member(self, guild, data):
        """Stores a Member and links it to the Guild."""
        # data is the full member object: { userId: ..., user: {...}, roles: [], ... }
        user_data = data.get('user')
        if not user_data and 'username' in data:
             # Handle flat user object if necessary (fallback)
             user_data = data
        
        if user_data:
            self.store_user(user_data)
            
        user_id = data.get('userId') or user_data.get('id')
        if not user_id:
            return None
            
        from .models import Member
        member = guild.get_member(user_id)
        if member is None:
            member = Member(state=self, data=data, guild=guild)
            guild._members[user_id] = member
        else:
            member._update(data)
            
        return member

    def get_channel(self, id: str) -> Optional[Channel]:
        return self._channels.get(id)

    def store_guild(self, data):
        guild_id = data.get('id')
        guild = self._guilds.get(guild_id)
        if guild is None:
            guild = Guild(state=self, data=data)
            self._guilds[guild_id] = guild
        else:
            guild._update(data)
        return guild

    def get_guild(self, id: str) -> Optional[Guild]:
        return self._guilds.get(id)

    # --- Event Parsers ---
    
    def parse_guild_update(self, data):
        guild_id = data.get('id')
        guild = self.get_guild(guild_id)
        if guild:
            import copy
            before = copy.copy(guild)
            guild._update(data)
            return before, guild
        return None, None

    def parse_channel_create(self, data) -> Optional[Channel]:
        return self.store_channel(data)

    def parse_channel_update(self, data) -> tuple:
        channel_id = data.get('id')
        channel = self.get_channel(channel_id)
        if channel:
            import copy
            before = copy.copy(channel)
            self.store_channel(data)
            return before, channel
        return None, None

    def parse_channel_delete(self, data) -> Optional[Channel]:
        channel_id = data.get('id')
        guild_id = data.get('guildId')
        
        channel = self._channels.pop(channel_id, None)
        
        if guild_id:
            guild = self.get_guild(guild_id)
            if guild and channel_id in guild._channels:
                del guild._channels[channel_id]
                
        return channel

    def parse_guild_member_add(self, data) -> Optional['User']: # Returns Member actually
        guild_id = data.get('guildId')
        guild = self.get_guild(guild_id)
        if guild:
            return self.store_member(guild, data)
        return None

    def parse_guild_member_remove(self, data):
        guild_id = data.get('guildId')
        user_id = data.get('userId') or data.get('user', {}).get('id')
        
        guild = self.get_guild(guild_id)
        if guild and user_id in guild._members:
            return guild._members.pop(user_id)
        return None

    def parse_guild_member_update(self, data):
        guild_id = data.get('guildId')
        user_data = data.get('user', {})
        user_id = user_data.get('id')
        
        guild = self.get_guild(guild_id)
        if guild and user_id:
            member = guild.get_member(user_id)
            if member:
                import copy
                before = copy.copy(member)
                member._update_member(data)
                return before, member
            else:
                 # Member not in cache, create it?
                 if user_data:
                     member = self.store_member(guild, data)
                     return None, member
                     
        return None, None

    def parse_guild_role_create(self, data):
        guild_id = data.get('guildId')
        role_data = data.get('role')
        
        guild = self.get_guild(guild_id)
        if guild and role_data:
            from .models.guild import Role
            role = Role(self, role_data, guild)
            guild._roles[role.id] = role
            # Also update guild's role list if it's stored separately? 
            # Guild.roles is a dict, so we are good.
            return role
        return None

    def parse_guild_role_update(self, data):
        guild_id = data.get('guildId')
        role_data = data.get('role')
        
        guild = self.get_guild(guild_id)
        if guild and role_data:
            role_id = role_data.get('id')
            role = guild.get_role(role_id)
            if role:
                import copy
                before = copy.copy(role)
                role._update(role_data)
                return before, role
        return None, None

    def parse_guild_role_delete(self, data):
        guild_id = data.get('guildId')
        role_id = data.get('roleId')
        
        guild = self.get_guild(guild_id)
        if guild and role_id in guild._roles:
            return guild._roles.pop(role_id)
        return None

    def parse_user_update(self, data):
        # Update self.user
        if self.user:
             import copy
             before = copy.copy(self.user)
             self.user._update(data)
             return before, self.user
             
        # Also update in global cache if present
        user_id = data.get('id')
        if user_id:
            user = self.get_user(user_id)
            if user:
                 user._update(data)
                 if not self.user:
                     return None, user
        return None, None

    def parse_presence_update(self, data):
        # Data: { userId, status, guildId, ... }
        user_id = data.get('userId') or data.get('user', {}).get('id')
        status = data.get('status')
        
        # 1. Update Global User
        user = self.get_user(user_id)
        if user:
            setattr(user, 'status', status)
            
        # 2. Fan-out: Update Member in ALL guilds
        if user_id:
            for guild in self._guilds.values():
                member = guild.get_member(user_id)
                if member:
                    setattr(member, 'status', status)
                    
        return user

    def parse_guild_roles_position_update(self, data):
        guild_id = data.get('guildId')
        roles_data = data.get('roles', [])
        
        guild = self.get_guild(guild_id)
        if guild:
            updated_roles = []
            for role_datum in roles_data:
                role_id = role_datum.get('id')
                role = guild.get_role(role_id)
                if role:
                    role._update(role_datum)
                    updated_roles.append(role)
            return updated_roles
        return None

    def parse_guild_ban_add(self, data):
        guild_id = data.get('guildId')
        user_data = data.get('user')
        
        guild = self.get_guild(guild_id)
        if guild and user_data:
            # We don't necessarily cache bans, but we return the user and guild info
            # so the client can dispatch 'on_member_ban(guild, user)'
            user = self.store_user(user_data)
            return guild, user
        return None

    def parse_guild_ban_remove(self, data):
        guild_id = data.get('guildId')
        user_data = data.get('user')
        
        guild = self.get_guild(guild_id)
        if guild and user_data:
            user = self.store_user(user_data)
            return guild, user
        return None

    def parse_channel_update_permissions(self, data):
        guild_id = data.get('guildId')
        channel_id = data.get('channelId')
        override = data.get('override')
        
        channel = self.get_channel(channel_id)
        if channel:
            # TODO: Update channel's internal permission overrides list if cached
            # For now return relevant info
            pass
        return channel

    def parse_message_reaction_add(self, data):
        # data: { userId, channelId, messageId, guildId, emoji: { name, id } }
        channel_id = data.get('channelId')
        message_id = data.get('messageId')
        user_id = data.get('userId')
        emoji_data = data.get('emoji')
        
        # Resolve Emoji (simplify to name/str for now if id is null)
        emoji = emoji_data.get('name') if emoji_data else None

        channel = self.get_channel(channel_id)
        if not channel:
            # Partial Channel?
            pass
            
        # Try to find message in cache
        message = self._get_message(message_id)
        if not message and channel:
             # Create partial message for reaction context
             pass

        user = self.get_user(user_id)
        if not user and data.get('guildId'):
             guild = self.get_guild(data.get('guildId'))
             if guild:
                 user = guild.get_member(user_id)
        
        if not message:
            from .models.channel import Message
            msg_data = {'id': message_id, 'channelId': channel_id, 'guildId': data.get('guildId')}
            message = Message(self, msg_data, channel)
            
        from .models.channel import Reaction
        reaction = Reaction(message, {}, emoji=emoji)
        return reaction, user

    def parse_interaction_create(self, data):
        # data is raw interaction object
        from .models import Interaction
        interaction = Interaction(self, data)
        return interaction
