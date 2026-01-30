"""
velmu.models.attachment
~~~~~~~~~~~~~~~~~~~~~~~

Represents an attachment in a Message.
"""
from typing import Optional

class Attachment:
    """Represents an attachment."""
    __slots__ = ('id', 'filename', 'size', 'url', 'proxy_url', 'content_type', 'height', 'width')
    
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.filename = data.get('filename')
        self.size = data.get('size')
        self.url = data.get('url')
        self.proxy_url = data.get('proxyUrl') # Optional
        self.content_type = data.get('contentType')
        self.height = data.get('height')
        self.width = data.get('width')

    def __repr__(self):
        return f'<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>'
