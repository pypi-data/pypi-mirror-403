"""
Virtualizor Forwarding Tool

CLI tool for managing domain/port forwarding in Virtualizor VPS environments
with multi-host support and Rich TUI.
"""

__version__ = "1.0.3"
__author__ = "Rizky Adhy Pratama"
__email__ = "rizkyadhypratama@gmail.com"

from .models import (
    Protocol,
    VMStatus,
    HostProfile,
    Config,
    VMInfo,
    ForwardingRule,
    HAProxyConfig,
    APIResponse,
    ValidationResult,
    BatchResult,
)
from .config import ConfigManager
from .api import VirtualizorClient, APIError, APIConnectionError, AuthenticationError
from .tui import TUIRenderer
from .cli import CLI, main

__all__ = [
    # Models
    "Protocol",
    "VMStatus",
    "HostProfile",
    "Config",
    "VMInfo",
    "ForwardingRule",
    "HAProxyConfig",
    "APIResponse",
    "ValidationResult",
    "BatchResult",
    # Core classes
    "ConfigManager",
    "VirtualizorClient",
    "TUIRenderer",
    "CLI",
    "main",
    # Exceptions
    "APIError",
    "APIConnectionError",
    "AuthenticationError",
]
