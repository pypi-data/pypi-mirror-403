from datetime import datetime

class Embed:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.url = kwargs.get('url')
        self.color = kwargs.get('color')
        self.timestamp = kwargs.get('timestamp')
        self.html = kwargs.get('html')
        self.fields = []
        
        # Ownership fields
        self.owner_id = kwargs.get('owner_id')  # User ID who can interact
        self.owner_username = kwargs.get('owner_username')  # Display name for overlay
        self.public = kwargs.get('public', True if not kwargs.get('owner_id') else False)
        
        self.footer = None
        self.image = None
        self.thumbnail = None
        self.author = None

    def set_owner(self, user_id, username=None):
        """Restrict interactions to a specific user"""
        self.owner_id = user_id
        self.owner_username = username
        self.public = False
        return self

    def set_public(self, is_public=True):
        """Allow anyone to interact"""
        self.public = is_public
        return self

    def set_footer(self, text, icon_url=None):
        self.footer = {'text': text, 'icon_url': icon_url}
        return self

    def set_image(self, url):
        self.image = {'url': url}
        return self

    def set_thumbnail(self, url):
        self.thumbnail = {'url': url}
        return self

    def set_author(self, name, url=None, icon_url=None):
        self.author = {'name': name, 'url': url, 'icon_url': icon_url}
        return self

    def add_field(self, name, value, inline=True):
        self.fields.append({'name': name, 'value': value, 'inline': inline})
        return self

    def to_dict(self):
        result = {
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'color': self.color,
            'fields': self.fields,
            'public': self.public
        }

        if self.owner_id:
            result['ownerId'] = self.owner_id
            result['ownerUsername'] = self.owner_username

        if self.html:
            result['html'] = self.html
        
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp

        if self.footer: result['footer'] = self.footer
        if self.image: result['image'] = self.image['url'] if isinstance(self.image, dict) else self.image
        if self.thumbnail: result['thumbnail'] = self.thumbnail['url'] if isinstance(self.thumbnail, dict) else self.thumbnail
        if self.author: result['author'] = self.author
        
        return result

