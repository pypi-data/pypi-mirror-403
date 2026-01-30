"""
velmu.models.components
~~~~~~~~~~~~~~~~~~~~~~~

Message Components for the Velmu SDK.
"""
from typing import List, Optional, Union, Dict, Any
from enum import IntEnum

class ComponentType(IntEnum):
    ACTION_ROW = 1
    BUTTON = 2

class ButtonStyle(IntEnum):
    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5
    
    # Aliases to match backend/discord names
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5

class Component:
    """Base class for message components."""
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

class Button(Component):
    """Represents a button component.
    
    Attributes
    ----------
    style: ButtonStyle
        The style of the button.
    label: Optional[str]
        The text displayed on the button.
    custom_id: Optional[str]
        The ID sent back when clicked (for non-link buttons).
    url: Optional[str]
        The URL for link buttons.
    emoji: Optional[str]
        The emoji displayed next to the label.
    disabled: bool
        Whether the button is disabled.
    """
    def __init__(
        self, 
        style: Union[ButtonStyle, int] = ButtonStyle.primary,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[str] = None,
        disabled: bool = False
    ):
        self.type = ComponentType.BUTTON
        self.style = style
        self.label = label
        self.custom_id = custom_id
        self.url = url
        self.emoji = emoji
        self.disabled = disabled

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "type": self.type,
            "style": int(self.style) if isinstance(self.style, ButtonStyle) else self.style,
            "disabled": self.disabled
        }
        if self.label: res["label"] = self.label
        if self.custom_id: res["customId"] = self.custom_id
        if self.url: res["url"] = self.url
        if self.emoji: res["emoji"] = self.emoji
        
        # Convert style back to string names if it's an int/enum for backend compatibility if needed
        # But wait, backend handles both usually. Our frontend expects string styles maybe?
        # Let's check MessageButton.tsx again.
        return res

class ActionRow(Component):
    """Represents an Action Row component.
    
    Attributes
    ----------
    components: List[Component]
        The components contained in this row.
    """
    def __init__(self, *components: Component):
        self.type = ComponentType.ACTION_ROW
        self.components = list(components)

    def add_button(self, **kwargs) -> 'ActionRow':
        self.components.append(Button(**kwargs))
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "components": [c.to_dict() for c in self.components]
        }
