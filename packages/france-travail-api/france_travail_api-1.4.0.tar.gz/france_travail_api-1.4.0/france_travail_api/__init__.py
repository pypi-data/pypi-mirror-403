"""
Client interface for the France Travail API.

This module provides the main `FranceTravailClient` class for authenticating
and interacting with France Travail services.

Classes
-------
FranceTravailClient
    Primary client for API access with OAuth2 authentication.

Scope
    Available API scopes.

Examples
--------
>>> from france_travail_api.client import FranceTravailClient
>>> from france_travail_api.auth.scope import Scope
>>>
>>> with FranceTravailClient(
...     client_id="your_id",
...     client_secret="your_secret",
...     scopes=[Scope.OFFRES]
... ) as client:
...     pass  # Use client to access API endpoints
"""

from france_travail_api.auth.scope import Scope
from france_travail_api.client import FranceTravailClient

__all__ = [
    "FranceTravailClient",
    "Scope",
]
