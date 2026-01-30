"""
MCP Server: did:jis - The Intent-Centric Web
Bilateral Intent DID Method for AI and Human Communication.

Part of the HumoticaOS ecosystem.
"""

from .server import run, JISClient, IntentRequest, IntentResponse

__version__ = "1.0.0"
__author__ = "Jasper van de Meent, Root AI"
__email__ = "info@humotica.nl"

__all__ = ["run", "JISClient", "IntentRequest", "IntentResponse"]
