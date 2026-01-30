"""
Velmu Intent Flags

Bitfield flags for Gateway intents.
"""


class BaseFlags:
    """Base class for bitfield flags."""
    
    def __init__(self, value=0):
        self.value = value

    def __getattr__(self, name):
        # Automate property generation for uppercase bit constants
        # If we have a constant 'ADMINISTRATOR', flag.administrator returns (value & ADMINISTRATOR) != 0
        const_name = name.upper()
        if hasattr(self.__class__, const_name):
            val = getattr(self.__class__, const_name)
            if isinstance(val, int):
                return (self.value & val) == val
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name == 'value':
            super().__setattr__(name, value)
            return

        const_name = name.upper()
        if hasattr(self.__class__, const_name):
            val = getattr(self.__class__, const_name)
            if isinstance(val, int):
                self._set_flag(val, value)
                return
        super().__setattr__(name, value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, int) and not name.startswith('_'):
                yield name, (self.value & value) == value
    
    def __repr__(self):
        enabled = [name for name, enabled in self if enabled]
        return f'<{self.__class__.__name__} value={self.value} enabled={enabled}>'

    def _set_flag(self, flag, value):
        if value:
            self.value |= flag
        else:
            self.value &= ~flag


class Intents(BaseFlags):
    """Gateway intents for subscribing to events.
    
    Intents control which events your bot receives from the Gateway.
    Some intents are **privileged** and must be enabled in the Developer Portal.
    
    Privileged Intents
    ------------------
    - GUILD_MEMBERS (1 << 1): Required for member join/leave events
    - GUILD_PRESENCES (1 << 8): Required for presence updates
    - MESSAGE_CONTENT (1 << 15): Required to read message content
    
    Example
    -------
    ```python
    # Default intents (most common use case)
    intents = Intents.default()
    
    # Enable a privileged intent
    intents.message_content = True
    intents.members = True
    
    # All intents (requires all privileged intents enabled in portal)
    intents = Intents.all()
    ```
    """
    
    # Guild-related
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1  # PRIVILEGED
    GUILD_MODERATION = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8  # PRIVILEGED
    
    # Message-related
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    
    # DM-related
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    
    # Content
    MESSAGE_CONTENT = 1 << 15  # PRIVILEGED
    
    # Scheduled Events
    GUILD_SCHEDULED_EVENTS = 1 << 16
    
    # Auto Moderation
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21

    # =========================================
    # Factory Methods
    # =========================================

    @classmethod
    def default(cls) -> 'Intents':
        """Create intents with common non-privileged intents enabled.
        
        Includes: GUILDS, GUILD_MESSAGES, GUILD_MESSAGE_REACTIONS,
        DIRECT_MESSAGES, DIRECT_MESSAGE_REACTIONS
        """
        self = cls(0)
        self.value = (
            cls.GUILDS |
            cls.GUILD_MESSAGES |
            cls.GUILD_MESSAGE_REACTIONS |
            cls.DIRECT_MESSAGES |
            cls.DIRECT_MESSAGE_REACTIONS
        )
        return self

    @classmethod
    def all(cls) -> 'Intents':
        """Create intents with ALL intents enabled.
        
        ⚠️ Warning: This includes privileged intents that must be
        enabled in the Developer Portal.
        """
        self = cls(0)
        all_bits = 0
        for name, value in cls.__dict__.items():
            if isinstance(value, int) and not name.startswith('_'):
                all_bits |= value
        self.value = all_bits
        return self
    
    @classmethod
    def none(cls) -> 'Intents':
        """Create intents with no intents enabled."""
        return cls(0)
    
    @classmethod
    def privileged(cls) -> 'Intents':
        """Create intents with only privileged intents enabled."""
        self = cls(0)
        self.value = cls.GUILD_MEMBERS | cls.GUILD_PRESENCES | cls.MESSAGE_CONTENT
        return self

