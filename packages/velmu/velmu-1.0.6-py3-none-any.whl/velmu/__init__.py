"""
Velmu SDK

The official Python SDK for building bots on Velmu.

Quick Start
-----------
```python
import velmu
from velmu.ext import commands

intents = velmu.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot ready: {bot.user.username}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run('YOUR_TOKEN')
```
"""

# Core
from .client import Client
from .flags import Intents
from .api import HTTPClient
# Models
from .models import (
    BaseModel,
    User,
    Member,
    Guild,
    Channel,
    Message,
    Interaction,
    PartialMessageable,
    Embed,
    Role,
    File
)

# Exceptions
from .errors import (
    VelmuException,
    HTTPException,
    Forbidden,
    NotFound,
    RateLimited,
    VelmuServerError,
    LoginFailure,
    GatewayError,
    CommandError,
    # MissingRequiredArgument, # These are usually in ext.commands, but okay if aliased
)

# Alias old names for compatibility if needed, or stick to new structure
ServerError = VelmuServerError

__title__ = 'velmu'
__author__ = 'Velmu'
__license__ = 'MIT'
__copyright__ = 'Copyright 2024-2026 Velmu'
from ._version import __version__
print(f"📦 Velmu SDK Loaded: v{__version__} from {__file__}")


__all__ = [
    # Core
    'Client',
    'Intents',
    'Embed',
    'File',
    'HTTPClient',
    
    # Models
    'BaseModel',
    'User',
    'Member',
    'Guild',
    'Channel',
    'Message',
    'Interaction',
    'PartialMessageable',
    'Role',
    
    # Exceptions
    'VelmuException',
    'HTTPException',
    'Forbidden',
    'NotFound',
    'RateLimited',
    'ServerError',
    'LoginFailure',
    'GatewayError',
    'CommandError',
    'MissingRequiredArgument',
    'BadArgument',
    'CheckFailure',
    'CommandNotFound',
    'CommandOnCooldown',
]
