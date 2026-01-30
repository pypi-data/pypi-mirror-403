"""
velmu.models.base
~~~~~~~~~~~~~~~~~

Base model class.
"""

class BaseModel:
    """Base class for all Velmu models."""
    
    __slots__ = ('_state', 'id')

    def __init__(self, state, data):
        self._state = state
        self.id = data.get('id')

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)
