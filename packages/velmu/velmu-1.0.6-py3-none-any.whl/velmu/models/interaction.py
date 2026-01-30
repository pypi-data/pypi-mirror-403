from typing import Optional, Dict, Any, Union
from .base import BaseModel

class Interaction(BaseModel):
    """Represents an Interaction.
    
    Attributes
    ----------
    id: str
        The interaction ID.
    type: int
        The type of interaction.
    data: dict
        The interaction data (e.g. custom_id).
    user: User
        The user who triggered the interaction.
    message: Message
        The message the interaction was on.
    message_id: str
        The ID of the message the interaction was on.
    channel_id: str
        The ID of the channel.
    guild_id: str
        The ID of the guild.
    """
    def __init__(self, state, data):
        self._state = state
        self.id = data.get('id')
        self.type = data.get('type')
        self.data = data.get('data')
        self.user = data.get('user')
        self.message = data.get('message')
        self.message_id = data.get('messageId')
        self.application_id = data.get('applicationId')
        self.channel_id = data.get('channelId') or data.get('channel_id')
        self.guild_id = data.get('guildId') or data.get('guild_id')

    async def edit_original(self, content: Optional[str] = None, embed: Optional[Union[Dict, 'Embed']] = None, components: Optional[list] = None):
        """Edits the message that triggered the interaction."""
        if not self.message_id:
            raise ValueError("No message_id found in interaction to edit.")
            
        # Convert embed if it's an object
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
            
        # Convert components to dicts if they are objects
        if components:
            components = [(c.to_dict() if hasattr(c, 'to_dict') else c) for c in components]
            
        return await self._state.http.edit_message(self.message_id, content=content, embed=embed, components=components)

    async def respond(self, content: Optional[str] = None, embed: Optional[Union[Dict, 'Embed']] = None, components: Optional[list] = None):
        """Sends a message in the channel where the interaction occurred."""
        if not self.channel_id:
            raise ValueError("No channel_id found in interaction to respond to.")
            
        # Convert embed
        if embed and hasattr(embed, 'to_dict'):
            embed = embed.to_dict()
            
        # Convert components
        if components:
            components = [(c.to_dict() if hasattr(c, 'to_dict') else c) for c in components]
            
        # We can use the state.http directly
        return await self._state.http.send_message(self.channel_id, content=content, embed=embed, components=components)
