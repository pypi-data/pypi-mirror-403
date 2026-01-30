"""
velmu.permissions
~~~~~~~~~~~~~~~~~

Bitfield flags for Permissions.
"""
from .flags import BaseFlags

class Permissions(BaseFlags):
    """Represents a set of permissions.
    
    The value is a bitfield integer.
    """
    
    CREATE_INSTANT_INVITE = 1 << 0
    KICK_MEMBERS = 1 << 1
    BAN_MEMBERS = 1 << 2
    ADMINISTRATOR = 1 << 3
    MANAGE_CHANNELS = 1 << 4
    MANAGE_GUILD = 1 << 5
    ADD_REACTIONS = 1 << 6
    PRIORITY_SPEAKER = 1 << 8
    STREAM = 1 << 9
    VIEW_CHANNEL = 1 << 10
    SEND_MESSAGES = 1 << 11
    SEND_TTS_MESSAGES = 1 << 12
    MANAGE_MESSAGES = 1 << 13
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    READ_MESSAGE_HISTORY = 1 << 16
    MENTION_EVERYONE = 1 << 17
    USE_EXTERNAL_EMOJIS = 1 << 18
    VIEW_GUILD_INSIGHTS = 1 << 19
    CONNECT = 1 << 20
    SPEAK = 1 << 21
    MUTE_MEMBERS = 1 << 22
    DEAFEN_MEMBERS = 1 << 23
    MOVE_MEMBERS = 1 << 24
    USE_VAD = 1 << 25
    CHANGE_NICKNAME = 1 << 26
    MANAGE_NICKNAMES = 1 << 27
    MANAGE_ROLES = 1 << 28
    MANAGE_WEBHOOKS = 1 << 29
    MANAGE_EMOJIS_AND_STICKERS = 1 << 30
    USE_APPLICATION_COMMANDS = 1 << 31
    REQUEST_TO_SPEAK = 1 << 32
    MANAGE_EVENTS = 1 << 33
    MANAGE_THREADS = 1 << 34
    CREATE_PUBLIC_THREADS = 1 << 35
    CREATE_PRIVATE_THREADS = 1 << 36
    USE_EXTERNAL_STICKERS = 1 << 37
    SEND_MESSAGES_IN_THREADS = 1 << 38
    USE_EMBEDDED_ACTIVITIES = 1 << 39
    MODERATE_MEMBERS = 1 << 40
    
    @classmethod
    def all(cls):
        """A helper method that sets all permissions to True."""
        all_perms = 0
        for name, value in cls.__dict__.items():
            if isinstance(value, int) and not name.startswith('_'):
                all_perms |= value
        return cls(all_perms)

    @classmethod
    def none(cls):
        """A helper method that sets all permissions to False."""
        return cls(0)
    
    @classmethod
    def general(cls):
        """A helper method that sets permissions generally for public channels."""
        p = cls.none()
        p.view_channel = True
        p.send_messages = True
        p.read_message_history = True
        p.change_nickname = True
        p.use_application_commands = True
        return p
        
    @classmethod
    def from_backend_strings(cls, strings: list):
        """Converts a list of backend permission strings to a Permissions object."""
        value = 0
        # Mapping for discrepancies between Backend and SDK/Discord naming
        mapping = {
            'ADMINISTRATOR': cls.ADMINISTRATOR,
            'MANAGE_SERVER': cls.MANAGE_GUILD,
            'VIEW_CHANNELS': cls.VIEW_CHANNEL,
            'CREATE_INVITES': cls.CREATE_INSTANT_INVITE,
            # Standard mappings
            'KICK_MEMBERS': cls.KICK_MEMBERS,
            'BAN_MEMBERS': cls.BAN_MEMBERS,
            'MODERATE_MEMBERS': cls.MODERATE_MEMBERS,
            'MANAGE_ROLES': cls.MANAGE_ROLES,
            'MANAGE_CHANNELS': cls.MANAGE_CHANNELS,
            'SEND_MESSAGES': cls.SEND_MESSAGES,
            'SEND_TTS_MESSAGES': cls.SEND_TTS_MESSAGES,
            'READ_MESSAGE_HISTORY': cls.READ_MESSAGE_HISTORY,
            'MENTION_EVERYONE': cls.MENTION_EVERYONE,
            'MANAGE_MESSAGES': cls.MANAGE_MESSAGES,
            'EMBED_LINKS': cls.EMBED_LINKS,
            'ATTACH_FILES': cls.ATTACH_FILES,
            'ADD_REACTIONS': cls.ADD_REACTIONS,
            'USE_EXTERNAL_EMOJIS': cls.USE_EXTERNAL_EMOJIS,
            'CONNECT': cls.CONNECT,
            'SPEAK': cls.SPEAK,
            'MUTE_MEMBERS': cls.MUTE_MEMBERS,
            'DEAFEN_MEMBERS': cls.DEAFEN_MEMBERS,
            'MOVE_MEMBERS': cls.MOVE_MEMBERS,
            'PRIORITY_SPEAKER': cls.PRIORITY_SPEAKER,
            'STREAM': cls.STREAM,
            'USE_VAD': cls.USE_VAD,
            'MANAGE_WEBHOOKS': cls.MANAGE_WEBHOOKS,
            'MANAGE_EMOJIS_AND_STICKERS': cls.MANAGE_EMOJIS_AND_STICKERS,
            'MANAGE_NICKNAMES': cls.MANAGE_NICKNAMES,
            'CHANGE_NICKNAME': cls.CHANGE_NICKNAME,
            'MANAGE_THREADS': cls.MANAGE_THREADS,
            'CREATE_PUBLIC_THREADS': cls.CREATE_PUBLIC_THREADS,
            'CREATE_PRIVATE_THREADS': cls.CREATE_PRIVATE_THREADS,
            'USE_EXTERNAL_STICKERS': cls.USE_EXTERNAL_STICKERS,
            'SEND_MESSAGES_IN_THREADS': cls.SEND_MESSAGES_IN_THREADS,
            'USE_EMBEDDED_ACTIVITIES': cls.USE_EMBEDDED_ACTIVITIES,
        }
        
        for s in strings:
            if s in mapping:
                value |= mapping[s]
            elif hasattr(cls, s) and isinstance(getattr(cls, s), int):
                value |= getattr(cls, s)
                
        return cls(value)
        
