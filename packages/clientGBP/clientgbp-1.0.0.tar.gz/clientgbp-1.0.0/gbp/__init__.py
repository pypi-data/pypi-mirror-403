"""
ClientGBP - Librería para interactuar con GBP mediante HTTP (Scraping).

Uso básico:
    from gbp import ClientGBP, Client, Contact, ClientType

    client = ClientGBP(username="user", password="pass")
    client.login()
"""

from gbp.client import ClientGBP
from gbp.models import Client, Contact
from gbp.enums import ClientType

__version__ = "1.0.0"

__all__ = [
    "ClientGBP",
    "Client",
    "Contact",
    "ClientType",
    "__version__",
]
