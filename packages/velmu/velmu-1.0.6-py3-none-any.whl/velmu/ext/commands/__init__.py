"""
Velmu Commands Extension

Provides command handling for Velmu bots.

Example
-------
```python
from velmu.ext import commands

bot = commands.Bot(command_prefix='+')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run('TOKEN')
```
"""

from .core import (
    Bot,
    Context,
    Command,
    Group,
    Cog,
    command,
    group,
    cooldown,
    CooldownMapping
)

from ...errors import (
    CommandError,
    MissingRequiredArgument,
    BadArgument,
    CheckFailure,
    CommandNotFound,
    CommandOnCooldown
)

from .checks import check, has_permissions, is_owner
from .converters import (
    Converter, 
    MemberConverter, 
    ChannelConverter,
    UserConverter,
    RoleConverter,
    GuildConverter,
    MessageConverter,
    InviteConverter
)

__all__ = [
    'Bot',
    'Context',
    'Command',
    'Cog',
    'command',
    'cooldown',
    'CooldownMapping',
    'check',
    'has_permissions',
    'is_owner',
    'Converter',
    'MemberConverter',
    'ChannelConverter',
    'UserConverter',
    'RoleConverter',
    'GuildConverter',
    'MessageConverter',
    'InviteConverter',
    'CommandError',
    'MissingRequiredArgument',
    'BadArgument',
    'CheckFailure',
    'CommandOnCooldown',
]
