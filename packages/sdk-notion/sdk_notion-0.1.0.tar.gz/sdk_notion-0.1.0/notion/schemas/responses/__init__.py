from .databases import Schemas as _databases
from .pages     import Schemas as _pages
from .users     import Schemas as _users
from .errors    import Schemas as _errors

class Schemas:

    databases = _databases
    pages     = _pages
    users     = _users
    errors    = _errors

__all__ = ["Schemas"]