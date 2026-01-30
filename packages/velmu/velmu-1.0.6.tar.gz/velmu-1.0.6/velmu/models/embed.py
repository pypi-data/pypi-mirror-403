from typing import List, Dict, Union, Optional
import datetime

class Embed:
    """Represents a rich embed object."""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.type = kwargs.get('type', 'rich')
        self.description = kwargs.get('description')
        self.url = kwargs.get('url')
        self.timestamp = kwargs.get('timestamp')
        self.color = kwargs.get('color')
        self.width = kwargs.get('width')
        
        self.footer = kwargs.get('footer')
        self.image = kwargs.get('image')
        self.thumbnail = kwargs.get('thumbnail')
        self.video = kwargs.get('video')
        self.provider = kwargs.get('provider')
        self.author = kwargs.get('author')
        self.fields = kwargs.get('fields', [])
        
    def to_dict(self) -> Dict:
        """Converts the embed to a dictionary."""
        result = {'type': self.type}
        
        if self.title:
            result['title'] = self.title
        if self.description:
            result['description'] = self.description
        if self.url:
            result['url'] = self.url
        if self.timestamp:
            if isinstance(self.timestamp, datetime.datetime):
                result['timestamp'] = self.timestamp.isoformat()
            else:
                result['timestamp'] = self.timestamp
        if self.color:
            result['color'] = self.color
        if self.width:
            result['width'] = self.width
            
        if self.footer:
            result['footer'] = self.footer
        if self.image:
            result['image'] = self.image
        if self.thumbnail:
            result['thumbnail'] = self.thumbnail
        if self.author:
            result['author'] = self.author
        if self.fields:
            result['fields'] = self.fields
            
        return result

    def set_width(self, width: int):
        """Sets the width of the embed."""
        self.width = width
        return self

    def set_footer(self, text: str, icon_url: Optional[str] = None):
        """Sets the footer of the embed."""
        self.footer = {'text': text}
        if icon_url:
            self.footer['iconUrl'] = icon_url
        return self

    def set_image(self, url: str):
        """Sets the image of the embed."""
        self.image = {'url': url}
        return self

    def set_thumbnail(self, url: str):
        """Sets the thumbnail of the embed."""
        self.thumbnail = {'url': url}
        return self

    def set_author(self, name: str, url: Optional[str] = None, icon_url: Optional[str] = None):
        """Sets the author of the embed."""
        self.author = {'name': name}
        if url:
            self.author['url'] = url
        if icon_url:
            self.author['iconUrl'] = icon_url
        return self

    def add_field(self, name: str, value: str, inline: bool = True):
        """Adds a field to the embed."""
        field = {
            'name': name,
            'value': value,
            'inline': inline
        }
        self.fields.append(field)
        return self
