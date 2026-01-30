"""
velmu.client
~~~~~~~~~~~~

The main Client class.
"""
import asyncio
import logging
import signal
import sys
import aiohttp
from typing import Optional, List, Any, Callable, Coroutine

from .api import HTTPClient
from .gateway import VelmuGateway
from .state import ConnectionState
from .flags import Intents
from .models import User, Guild
from .models.activity import Activity, ActivityType
from .errors import LoginFailure, GatewayError

_log = logging.getLogger(__name__)

class Client:
    """The client that connects to Velmu.
    
    Attributes
    ----------
    loop : asyncio.AbstractEventLoop
        The event loop.
    intents : Intents
        The intents flags.
    user : Optional[User]
        The connected user.
    """

    def __init__(self, intents: Optional[Intents] = None, **options: Any):
        self.intents = intents or Intents.default()
        
        self.http = HTTPClient()
        self._connection = ConnectionState(dispatch=self.dispatch, http=self.http)
        
        self._gateway: Optional[VelmuGateway] = None
        self._closed = False
        self._ready = asyncio.Event()
        
        # Event handlers storage
        self._events = {}
        self.extra_events = {} # For extensions

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_running_loop()

    @property
    def user(self) -> Optional[User]:
        return self._connection.user
    
    @property
    def guilds(self) -> List[Guild]:
        return list(self._connection._guilds.values())

    @property
    def users(self) -> List[User]:
        return list(self._connection._users.values())

    @property
    def latency(self) -> float:
        return self._gateway.latency if self._gateway else 0.0

    # --- Event Registry ---

    def event(self, coro: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        """Decorator to register an event."""
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Events must be coroutines.')
        
        name = coro.__name__
        if name not in self._events:
            self._events[name] = []
        
        self._events[name].append(coro)
        _log.debug(f'Registered event: {name}')
        return coro

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any):
        """Dispatches an event."""
        _log.debug(f'Dispatching: {event_name}')
        
        # Normalize event name
        if event_name == 'MESSAGE_CREATE':
            normalized_name = 'message'
        elif event_name == 'GUILD_CREATE':
            normalized_name = 'guild_available'
        elif event_name == 'MESSAGE_DELETE':
            normalized_name = 'message_delete'
            # Try to resolve message from cache to pass object instead of dict
            if args and isinstance(args[0], dict):
                payload = args[0]
                message_id = payload.get('id')
                cached_message = self._connection._get_message(message_id) # FIX: Fetch from cache
                if cached_message:
                    cached_message.deleter_id = payload.get('deleterId')
                    args = (cached_message,)
        elif event_name == 'INTERACTION_CREATE':
            normalized_name = 'interaction'
        else:
            normalized_name = event_name.lower()

        # Event Parsing
        if normalized_name == 'ready':
            self._ready.set()
            args = ()
        elif normalized_name == 'message':
            # Parse raw dict into Message object
            if args and isinstance(args[0], dict):
                # Use store_message to cache it automatically!
                msg_data = args[0]
                channel_id = msg_data.get('channelId')
                cached_channel = self._connection.get_channel(channel_id)
                if not cached_channel:
                    pass
                else:
                    pass
                    
                message = self._connection.store_message(msg_data)
                args = (message,)
        elif normalized_name == 'guild_available':
             if args and isinstance(args[0], dict):
                # Cache Population
                guild_data = args[0]
                # _log.info(f"Received GUILD_AVAILABLE for {guild_data.get('id')}")
                
                guild = self._connection.store_guild(guild_data)
                
                # Cache Channels (Orphans)
                channels = guild_data.get('channels') or guild_data.get('Channels') or []
                if channels:
                    _log.debug(f"Caching {len(channels)} orphan channels for guild {guild.id}")
                    for channel_data in channels:
                        channel_data['guildId'] = guild.id
                        self._connection.store_channel(channel_data)
                
                # Cache Categories and their Channels
                categories = guild_data.get('categories') or []
                if categories:
                    _log.debug(f"Caching {len(categories)} categories for guild {guild.id}")
                    for cat_data in categories:
                        cat_data['guildId'] = guild.id
                        # Store Category itself as a channel
                        self._connection.store_channel(cat_data)
                        
                        # Store sub-channels
                        sub_channels = cat_data.get('channels') or []
                        # print(f"[SDK DEBUG]   Category {cat_data.get('name')} has {len(sub_channels)} sub-channels")
                        for sub in sub_channels:
                            sub['guildId'] = guild.id
                            sub['categoryId'] = cat_data.get('id') # Ensure linkage
                            self._connection.store_channel(sub)

                # Cache Members (Users)
                members = guild_data.get('members') or []
                if members:
                    for member_data in members:
                        self._connection.store_member(guild, member_data)

                # Cache Presences
                presences = guild_data.get('presences') or []
                if presences:
                    _log.info(f"Caching {len(presences)} presences for guild {guild.id}")
                    for p in presences:
                        # p: { user: {id: ...}, status: ... }
                        user_id = p.get('user', {}).get('id')
                        status = p.get('status')
                        if user_id:
                            member = guild.get_member(user_id)
                            if member:
                                member.status = status
                            
                            # Also update global user
                            user = self._connection.get_user(user_id)
                            if user:
                                user.status = status

                args = (guild,)

        elif normalized_name == 'message_delete':
            # args[0] is likely { id: "...", channelId: "...", guildId: "..." }
            # We pass it as is, or wrap it?
            # Let's wrap it in a lightweight object or just pass dict for now to be safe
            pass

        # --- Modular Event Handling ---
        
        elif normalized_name == 'guild_update':
             if args and isinstance(args[0], dict):
                before, after = self._connection.parse_guild_update(args[0])
                if after:
                    self.dispatch('guild_update', before, after)
                return

        # --- Modular Event Handling ---
        
        elif normalized_name == 'channel_create':
             if args and isinstance(args[0], dict):
                channel = self._connection.parse_channel_create(args[0])
                args = (channel,) if channel else ()
        
        elif normalized_name == 'channel_update':
             if args and isinstance(args[0], dict):
                before, after = self._connection.parse_channel_update(args[0])
                if after:
                    self.dispatch('channel_update', before, after)
                return
                
        elif normalized_name == 'channel_delete':
             if args and isinstance(args[0], dict):
                channel = self._connection.parse_channel_delete(args[0])
                args = (channel,) if channel else (args[0],)

        elif normalized_name == 'guild_member_add':
             if args and isinstance(args[0], dict):
                member = self._connection.parse_guild_member_add(args[0])
                if member:
                    self.dispatch('member_join', member)
                else:
                     import logging
                     logging.getLogger('velmu.client').error(f"Failed to parse Member from GUILD_MEMBER_ADD: {args[0]}")
                
                return 

        elif normalized_name == 'guild_member_remove':
             if args and isinstance(args[0], dict):
                member = self._connection.parse_guild_member_remove(args[0])
                if member:
                    # FIX: Map to 'member_remove'
                    self.dispatch('member_remove', member)
                return 

        elif normalized_name == 'guild_member_update':
             if args and isinstance(args[0], dict):
                before, after = self._connection.parse_guild_member_update(args[0])
                if after:
                    self.dispatch('member_update', before, after)
                return

        elif normalized_name == 'guild_ban_add':
             if args and isinstance(args[0], dict):
                res = self._connection.parse_guild_ban_add(args[0])
                if res:
                    guild, user = res
                    self.dispatch('member_ban', guild, user)
                return

        elif normalized_name == 'guild_ban_remove':
             if args and isinstance(args[0], dict):
                res = self._connection.parse_guild_ban_remove(args[0])
                if res:
                    guild, user = res
                    self.dispatch('member_unban', guild, user)
                return

        elif normalized_name == 'guild_role_create':
             if args and isinstance(args[0], dict):
                role = self._connection.parse_guild_role_create(args[0])
                args = (role,) if role else ()

        elif normalized_name == 'guild_role_update':
             if args and isinstance(args[0], dict):
                before, after = self._connection.parse_guild_role_update(args[0])
                if after:
                    self.dispatch('role_update', before, after)
                return
        
        elif normalized_name == 'user_update':
             if args and isinstance(args[0], dict):
                before, after = self._connection.parse_user_update(args[0])
                if after:
                     self.dispatch('user_update', before, after)
                return

        elif normalized_name == 'guild_role_delete':
             if args and isinstance(args[0], dict):
                role = self._connection.parse_guild_role_delete(args[0])
                args = (role,) if role else (args[0],)

        elif normalized_name == 'guild_roles_position_update':
             if args and isinstance(args[0], dict):
                roles = self._connection.parse_guild_roles_position_update(args[0])
                # Dispatch 'guild_role_update' for each? Or a bulk event?
                # Discord.py usually dispatches role_update for each.
                # Let's dispatch a custom 'guild_roles_position_update' with list
                args = (roles,) if roles else ()

        elif normalized_name == 'presence_update':
             if args and isinstance(args[0], dict):
                user = self._connection.parse_presence_update(args[0])
                args = (user,) if user else (args[0],)

        elif normalized_name == 'channel_update_permissions':
             if args and isinstance(args[0], dict):
                 channel = self._connection.parse_channel_update_permissions(args[0])
                 # Just trigger generic channel_update or specific?
                 # channel_update is fine
                 args = (channel,) if channel else ()

        elif normalized_name == 'message_reaction_add':
             if args and isinstance(args[0], dict):
                # Dispatch RAW first (always)
                self.dispatch('raw_reaction_add', args[0])
                
                reaction, user = self._connection.parse_message_reaction_add(args[0])
                if reaction:
                    self.dispatch('reaction_add', reaction, user)
                return

        elif normalized_name == 'interaction':
             if args and isinstance(args[0], dict):
                 interaction = self._connection.parse_interaction_create(args[0])
                 args = (interaction,)

        elif normalized_name == 'message_reaction_remove':
             if args and isinstance(args[0], dict):
                self.dispatch('raw_reaction_remove', args[0])
             normalized_name = 'reaction_remove'
             pass
        
        # --- Dispatch to Waiters (for wait_for) ---
        if hasattr(self, '_waiters') and normalized_name in self._waiters:
            waiters = self._waiters[normalized_name]
            # Copy list to allow removal during iteration
            for i, (future, check) in enumerate(waiters[:]):
                try:
                    # Check predicate
                    if check(*args):
                        future.set_result(args[0] if len(args) == 1 else args)
                        waiters.remove((future, check))
                except Exception as e:
                    future.set_exception(e)
                    if (future, check) in waiters:
                        waiters.remove((future, check))

        method_name = 'on_' + normalized_name
        
        # Internal listeners
        listeners = self._events.get(method_name, [])
        if listeners:
            for listener in listeners:
                self.loop.create_task(listener(*args, **kwargs))
        
        # Class listeners (subclassing Client)
        try:
            class_method = getattr(self, method_name)
            if class_method and class_method not in listeners:
                self.loop.create_task(class_method(*args, **kwargs))
        except AttributeError:
            pass

    async def wait_until_ready(self):
        """Wait until the client's internal cache is ready."""
        await self._ready.wait()

    async def wait_for(self, event: str, *, check: Optional[Callable[..., bool]] = None, timeout: Optional[float] = None) -> Any:
        """Waits for a WebSocket event to be dispatched."""
        future = self.loop.create_future()
        if check is None:
            def _check(*args):
                return True
            check = _check

        event_name = event.lower()
        
        if not hasattr(self, '_waiters'):
            self._waiters = {}

        if event_name not in self._waiters:
            self._waiters[event_name] = []
        
        self._waiters[event_name].append((future, check))
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            if event_name in self._waiters:
                try:
                    self._waiters[event_name].remove((future, check))
                except ValueError:
                    pass
            raise


    async def on_error(self, event_method: str, *args: Any, **kwargs: Any):
        """Default error handler."""
        print(f"Error in {event_method}:", file=sys.stderr)
        import traceback
        traceback.print_exc()

    # --- Lifecycle ---

    async def login(self, token: str):
        """Logs in the client."""
        _log.info('Logging in...')
        await self.http.static_login(token)
        
        data = None
        try:
            data = await self.http.get_me()
        except Exception as e:
            _log.error(f"Login HTTP call failed: {e}")
            raise LoginFailure(f"Login failed: {e}")

        if data:
            self._connection.user = self._connection.store_user(data)
        else:
            raise LoginFailure("Login failed: No data received from get_me")

    async def connect(self, reconnect: bool = True):
        """Connects to the Gateway."""
        if self._closed:
            return
            
        from .config import GATEWAY_URL
        self._gateway = VelmuGateway(self._connection, self.http._token, self.intents)
        
        try:
            await self._gateway.connect(GATEWAY_URL)
        except Exception as e:
            await self.close()
            raise GatewayError(f"Connection failed: {e}")

    async def start(self, token: str, *, reconnect: bool = True):
        """Starts the client."""
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(self, token: str, **kwargs: Any):
        """Blocking call to run the bot."""
        async def runner():
            try:
                await self.start(token, **kwargs)
            finally:
                if not self._closed:
                    await self.close()

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Handle Ctrl+C
        try:
            # Only works if loop is running? No, add_signal_handler works on loop object.
            # But get_running_loop() failed in self.loop property.
            # So we use our local 'loop' variable.
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.close()))
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.close()))
        except (NotImplementedError, AttributeError):
            pass # Windows

        try:
            loop.run_until_complete(runner())
        except KeyboardInterrupt:
            pass
        finally:
            _log.info("Client cleanup...")
            # loop.close() # Optional, strict cleanup

    async def close(self):
        """Closes the client."""
        if self._closed:
            return
            
        self._closed = True
        
        if self._gateway:
            await self._gateway.close()
            
        await self.http.close()
        _log.info("Client closed.")

    async def wait_until_ready(self):
        await self._ready.wait()

    async def __aenter__(self):
        # Ensure HTTP session is created if we are entering context
        if self.http._session is None:
             self.http._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if not self._closed:
            await self.close()
        
    # --- Methods ---
    
    def get_channel(self, id: str):
        return self._connection.get_channel(id)

    def get_guild(self, id: str):
        return self._connection.get_guild(id)

    def get_user(self, id: str):
        return self._connection.get_user(id)
        
    async def fetch_user(self, id: str):
        data = await self.http.get_user(id)
        return self._connection.store_user(data)
        
    async def fetch_guild(self, id: str):
        data = await self.http.get_guild(id)
        return self._connection.store_guild(data)
        
    async def fetch_channel(self, id: str):
        data = await self.http.get_channel(id)
        return self._connection.store_channel(data)

    async def change_presence(self, *, status: Optional[str] = None, activity: Optional[Any] = None, afk: bool = False):
        """Changes the client's presence.

        Parameters
        ----------
        status: Optional[:class:`str`]
            The status to change to. Can be 'online', 'idle', 'dnd', 'invisible'.
            If None, the current status is preserved.
        activity: Optional[:class:`Activity`]
            The activity to change to.
        afk: :class:`bool`
            Whether the client is AFK.
        """
        if self._gateway is None:
            raise GatewayError("Not connected to Gateway")
            
        # Validate Status
        valid_statuses = ['online', 'idle', 'dnd', 'invisible']
        if status and status not in valid_statuses:
             raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

        # Current status preservation logic could be added here if we tracked it locally in Client
        # For now, we assume explicit intent or default 'online' in gateway.

        activities = []
        if activity:
            activities.append(activity.to_dict())

        await self._gateway.update_presence(status=status or 'online', activities=activities, afk=afk)

