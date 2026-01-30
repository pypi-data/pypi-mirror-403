"""
velmu.api
~~~~~~~~~

HTTP Client implementation for Velmu.
"""
import aiohttp
import asyncio
import json
import logging
import sys
import weakref
from urllib.parse import quote as _uriquote
from typing import ClassVar, Any, Optional, Dict, Union

from .errors import (
    HTTPException,
    Forbidden,
    NotFound,
    VelmuServerError,
    RateLimited,
    LoginFailure
)
from ._version import __version__
from .config import API_BASE_URL

_log = logging.getLogger(__name__)

class Route:
    """Represents an API Route.
    
    Attributes
    ----------
    method : str
        HTTP Method (GET, POST, PUT, DELETE, PATCH).
    path : str
        API Path template.
    url : str
        Full formatted URL.
    """
    
    BASE: ClassVar[str] = API_BASE_URL

    def __init__(self, method: str, path: str, **parameters: Any):
        self.method = method
        self.path = path
        url = self.BASE + path
        if parameters:
            self.url = url.format(**{k: _uriquote(str(v)) if isinstance(v, str) else v for k, v in parameters.items()})
        else:
            self.url = url
            
        # Bucket hashing for rate limits (simulated for now)
        self.channel_id: Optional[str] = parameters.get('channel_id')
        self.guild_id: Optional[str] = parameters.get('guild_id')


class Bucket:
    """Manages rate limits for a specific route."""
    def __init__(self, key: str):
        self.key = key
        self._limit = None
        self._remaining = None
        self._reset = None
        self._lock = asyncio.Lock()
    
    @property
    def is_locked(self) -> bool:
        if self._remaining is None:
            return False
        return self._remaining == 0 and self._reset > asyncio.get_event_loop().time()
    
    async def wait(self):
        """Waits if the bucket is exhausted."""
        async with self._lock:
            if self._remaining == 0:
                current_time = asyncio.get_event_loop().time()
                wait_time = self._reset - current_time
                if wait_time > 0:
                    _log.info(f"Rate Limit Proactive: Sleeping {wait_time:.2f}s for {self.key}")
                    await asyncio.sleep(wait_time)
    
    def update(self, headers: Any):
        """Updates the bucket state from response headers."""
        try:
            self._limit = int(headers.get('X-RateLimit-Limit', 1))
            self._remaining = int(headers.get('X-RateLimit-Remaining', 1))
            # X-RateLimit-Reset is typically epoch seconds
            reset_header = headers.get('X-RateLimit-Reset')
            if reset_header:
                 # Ensure we parse it correctly (assuming standard epoch seconds)
                 self._reset = float(reset_header)
        except (ValueError, TypeError):
            pass

class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Velmu API."""

    def __init__(self, token: Optional[str] = None):
        self._token: Optional[str] = token
        self._session: Optional[aiohttp.ClientSession] = None
        self.user_agent: str = f'VelmuBot (https://github.com/velmu-dev/velmu, {__version__}) Python/{sys.version_info[0]}.{sys.version_info[1]} aiohttp/{aiohttp.__version__}'
        self._buckets: Dict[str, Bucket] = {} # Key -> Bucket

        self._global_lock = asyncio.Event()
        self._global_lock.set()

    async def static_login(self, token: str):
        self._token = token
        self._session = aiohttp.ClientSession()

    async def close(self):
        if self._session:
            await self._session.close()

    def get_bucket(self, route: Route) -> Bucket:
        key = f"{route.path}"
        if route.channel_id:
            key += f":{route.channel_id}"
        elif route.guild_id:
            key += f":{route.guild_id}"
            
        if key not in self._buckets:
            self._buckets[key] = Bucket(key)
        return self._buckets[key]

    async def request(self, route: Route, **kwargs: Any) -> Any:
        if self._session is None:
            self._session = aiohttp.ClientSession()

        # 0. Global Rate Limit Wait
        await self._global_lock.wait()

        headers: Dict[str, str] = {
            'User-Agent': self.user_agent
        }

        if self._token:
            headers['Authorization'] = f'Bot {self._token}'

        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            del kwargs['headers']

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs['json'])
            del kwargs['json']

        bucket = self.get_bucket(route)

        for attempt in range(5):
            await bucket.wait()
            await self._global_lock.wait()

            async with self._session.request(route.method, route.url, headers=headers, **kwargs) as response:
                bucket.update(response.headers)
                
                # Load data if available
                data = None
                if response.status != 204:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        data = await response.json()
                    else:
                        data = await response.text()

                # Check Success
                if 200 <= response.status < 300:
                    return data

                # Check Global Rate Limit header
                if response.headers.get('X-RateLimit-Global'):
                    self._global_lock.clear()
                    loop = asyncio.get_event_loop()
                    retry_after = float(response.headers.get('Retry-After', 1))
                    loop.call_later(retry_after, self._global_lock.set)
                    _log.warning(f"Global Rate Limit Hit! Waiting {retry_after}s")

                if response.status == 429:
                    # Specific 429 handling
                    retry_after = data.get('retry_after', 1) if isinstance(data, dict) else 1
                    
                    if response.headers.get('X-RateLimit-Global'):
                        # Already handled above
                        await self._global_lock.wait()
                    else:
                        _log.warning(f"Rate Limited on {route.path}. Retrying in {retry_after}s")
                        await asyncio.sleep(retry_after)
                    continue

                if response.status == 403:
                    raise Forbidden(response, data)
                elif response.status == 404:
                    raise NotFound(response, data)
                elif response.status >= 500:
                    raise VelmuServerError(response, data)
                else:
                    raise HTTPException(response, data)
        
        raise HTTPException(response, data)

    # --- API Methods ---
    # Organized by Resource
    
    # User
    async def get_me(self):
        """Returns the current bot user."""
        return await self.request(Route('GET', '/users/me'))

    async def get_user(self, user_id: str):
        """Returns a user by ID."""
        return await self.request(Route('GET', f'/users/{user_id}'))

    async def create_dm(self, recipient_id: str):
        """Creates a DM channel with a user."""
        # VELMU API uses /conversations for DMs
        return await self.request(Route('POST', '/conversations'), json={'targetUserId': recipient_id})

    # Guild
    async def get_guild(self, guild_id: str):
        """Returns a guild by ID."""
        return await self.request(Route('GET', f'/servers/{guild_id}'))
        
    async def get_guild_channels(self, guild_id: str):
        """Returns all channels in a guild."""
        return await self.request(Route('GET', f'/servers/{guild_id}/channels'))

    async def get_member(self, guild_id: str, user_id: str):
        """Returns a member of a guild."""
        return await self.request(Route('GET', f'/members/{guild_id}/{user_id}'))

    # Channel
    async def get_channel(self, channel_id: str):
        """Returns a channel by ID."""
        return await self.request(Route('GET', f'/channels/{channel_id}'))

    # Messages
    async def send_message(self, channel_id: str, content: Optional[str], embed: Optional[Dict], reply_to: Optional[str] = None, files: Optional[list] = None, **kwargs):
        """Sends a message to a channel."""
        payload = {}
        if content: payload['content'] = content
        if embed: payload['embed'] = embed
        if reply_to: payload['replyToId'] = reply_to
        
        # Add components if present
        if 'components' in kwargs:
            payload['components'] = kwargs['components']
        
        # If files are present, we MUST use multipart/form-data
        if files:
            form = aiohttp.FormData()
            form.add_field('payload_json', json.dumps(payload))
            
            # Backend currently supports only ONE file named 'file'
            # and validates mimetype.
            import mimetypes
            
            # Take the first file
            file = files[0]
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
                
            form.add_field('file', file.fp, filename=file.filename, content_type=mime_type)
                
            return await self.request(Route('POST', f'/channels/{channel_id}/messages'), data=form)
        else:
            return await self.request(Route('POST', f'/channels/{channel_id}/messages'), json=payload)

    async def send_conversation_message(self, conversation_id: str, content: Optional[str], embed: Optional[Dict], reply_to: Optional[str] = None, files: Optional[list] = None, **kwargs):
        """Sends a message to a DM conversation."""
        payload = {'conversationId': conversation_id}
        if content: payload['content'] = content
        if embed: payload['embed'] = embed
        if reply_to: payload['replyToId'] = reply_to

        # Add components if present
        if 'components' in kwargs:
            payload['components'] = kwargs['components']
        
        if files:
            form = aiohttp.FormData()
            form.add_field('payload_json', json.dumps(payload))
            
            import mimetypes
            file = files[0]
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = 'application/octet-stream'

            form.add_field('file', file.fp, filename=file.filename, content_type=mime_type)
            return await self.request(Route('POST', '/messages'), data=form)
        else:
            return await self.request(Route('POST', '/messages'), json=payload)

    async def get_messages(self, channel_id: str, limit: int = 50, before: Optional[str] = None, after: Optional[str] = None):
        """Returns messages from a channel."""
        params = {'limit': limit}
        if before:
            params['before'] = before
        if after:
            params['after'] = after
            
        return await self.request(Route('GET', f'/channels/{channel_id}/messages'), params=params)

    async def get_message(self, channel_id: str, message_id: str):
        """Returns a specific message."""
        return await self.request(Route('GET', f'/messages/{message_id}'))

    async def delete_message(self, message_id: str):
        """Deletes a message."""
        return await self.request(Route('DELETE', f'/messages/{message_id}'))

    async def bulk_delete_messages(self, channel_id: str, message_ids: list):
        """Deletes multiple messages at once."""
        return await self.request(Route('POST', '/messages/bulk-delete'), json={'channelId': channel_id, 'messageIds': message_ids})

    async def edit_message(self, message_id: str, content: Optional[str] = None, embed: Optional[Union[Dict, Any]] = None, components: Optional[list] = None):
        """Edits a message."""
        payload = {}
        if content is not None: payload['content'] = content
        
        # Auto-convert Embed object
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
            
        if embed is not None: payload['embed'] = embed
        if components is not None: payload['components'] = components
        return await self.request(Route('PUT', f'/messages/{message_id}'), json=payload)
    
    async def add_reaction(self, message_id: str, emoji: str):
         """Adds a reaction to a message."""
         return await self.request(Route('POST', f'/messages/{message_id}/reactions'), json={'emoji': emoji})

    async def remove_reaction(self, message_id: str, emoji: str, user_id: Optional[str] = None):
        """Removes a reaction from a message.
        
        If user_id is None, removes the bot's own reaction.
        """
        params = {}
        if user_id: params['userId'] = user_id
        return await self.request(Route('DELETE', f'/messages/{message_id}/reactions/{emoji}'), params=params)

    # Pins
    async def pin_message(self, message_id: str):
        """Pins a message in its channel."""
        return await self.request(Route('PUT', f'/messages/{message_id}/pin'))

    async def unpin_message(self, message_id: str):
        """Unpins a message."""
        return await self.request(Route('DELETE', f'/messages/{message_id}/pin'))

    async def get_channel_pins(self, channel_id: str):
        """Returns all pinned messages in a channel."""
        return await self.request(Route('GET', f'/channels/{channel_id}/pins'))

    async def get_conversation_pins(self, conversation_id: str):
        """Returns all pinned messages in a conversation."""
        return await self.request(Route('GET', f'/conversations/{conversation_id}/pins'))

    # Invites
    async def get_invite(self, code: str):
        """Returns invite info."""
        return await self.request(Route('GET', f'/invites/{code}'))

    # Channel/Category Management
    async def create_channel(self, guild_id: str, name: str, type: int, category_id: str = None, permission_overwrites = None):
        """Creates a channel."""
        payload = {
            'serverId': guild_id,
            'name': name, 
            'type': type
        }
        if category_id:
            payload['categoryId'] = category_id
        if permission_overwrites:
            payload['permissionOverwrites'] = permission_overwrites
            
        return await self.request(Route('POST', '/channels'), json=payload)

    async def delete_channel(self, channel_id: str):
        """Deletes a channel."""
        return await self.request(Route('DELETE', f'/channels/{channel_id}'))

    async def create_category(self, guild_id: str, name: str):
        """Creates a new category in a guild."""
        payload = {
            'serverId': guild_id,
            'name': name
        }
        return await self.request(Route('POST', '/categories'), json=payload)

    async def delete_category(self, category_id: str):
        """Deletes a category."""
        return await self.request(Route('DELETE', f'/categories/{category_id}'))

    async def edit_channel(self, channel_id: str, **kwargs):
        """Edits channel settings."""
        return await self.request(Route('PUT', f'/channels/{channel_id}'), json=kwargs)

    async def edit_guild(self, guild_id: str, **kwargs):
        """Edits guild settings."""
        return await self.request(Route('PUT', f'/servers/{guild_id}'), json=kwargs)

    async def edit_member(self, guild_id: str, user_id: str, **kwargs):
        """Edits a member (e.g. nickname)."""
        return await self.request(Route('PUT', f'/members/{guild_id}/update/{user_id}'), json=kwargs)

    # Moderation
    async def kick_member(self, guild_id: str, user_id: str):
        """Kicks a member from the guild."""
        return await self.request(Route('DELETE', f'/members/{guild_id}/kick/{user_id}'))

    async def ban_member(self, guild_id: str, user_id: str, reason: Optional[str] = None, expires_at: Optional[str] = None):
        """Bans a member from the guild."""
        payload = {}
        if reason: payload['reason'] = reason
        if expires_at: payload['expiresAt'] = expires_at
        return await self.request(Route('POST', f'/servers/{guild_id}/bans/{user_id}'), json=payload)

    async def unban_member(self, guild_id: str, user_id: str):
        """Unbans a member."""
        return await self.request(Route('DELETE', f'/servers/{guild_id}/bans/{user_id}'))
    
    async def get_bans(self, guild_id: str):
        """Returns a list of bans for a guild."""
        return await self.request(Route('GET', f'/servers/{guild_id}/bans'))

    # Roles
    async def get_roles(self, guild_id: str):
        """Returns all roles in a guild."""
        return await self.request(Route('GET', f'/servers/{guild_id}/roles'))

    async def add_role(self, guild_id: str, user_id: str, role_id: str):
        """Assigns a role to a member."""
        return await self.request(Route('PUT', f'/members/{guild_id}/{user_id}/roles/{role_id}'))

    async def remove_role(self, guild_id: str, user_id: str, role_id: str):
        """Removes a role from a member."""
        return await self.request(Route('DELETE', f'/members/{guild_id}/{user_id}/roles/{role_id}'))

    async def create_role(self, guild_id: str, name: Optional[str] = None, color: Optional[str] = None, permissions: int = 0):
        """Creates a new role.
        
        Note: Backend might require a separate update call for properties if not supported in create.
        """
        # Current backend implementation doesn't support body in create.
        # We create then update.
        role = await self.request(Route('POST', f'/servers/{guild_id}/roles'))
        if name or color or permissions:
             role_id = role.get('id')
             if role_id:
                 payload = {}
                 if name: payload['name'] = name
                 if color: payload['color'] = color
                 if permissions: payload['permissions'] = permissions
                 return await self.edit_role(guild_id, role_id, **payload)
        return role

    async def edit_role(self, guild_id: str, role_id: str, **kwargs):
        """Edits a role's permissions or settings."""
        return await self.request(Route('PUT', f'/servers/{guild_id}/roles/{role_id}'), json=kwargs)

    async def delete_role(self, guild_id: str, role_id: str):
        """Deletes a role."""
        return await self.request(Route('DELETE', f'/servers/{guild_id}/roles/{role_id}'))
    
    async def edit_role_positions(self, guild_id: str, roles: list):
        """Updates role hierarchy positions."""
        return await self.request(Route('PUT', f'/servers/{guild_id}/roles/positions'), json={'roles': roles})
