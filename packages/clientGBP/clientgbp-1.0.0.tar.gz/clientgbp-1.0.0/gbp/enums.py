"""
Contiene los enums utilizados en el proyecto
"""

from enum import Enum, auto, unique


@unique
class ClientType(Enum):
    """
    Representa los tipos de clientes asociados en GBP.

    CLIENT_C: Cliente C
    CLIENT_A: Cliente A
    END_USER: Usuario final
    """

    CLIENT_C = auto()
    CLIENT_A = auto()
    END_USER = auto()
