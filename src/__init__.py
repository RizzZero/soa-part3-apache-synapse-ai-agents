"""
Apache Synapse MCP Server

A Model Context Protocol (MCP) server that provides secure, controlled access
to Apache Synapse enterprise integration capabilities.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.server import SynapseMCPServer
from .core.config import SynapseMCPConfig
from .services.proxy_service import ProxyService
from .transformers.message_transformer import MessageTransformer
from .security.auth_manager import AuthManager
from .monitoring.metrics import MetricsCollector

__all__ = [
    "SynapseMCPServer",
    "SynapseMCPConfig", 
    "ProxyService",
    "MessageTransformer",
    "AuthManager",
    "MetricsCollector"
] 