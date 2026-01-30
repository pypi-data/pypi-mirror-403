"""
velmu.models.channel
~~~~~~~~~~~~~~~~~~~~

Channel and Message models.
"""
from typing import Optional, List, Union, TYPE_CHECKING
from ..abc import Snowflake, Messageable
from ..utils import parse_time
from .user import User, Member
import asyncio

if TYPE_CHECKING:
    from ..state import ConnectionState
    from .guild import Guild

class ChannelType:
    GUILD_TEXT = 'TEXT'
    DM = 'DM'
    GUILD_VOICE = 'AUDIO'
    GROUP_DM = 'GROUP_DM'
    GUILD_CATEGORY = 'CATEGORY'

class HistoryIterator:
    """Async iterator for channel history."""
    
    def __init__(self, channel, limit=100, before=None, after=None):
        self.channel = channel
        self.limit = limit
        self.before = before
        self.after = after
        
        self._messages = asyncio.Queue()
        self._retrieve_messages = True
    
    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._messages.empty():
            if not self._retrieve_messages:
                raise StopAsyncIteration
                
            await self._fill_messages()
            
            if self._messages.empty():
                raise StopAsyncIteration
        
        return await self._messages.get()

    async def _fill_messages(self):
        if self.limit <= 0:
            self._retrieve_messages = False
            return

        fetch_limit = min(self.limit, 100) 
        
        data = await self.channel._state.http.get_messages(
            self.channel.id, 
            limit=fetch_limit, 
            before=self.before,
            after=self.after
        )
        
        
        # Handle pagination object (items + cursor)
        if isinstance(data, dict) and 'items' in data:
            data = data['items']

        if not data:
            self._retrieve_messages = False
            return

        if not isinstance(data, list):
            # API returned something unexpected (error string?)
            print(f"History Error: Expected list, got {type(data)}: {data}")
            self._retrieve_messages = False
            return
            
        found = 0
        for msg_data in data:
            self._messages.put_nowait(Message(self.channel._state, msg_data, self.channel))
            found += 1
            
            # Update pointers (Legacy: usually traverse backwards)
            self.before = msg_data['id'] 
            
        self.limit -= found
        if self.limit <= 0 or found < fetch_limit:
            self._retrieve_messages = False

class Channel(Snowflake, Messageable):
    """Represents a Guild or DM Channel."""
    
    __slots__ = ('_state', 'id', 'name', 'type', 'guild_id', 'position', 'permission_overwrites', 'category_id', 'topic', 'last_message_id', 'nsfw')
    
    def __init__(self, state: 'ConnectionState', data: dict, guild: Optional['Guild'] = None):
        self._state = state
        self.id = data.get('id')
        self._update(data, guild)
        
    def _update(self, data: dict, guild: Optional['Guild'] = None):
        self.name = data.get('name')
        self.type = data.get('type')
        self.guild_id = data.get('guildId') or data.get('serverId')
        if not self.guild_id and guild:
            self.guild_id = guild.id
        self.position = data.get('position')
        self.topic = data.get('topic')
        self.category_id = data.get('categoryId')
        self.nsfw = data.get('nsfw', False)
        
    @property
    def guild(self) -> Optional['Guild']:
        if self.guild_id:
            return self._state.get_guild(self.guild_id)
        return None
        
    @property
    def mention(self) -> str:
        return f'<#{self.id}>'

    async def _get_channel(self):
        return self

    async def send(self, content=None, *, embed=None, file=None, files=None, **kwargs):
        """Sends a message to the channel."""
        # Convert embed object to dict if necessary
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()

        # Convert components to list of dicts
        components = kwargs.get('components')
        if components:
            if hasattr(components, 'to_dict'):
                components = [components.to_dict()]
            elif isinstance(components, list):
                components = [(c.to_dict() if hasattr(c, 'to_dict') else c) for c in components]
            kwargs['components'] = components
            
        # Normalize file/files to a list
        if file is not None:
            if files is not None:
                raise ValueError("cannot pass both file and files")
            files = [file]
            
        if self.guild_id or getattr(self, 'serverId', None):
            data = await self._state.http.send_message(self.id, content, embed, files=files, **kwargs)
        else:
            # Assume Conversation/DM
            data = await self._state.http.send_conversation_message(self.id, content, embed, files=files, **kwargs)
            
        return Message(self._state, data, self)

    async def fetch_message(self, message_id: str) -> 'Message':
        data = await self._state.http.get_message(self.id, message_id)
        return Message(self._state, data, self)

    async def edit(self, *, name: str = None, topic: str = None, position: int = None, nsfw: bool = None, category: Optional[Union['Channel', str]] = None, overwrites: list = None):
        """Edits the channel."""
        payload = {}
        if name is not None: payload['name'] = name
        if topic is not None: payload['topic'] = topic
        if position is not None: payload['position'] = position
        if nsfw is not None: payload['nsfw'] = nsfw
        
        if category is not None:
             if isinstance(category, str):
                 payload['categoryId'] = category
             elif hasattr(category, 'id'):
                 payload['categoryId'] = category.id
             else:
                 payload['categoryId'] = None # Remove category

        if overwrites is not None:
            payload['overwrites'] = overwrites
            
        await self._state.http.edit_channel(self.id, **payload)

    def history(self, *, limit: int = 100, before=None, after=None) -> HistoryIterator:
        """Returns an AsyncIterator for channel history."""
        return HistoryIterator(self, limit=limit, before=before, after=after)

    async def delete(self):
        """Deletes the channel or category."""
        if self.type == ChannelType.GUILD_CATEGORY:
            await self._state.http.delete_category(self.id)
        else:
            await self._state.http.delete_channel(self.id)

    async def purge(self, *, limit: int = 100, check=None, before=None, after=None) -> List['Message']:
        """Purges a specified amount of messages from the channel."""
        iterator = self.history(limit=limit, before=before, after=after)
        ret = []
        count = 0
        to_delete = []

        async for message in iterator:
            if check is None or check(message):
                to_delete.append(message.id)
                ret.append(message)
                count += 1
            
            if len(to_delete) >= 100:
                await self._state.http.bulk_delete_messages(self.id, to_delete)
                to_delete = []

        if len(to_delete) > 0:
            if len(to_delete) == 1:
                await self._state.http.delete_message(to_delete[0])
            else:
                await self._state.http.bulk_delete_messages(self.id, to_delete)

        return ret

    async def pins(self) -> List['Message']:
        """Returns a list of pinned messages in the channel."""
        if self.guild_id or getattr(self, 'serverId', None):
             data = await self._state.http.get_channel_pins(self.id)
        else:
             data = await self._state.http.get_conversation_pins(self.id)
        
        return [Message(self._state, m, self) for m in data]

class PartialMessageable(Snowflake, Messageable):
    """Represents a partial messageable entity (e.g. just a channel ID)."""
    
    __slots__ = ('_state', 'id', 'guild_id', 'type')
    
    def __init__(self, state, id: str, guild_id: Optional[str] = None, type: Optional[int] = None):
        self._state = state
        self.id = id
        self.guild_id = guild_id
        self.type = type
        
    async def _get_channel(self):
        return self
        
    async def edit(self, **kwargs):
        """Edits the channel (Partial Support)."""
        await self._state.http.edit_channel(self.id, **kwargs)

    async def send(self, content=None, *, embed=None, file=None, files=None, **kwargs):
        """Sends a message to the channel (Partial Support)."""
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
            
        # Normalize file/files to a list
        if file is not None:
            if files is not None:
                raise ValueError("cannot pass both file and files")
            files = [file]

        # We don't know if it's a DM or Guild channel easily without type/guild_id
        # But for 'send_message' we assume standard route
        await self._state.http.send_message(self.id, content, embed, files=files, **kwargs)

    @property
    def guild(self) -> Optional['Guild']:
        if self.guild_id:
            return self._state.get_guild(self.guild_id)
        return None

from .attachment import Attachment

class Message(Snowflake):
    """Represents a Message in a Channel."""
    
    __slots__ = ('_state', 'id', 'content', 'channel_id', 'author', 'embeds', 'components', 'timestamp', 'edited_timestamp', 'tts', 'mention_everyone', 'mentions', 'mention_roles', 'attachments', 'pinned', 'webhook_id', 'type', 'activity', 'application', 'reference', 'flags', '_guild_id', 'deleter_id')
    
    def __init__(self, state: 'ConnectionState', data: dict, channel: Optional[Channel] = None):
        self._state = state
        self.id = data.get('id')
        self.channel_id = data.get('channelId')
        self._guild_id = data.get('guildId') or data.get('serverId') # Store this!
        self._update(data, channel)
        
    def _update(self, data: dict, channel: Optional[Channel] = None):
        self.content = data.get('content')
        self.timestamp = parse_time(data.get('timestamp'))
        self.pinned = data.get('isPinned', False)
        self.embeds = data.get('embeds', [])
        self.components = data.get('components', [])
        
        # Attachments
        raw_attachments = data.get('attachments', [])
        self.attachments = [Attachment(a) for a in raw_attachments]
        
        # Author
        user_data = data.get('author') or data.get('user') # Fix: Fallback to 'user' key
        if user_data:
            # 1. Try to resolve as Member if in a Guild
            guild_id = data.get('guildId') or data.get('serverId')
            member_found = None
            if guild_id:
                guild = self._state.get_guild(guild_id)
                if guild:
                    # Try cache first
                    member_found = guild.get_member(user_data.get('id'))
                    
                    # If message payload has 'member' data, OR if 'user' data contains member fields (like displayName)
                    # update/create member using the user_data itself if it looks like member data
                    member_data = data.get('member')
                    
                    # If Velmu sends member info mixed in 'user' object (like displayName), use it
                    if not member_data and 'displayName' in user_data:
                         member_data = user_data

                    if member_data:
                        full_member_data = {**member_data, 'user': user_data}
                        if member_found:
                            member_found._update_member(full_member_data)
                        else:
                            member_found = Member(self._state, full_member_data, guild)
                            guild._add_member(member_found)

            if member_found:
                self.author = member_found
            else:
                self.author = User(self._state, user_data)
        else:
            # Fallback: Try to resolve from cache using userId
            user_id = data.get('userId')
            if user_id:
                # Try global cache (User)
                self.author = self._state.get_user(user_id)
                if not self.author:
                     # Create a minimal User object if not in cache
                     self.author = User(self._state, {'id': user_id, 'username': 'Unknown User', 'discriminator': '0000'})

                # Try guild cache (Member) if available
                guild_id = data.get('guildId')
                if guild_id:
                    guild = self._state.get_guild(guild_id)
                    if guild:
                       member = guild.get_member(user_id)
                       if member: self.author = member
            else:
                self.author = None
        
    @property
    def channel(self) -> Union['Channel', 'PartialMessageable']:
        channel = self._state.get_channel(self.channel_id)
        if channel:
            return channel
        # Fallback to PartialMessageable if channel is not in cache (e.g. DMs or Cold Cache)
        # We try to infer if it's a DM or Guild Channel?
        # For edits, ID is enough.
        
        # Try to resolve guild_id from Message data or Author
        guild_id = getattr(self, '_guild_id', None)
        return PartialMessageable(self._state, self.channel_id, guild_id=guild_id)

    async def fetch(self) -> 'Message':
        """Retrieves the full message content from the API."""
        data = await self._state.http.get_message(self.id)
        self._update(data)
        return self

    @property
    def guild(self) -> Optional['Guild']:
        channel = self.channel
        return channel.guild if channel else None

    async def delete(self):
        await self._state.http.delete_message(self.id)
        
    async def edit(self, content=None, embed=None):
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
        return await self._state.http.edit_message(self.id, content, embed)
        
    async def reply(self, content=None, embed=None, file=None, files=None):
        return await self.channel.send(content, embed=embed, file=file, files=files)

    async def add_reaction(self, emoji: str):
        """Adds a reaction to the message."""
        return await self._state.http.add_reaction(self.id, emoji)

    async def remove_reaction(self, emoji: str, user_id: str = None):
        """Removes a reaction from the message."""
        return await self._state.http.remove_reaction(self.id, emoji, user_id)

    async def pin(self):
        """Pins the message."""
        await self._state.http.pin_message(self.id)
        self.pinned = True

    async def unpin(self):
        """Unpins the message."""
        await self._state.http.unpin_message(self.id)
        self.pinned = False




class Reaction:
    """Represents a reaction to a message."""
    __slots__ = ('message', 'count', 'emoji', 'me')

    def __init__(self, message, data, emoji=None):
        self.message = message
        self.emoji = emoji or data.get('emoji')
        self.count = data.get('count', 1)
        self.me = data.get('me', False)

    def is_custom_emoji(self):
        return not isinstance(self.emoji, str)

    def __repr__(self):
        return f'<Reaction emoji={self.emoji!r} count={self.count} message={self.message!r}>'
