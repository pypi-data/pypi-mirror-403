"""
Velmu Commands Framework

Extension for creating bot commands with decorators.
"""
import inspect
import asyncio
import time
from functools import wraps
from typing import Optional, Dict, Any, Callable, List

from ...models import Message, User
from ...client import Client
from ...errors import (
    CommandError,
    MissingRequiredArgument,
    BadArgument,
    CheckFailure,
    CommandOnCooldown
)


class CooldownMapping:
    """Tracks cooldowns per user/channel/guild."""
    
    def __init__(self, rate: int, per: float, type_: str = 'user'):
        self.rate = rate  # Number of uses
        self.per = per  # Per X seconds
        self.type = type_  # 'user', 'channel', 'guild'
        self._cache: Dict[str, List[float]] = {}

    def _get_key(self, ctx) -> str:
        if self.type == 'user':
            return ctx.author.id
        elif self.type == 'channel':
            return ctx.channel.id
        elif self.type == 'guild':
            return ctx.guild.id if ctx.guild else ctx.channel.id
        return ctx.author.id

    def get_retry_after(self, ctx) -> Optional[float]:
        """Check if on cooldown, return seconds to wait or None."""
        key = self._get_key(ctx)
        now = time.time()
        
        if key not in self._cache:
            self._cache[key] = []
        
        # Clean old entries
        self._cache[key] = [t for t in self._cache[key] if now - t < self.per]
        
        if len(self._cache[key]) >= self.rate:
            oldest = min(self._cache[key])
            return self.per - (now - oldest)
        
        return None

    def update(self, ctx):
        """Record a command use."""
        key = self._get_key(ctx)
        if key not in self._cache:
            self._cache[key] = []
        self._cache[key].append(time.time())


class Command:
    """Represents a bot command.
    
    Attributes
    ----------
    name : str
        The command name.
    callback : Callable
        The command function.
    help : str
        Help text for the command.
    aliases : list[str]
        Alternative names for the command.
    checks : list[Callable]
        Check functions that must pass.
    cooldown : CooldownMapping
        Cooldown tracking for the command.
    """
    
    def __init__(self, func, **kwargs):
        self.callback = func
        self.name = kwargs.get('name') or func.__name__
        
        # Docstring parsing
        doc = inspect.getdoc(func)
        self.help = kwargs.get('help') or doc or ''
        self.description = kwargs.get('description') or (doc.splitlines()[0] if doc else '')
        
        self.category = kwargs.get('category')
        self.aliases = kwargs.get('aliases', [])
        self.checks = kwargs.get('checks', [])
        self.cooldown: Optional[CooldownMapping] = None
        self.cog = None  # Set when added to a Cog

    @property
    def signature(self) -> str:
        """Returns a string representing the command signature (usage)."""
        target_func = getattr(self.callback, '__original_func__', self.callback)
        params = list(inspect.signature(target_func).parameters.values())
        
        # Skip self/ctx
        skip_count = 0
        if params and params[0].name == 'self': skip_count += 1
        if len(params) > skip_count and params[skip_count].name in ('ctx', 'context'): skip_count += 1
        params = params[skip_count:]
        
        sig_parts = []
        for param in params:
            name = param.name
            if param.kind == param.VAR_POSITIONAL:
                sig_parts.append(f"[{name}...]")
            elif param.kind == param.KEYWORD_ONLY:
                sig_parts.append(f"<{name}...>")
            elif param.default is not param.empty:
                sig_parts.append(f"[{name}={param.default}]" if param.default is not None else f"[{name}]")
            else:
                sig_parts.append(f"<{name}>")
                
        return " ".join(sig_parts)

    async def invoke(self, ctx):
        """Invoke the command with the given context."""
        # Run checks
        for check in self.checks:
            try:
                result = check(ctx) if not asyncio.iscoroutinefunction(check) else await check(ctx)
                if not result:
                    raise CheckFailure(f'Check failed for command {self.name}')
            except Exception as e:
                raise CheckFailure(str(e))
        
        # Check cooldown
        if self.cooldown:
            retry_after = self.cooldown.get_retry_after(ctx)
            if retry_after:
                raise CommandOnCooldown(retry_after)
            self.cooldown.update(ctx)
        
        # Parse arguments
        target_func = getattr(self.callback, '__original_func__', self.callback)
        sig = inspect.signature(target_func)
        params = list(sig.parameters.values())

        # Skip 'self' and 'ctx'
        skip_count = 0
        if params and params[0].name == 'self':
            skip_count += 1
        if len(params) > skip_count and params[skip_count].name in ('ctx', 'context'):
            skip_count += 1
             
        params = params[skip_count:]
        
        converted_args = []
        remaining_args = ctx.args
        
        for i, param in enumerate(params):
            # Keyword-only argument (consumes rest as one string)
            if param.kind == param.KEYWORD_ONLY:
                val = ' '.join(remaining_args[i:])
                ctx.kwargs[param.name] = val
                break
            
            # Variable Positional (*args) (consumes rest as list)
            if param.kind == param.VAR_POSITIONAL:
                rest = remaining_args[i:]
                # Apply conversion if needed
                annotation = param.annotation
                if annotation is not param.empty:
                    converted_rest = []
                    from .converters import (
                        MemberConverter, UserConverter, RoleConverter, 
                        ChannelConverter, GuildConverter, MessageConverter, InviteConverter
                    )
                    
                    for item in rest:
                        if hasattr(annotation, 'convert'):
                            converter = annotation()
                            item = await converter.convert(ctx, item)
                        else:
                            # Advanced resolution logic
                            converter = None
                            from ...models import Member, User, Role, Channel, Guild, Message, Invite
                            
                            if annotation is Member: converter = MemberConverter()
                            elif annotation is User: converter = UserConverter()
                            elif annotation is Role: converter = RoleConverter()
                            elif annotation is Channel: converter = ChannelConverter()
                            elif annotation is Guild: converter = GuildConverter()
                            elif annotation is Message: converter = MessageConverter()
                            elif annotation is Invite: converter = InviteConverter()
                            
                            if converter:
                                item = await converter.convert(ctx, item)
                            elif callable(annotation):
                                item = annotation(item)
                                
                        converted_rest.append(item)
                    converted_args.extend(converted_rest)
                else:
                    converted_args.extend(rest)
                break
            
            # Missing argument
            if i >= len(remaining_args):
                if param.default is not param.empty:
                    converted_args.append(param.default)
                    continue
                else:
                    raise MissingRequiredArgument(param)

            arg = remaining_args[i]
            

            # Type conversion
            annotation = param.annotation
            if annotation is not param.empty:
                try:
                    if hasattr(annotation, 'convert'):
                        # If the annotation itself is a Converter class
                        converter = annotation()
                        arg = await converter.convert(ctx, arg)
                    else:
                        # Check against known models mapping
                        from .converters import (
                            MemberConverter, UserConverter, RoleConverter, 
                            ChannelConverter, GuildConverter, MessageConverter, InviteConverter
                        )
                        from ...models import Member, User, Role, Channel, Guild, Message, Invite
                        
                        converter = None
                        if annotation is Member: converter = MemberConverter()
                        elif annotation is User: converter = UserConverter()
                        elif annotation is Role: converter = RoleConverter()
                        elif annotation is Channel: converter = ChannelConverter()
                        elif annotation is Guild: converter = GuildConverter()
                        elif annotation is Message: converter = MessageConverter()
                        elif annotation is Invite: converter = InviteConverter()
                        
                        if converter:
                            arg = await converter.convert(ctx, arg)
                        elif callable(annotation):
                            arg = annotation(arg)

                except Exception as e:
                    raise BadArgument(f'Could not convert "{arg}" to {getattr(annotation, "__name__", str(annotation))}')

            converted_args.append(arg)

        await self.callback(ctx, *converted_args, **ctx.kwargs)


class Group(Command):
    """Represents a group of commands that can have subcommands."""
    
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.commands: Dict[str, Command] = {}
        self.invoke_without_command = kwargs.get('invoke_without_command', False)

    def command(self, **kwargs):
        """Decorator to register a subcommand in this group."""
        def decorator(func):
            cmd = Command(func, **kwargs)
            self.add_command(cmd)
            return cmd
        return decorator

    def group(self, **kwargs):
        """Decorator to register a subgroup in this group."""
        def decorator(func):
            grp = Group(func, **kwargs)
            self.add_command(grp)
            return grp
        return decorator

    def add_command(self, command: Command):
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command

    def remove_command(self, name: str) -> Optional[Command]:
        return self.commands.pop(name, None)

    def get_command(self, name: str) -> Optional[Command]:
        return self.commands.get(name)

    async def invoke(self, ctx):
        # Look for subcommands
        if ctx.args:
            sub_name = ctx.args[0].lower()
            if sub_name in self.commands:
                sub_cmd = self.commands[sub_name]
                # Shift arguments
                ctx.invoked_subcommand = sub_cmd
                ctx.subcommand_passed = sub_name
                ctx.args = ctx.args[1:]
                await sub_cmd.invoke(ctx)
                return
        
        # If no subcommand found (or none provided)
        if self.invoke_without_command or not ctx.args:
            await super().invoke(ctx)
        else:
            # Maybe raise error? Or just show help?
            # Standard: if no subcmd and not invoke_without, it's often user error or help.
            await super().invoke(ctx)


def command(**kwargs):
    """Decorator to create a command.
    
    Parameters
    ----------
    name : str, optional
        The command name. Defaults to function name.
    help : str, optional
        Help text for the command.
    aliases : list[str], optional
        Alternative names for the command.
    cls : type, optional
        The class to use for the command. Defaults to Command.
    
    Example
    -------
    ```python
    @commands.command(name='ping', help='Check bot latency')
    async def ping(ctx):
        await ctx.send('Pong!')
    ```
    """
    cls = kwargs.pop('cls', Command)
    def decorator(func):
        return cls(func, **kwargs)
    return decorator


def group(**kwargs):
    """Decorator to create a command group.
    
    Parameters
    ----------
    name : str, optional
        The command name. Defaults to function name.
    invoke_without_command : bool, optional
        Whether to invoke the parent command if no subcommand is found. 
        Defaults to False.
    """
    kwargs.setdefault('cls', Group)
    return command(**kwargs)


def cooldown(rate: int, per: float, type_: str = 'user'):
    """Decorator to add a cooldown to a command.
    
    Parameters
    ----------
    rate : int
        Number of uses allowed.
    per : float
        Time period in seconds.
    type_ : str
        'user', 'channel', or 'guild'
    
    Example
    -------
    ```python
    @commands.command()
    @commands.cooldown(1, 60, 'user')  # Once per minute per user
    async def daily(ctx):
        await ctx.send('You got your daily reward!')
    ```
    """
    def decorator(func):
        if isinstance(func, Command):
            func.cooldown = CooldownMapping(rate, per, type_)
        else:
            # Store for later when wrapped in Command
            if not hasattr(func, '__command_cooldown__'):
                func.__command_cooldown__ = CooldownMapping(rate, per, type_)
        return func
    return decorator


class Cog:
    """Base class for command groups (Cogs).
    
    Cogs allow you to organize commands into separate files/classes.
    
    Example
    -------
    ```python
    class General(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @commands.command()
        async def ping(self, ctx):
            await ctx.send('Pong!')
    
    def setup(bot):
        bot.add_cog(General(bot))
    ```
    """
    
    def __init__(self, bot):
        self.bot = bot
        
    def get_commands(self) -> List[Command]:
        """Return all commands in this Cog."""
        cmds = []
        for name, member in inspect.getmembers(self):
            if isinstance(member, Command):
                cmds.append(member)
        return cmds

    @classmethod
    def listener(cls, name: str = None):
        """Decorator to register an event listener in a Cog.
        
        Parameters
        ----------
        name : str, optional
            Event name. Defaults to function name.
        
        Example
        -------
        ```python
        @commands.Cog.listener()
        async def on_message(self, message):
            print(f'Message: {message.content}')
        ```
        """
        def decorator(func):
            func.__is_listener__ = True
            func.__listener_name__ = name or func.__name__
            return func
        return decorator


class Context:
    """Context for a command invocation.
    
    Attributes
    ----------
    bot : Bot
        The bot instance.
    message : Message
        The message that triggered the command.
    author : User
        The message author.
    channel : Channel
        The channel the command was invoked in.
    guild : Guild
        The guild (if any).
    command : Command
        The command being invoked.
    prefix : str
        The prefix used.
    args : list[str]
        Parsed arguments.
    """
    
    def __init__(self, **kwargs):
        self.bot = kwargs.get('bot')
        self.message = kwargs.get('message')
        self.view = kwargs.get('view')
        self.prefix = kwargs.get('prefix', '')
        self.command: Optional[Command] = kwargs.get('command')
        self.invoked_with = kwargs.get('invoked_with', '')
        
        self.args: List[str] = []
        self.kwargs: Dict[str, Any] = {}
        
        self.guild = getattr(self.message, 'guild', None)
        self.channel = self.message.channel
        self.author = self.message.author
    
    @property
    def me(self) -> Optional[User]:
        """The bot's user object."""
        return self.bot.user

    async def send(self, content=None, embed=None, **kwargs) -> Message:
        """Send a message to the command channel.
        
        Parameters
        ----------
        content : str, optional
            Message content.
        embed : Embed or dict, optional
            Embed to send.
        
        Returns
        -------
        Message
            The sent message.
        """
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
        return await self.channel.send(content, embed=embed, **kwargs)

    async def reply(self, content=None, embed=None, **kwargs) -> Message:
        """Reply to the command message.
        
        Parameters
        ----------
        content : str, optional
            Message content.
        embed : Embed or dict, optional
            Embed to send.
        
        Returns
        -------
        Message
            The sent message.
        """
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
        return await self.message.reply(content, embed)


class Bot(Client):
    """Extended Client with command handling.
    
    Parameters
    ----------
    command_prefix : str or Callable
        The command prefix.
    **options
        Options passed to Client.
    
    Attributes
    ----------
    commands : dict
        Registered commands.
    cogs : dict
        Loaded Cogs.
    """
    
    def __init__(self, command_prefix, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix
        self.commands: Dict[str, Command] = {}
        self.cogs: Dict[str, Cog] = {}
        self.extensions: Dict[str, Any] = {}
        
        # Register on_message listener
        self.event(self.on_message)

    async def close(self):
        """Closes the bot and unloads extensions."""
        await super().close()
        # Add any extension cleanup here if necessary

    # =========================================
    # Extension Loading
    # =========================================

    def load_extension(self, name: str):
        """Load an extension module.
        
        Parameters
        ----------
        name : str
            Module name (e.g., 'cogs.general').
        """
        import importlib
        try:
            lib = importlib.import_module(name)
            if hasattr(lib, 'setup'):
                lib.setup(self)
            self.extensions[name] = lib
        except Exception as e:
            print(f'Failed to load extension {name}: {e}')
            raise e

    def unload_extension(self, name: str):
        """Unload an extension module.
        
        Parameters
        ----------
        name : str
            Module name.
        """
        if name in self.extensions:
            lib = self.extensions[name]
            if hasattr(lib, 'teardown'):
                lib.teardown(self)
            del self.extensions[name]

    def reload_extension(self, name: str):
        """Reload an extension module.
        
        Parameters
        ----------
        name : str
            Module name.
        """
        import importlib
        self.unload_extension(name)
        lib = importlib.import_module(name)
        importlib.reload(lib)
        self.load_extension(name)

    # =========================================
    # Cog Management
    # =========================================

    def add_cog(self, cog: Cog):
        """Add a Cog to the bot.
        
        Parameters
        ----------
        cog : Cog
            The Cog instance.
        """
        cog_name = cog.__class__.__name__
        self.cogs[cog_name] = cog
        
        # Register commands
        for name, member in inspect.getmembers(cog):
            if isinstance(member, Command):
                old_cb = member.callback
                
                # Bind to cog instance
                async def bound_callback(ctx, *args, real_cb=old_cb, cog_ref=cog, **kwargs):
                    return await real_cb(cog_ref, ctx, *args, **kwargs)
                
                bound_callback.__original_func__ = old_cb
                member.callback = bound_callback
                member.cog = cog
                
                # Apply stored cooldown if any
                if hasattr(old_cb, '__command_cooldown__'):
                    member.cooldown = old_cb.__command_cooldown__
                
                self.commands[member.name] = member
                
                # Register aliases
                for alias in member.aliases:
                    self.commands[alias] = member
                
                print(f"Registered cog command: {member.name}")

                # Handle subcommands for Groups
                if isinstance(member, Group):
                    # We already bound the group callbackAbove, but subcommands 
                    # also need binding if they were defined inside the Cog?
                    # Actually, decorators in Cogs usually just return the Command object.
                    # add_cog logic should recursively bind subcommands if they are not bound.
                    pass
        
        # Register event listeners
        for name, member in inspect.getmembers(cog):
            if hasattr(member, '__is_listener__') and member.__is_listener__:
                event_name = member.__listener_name__
                
                # Create a bound version
                async def bound_listener(*args, listener=member, cog_ref=cog, **kwargs):
                    return await listener(*args, **kwargs)
                
                if event_name not in self._events:
                    self._events[event_name] = []
                self._events[event_name].append(bound_listener)
                print(f"Registered cog listener: {event_name}")

    def remove_cog(self, name: str) -> Optional[Cog]:
        """Remove a Cog from the bot.
        
        Parameters
        ----------
        name : str
            The Cog class name.
        
        Returns
        -------
        Cog or None
            The removed Cog.
        """
        cog = self.cogs.pop(name, None)
        if cog:
            # Remove commands
            for cmd in cog.get_commands():
                self.commands.pop(cmd.name, None)
                for alias in cmd.aliases:
                    self.commands.pop(alias, None)
        return cog

    def get_cog(self, name: str) -> Optional[Cog]:
        """Get a Cog by name.
        
        Parameters
        ----------
        name : str
            The Cog class name.
        
        Returns
        -------
        Cog or None
        """
        return self.cogs.get(name)

    # =========================================
    # Command Registration
    # =========================================
         
    def command(self, **kwargs):
        """Decorator to register a command on the bot.
        
        Example
        -------
        ```python
        @bot.command(name='ping')
        async def ping(ctx):
            await ctx.send('Pong!')
        ```
        """
        def decorator(func):
            cmd = Command(func, **kwargs)
            
            # Apply stored cooldown
            if hasattr(func, '__command_cooldown__'):
                cmd.cooldown = func.__command_cooldown__
            
            self.commands[cmd.name] = cmd
            
            # Register aliases
            for alias in cmd.aliases:
                self.commands[alias] = cmd
            
            return cmd
        return decorator

    def get_command(self, name: str) -> Optional[Command]:
        """Get a command by name.
        
        Parameters
        ----------
        name : str
            Command name or alias.
        
        Returns
        -------
        Command or None
        """
        return self.commands.get(name)

    # =========================================
    # Command Processing
    # =========================================

    async def on_message(self, message: Message):
        """Handle incoming messages for commands."""
        # Ignore bots
        if message.author and message.author.bot:
            return

        await self.process_commands(message)

    async def process_commands(self, message: Message):
        """Process commands from a message.
        
        Parameters
        ----------
        message : Message
            The message to process.
        """
        content = message.content
        if not content:
            return
        
        # Check prefix
        prefix = self.command_prefix
        if callable(prefix):
            prefix = await prefix(self, message) if asyncio.iscoroutinefunction(prefix) else prefix(self, message)
        
        if not content.startswith(prefix):
            return

        # Parse command using shlex for proper quote handling
        import shlex
        try:
            # We need to handle the case where shlex fails (unclosed quotes)
            # Also, shlex.split might consume the prefix if not careful
            full_content = content[len(prefix):]
            view = shlex.split(full_content)
        except ValueError:
            # Fallback to simple split if quotes are messed up, or raise error
            # User compliant: "mal géré", so let's try to be robust or explicit
            view = content[len(prefix):].split(' ')
            
        if not view:
            return

        invoker = view[0].lower()
        args = view[1:]

        if invoker not in self.commands:
            return

        cmd = self.commands[invoker]
        ctx = Context(
            bot=self, 
            message=message, 
            view=view,
            prefix=prefix,
            command=cmd,
            invoked_with=invoker
        )
        ctx.args = args
        
        try:
            await cmd.invoke(ctx)
        except CommandError as e:
            self.dispatch('command_error', ctx, e)
        except Exception as e:
            self.dispatch('command_error', ctx, e)
            print(f'Command Error: {e}')
            import traceback
            traceback.print_exc()

    async def on_command_error(self, ctx: Context, error: Exception):
        """Default command error handler.
        
        Override this in your bot to customize error handling.
        
        Parameters
        ----------
        ctx : Context
            The command context.
        error : Exception
            The error that occurred.
        """
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"❌ Argument manquant : `{error.param.name}`")
        elif isinstance(error, CommandOnCooldown):
            await ctx.send(f"⏰ Commande en cooldown. Réessaie dans {error.retry_after:.1f}s")
        elif isinstance(error, CheckFailure):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.")
        elif isinstance(error, BadArgument):
            await ctx.send(f"❌ Argument invalide : {error}")
        else:
            await ctx.send(f"❌ Erreur : {error}")
