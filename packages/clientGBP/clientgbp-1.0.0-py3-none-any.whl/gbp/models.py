"""
Módulo de modelos para el cliente de GBP.

Contiene las clases que representan la información de envío de un cliente y un contacto.
"""

from pydantic import BaseModel
from gbp.enums import ClientType


class Client(BaseModel):
    """Clase que representa la información de un cliente en el módulo de Clientes en GBP"""

    state: str
    state_number: str = "54020"
    tax_number: str
    company_name: str
    city: str = "-"
    address: str = "-"
    zip_code: str = "-"
    phone: str = "0"
    seller_name: str
    seller_number: str | None = None
    name: str
    email: str
    type_client: ClientType


class Contact(BaseModel):
    """Clase que representa la información de un contacto en el módulo de Contactos en GBP"""

    name: str
    phone: str = "0"
    email: str
    seller_name: str
    seller_number: str | None = None
    tax_number: str
    crm: str | None = None
