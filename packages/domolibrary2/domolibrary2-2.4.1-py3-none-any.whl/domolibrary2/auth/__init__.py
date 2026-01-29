"""Domo authentication classes for various authentication methods.

This module re-exports authentication classes for different Domo auth methods:
- DomoAuth: Base authentication class
- DomoFullAuth: Username/password authentication
- DomoTokenAuth: Access token authentication
- DomoDeveloperAuth: OAuth2 client credentials authentication
- DomoJupyterAuth: Base Jupyter authentication
- DomoJupyterFullAuth: Jupyter with username/password
- DomoJupyterTokenAuth: Jupyter with access token

Type Hinting:
All authentication classes (DomoTokenAuth, DomoFullAuth, DomoDeveloperAuth, etc.)
are structurally compatible with DomoAuth even if not directly inheriting from it.
They implement the same interface via shared mixins, so functions can accept
`DomoAuth` and work with any auth subclass.
"""

from .base import DomoAuth
from .developer import DomoDeveloperAuth
from .full import DomoFullAuth
from .jupyter import DomoJupyterAuth, DomoJupyterFullAuth, DomoJupyterTokenAuth
from .token import DomoTokenAuth
from .utils import test_is_full_auth, test_is_jupyter_auth

__all__ = [
    "DomoAuth",
    "DomoFullAuth",
    "DomoTokenAuth",
    "DomoDeveloperAuth",
    "DomoJupyterAuth",
    "DomoJupyterFullAuth",
    "DomoJupyterTokenAuth",
    "test_is_full_auth",
    "test_is_jupyter_auth",
]
