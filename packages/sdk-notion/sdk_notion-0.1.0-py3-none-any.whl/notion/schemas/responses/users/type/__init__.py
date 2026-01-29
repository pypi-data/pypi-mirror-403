from .Person import Person as _Person
from .Bot    import Bot    as _Bot

class Schemas:

    Person = _Person
    Bot    = _Bot

__all__ = ["Schemas"]