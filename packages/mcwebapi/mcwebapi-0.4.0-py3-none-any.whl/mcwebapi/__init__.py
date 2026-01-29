"""
Minecraft WebAPI Client
A Python client for interacting with Minecraft servers via WebSocket API.
"""

from .api import MinecraftAPI
from . import types

__version__ = "0.4.0"
__author__ = "addavriance"

__all__ = [
    "MinecraftAPI",
    "types",
]