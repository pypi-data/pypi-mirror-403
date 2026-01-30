"""
velmu.abc
~~~~~~~~~

Abstract Base Classes for the Velmu SDK.
"""
import abc
import datetime
from .errors import ClientException

class Snowflake(abc.ABC):
    """An abstract base class for objects that have a unique ID."""
    
    __slots__ = ()

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """str: The unique ID of the object."""
        raise NotImplementedError

    @property
    def created_at(self) -> datetime.datetime:
        """datetime.datetime: The time the object was created (if derivable or stored).
        For standard UUIDs this might not be derivable, but we define the interface.
        """
        # Default implementation if not overridden
        return datetime.datetime.utcnow() 

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)


class Messageable(abc.ABC):
    """An abstract base class for models that can send messages.
    
    e.g. Channel, User (DM), Context
    """
    
    __slots__ = ()

    @abc.abstractmethod
    async def _get_channel(self):
        raise NotImplementedError

    async def send(self, content=None, *, embed=None, **kwargs):
        """Sends a message to the destination.
        
        Parameters
        ----------
        content : str
            The content of the message.
        embed : Embed
            The embed to send.
            
        Returns
        -------
        Message
            The sent message.
        """
        channel = await self._get_channel()
        if hasattr(channel, 'send'):
            return await channel.send(content, embed=embed, **kwargs)
        raise NotImplementedError("Channel retrieved from _get_channel has no send method")

class Connectable(abc.ABC):
    """An interface for objects that need a connection state."""
    __slots__ = ()
    
    @property
    @abc.abstractmethod
    def _state(self):
        raise NotImplementedError
