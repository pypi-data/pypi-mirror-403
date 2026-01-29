from .type   import Schemas as _type
from .User   import User    as _User
from .Person import Person as _Person
from .Bot    import Bot    as _Bot

class Schemas:

    type   = _type
    User   = _User
    Person = _Person
    Bot    = _Bot

__all__ = ["Schemas"]