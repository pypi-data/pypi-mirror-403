# Copyright (c) 2025 - 2026, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

"""Services module: iModel, ServiceBackend, hooks, and registry.

Core exports:
- iModel: Unified service interface with rate limiting and hooks
- ServiceBackend/Endpoint: Backend abstractions for API calls
- HookRegistry/HookEvent/HookPhase: Lifecycle hook system
- ServiceRegistry: O(1) name-based service lookup

Uses lazy loading for fast import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Lazy import mapping
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "Calling": ("kronos.services.backend", "Calling"),
    "NormalizedResponse": ("kronos.services.backend", "NormalizedResponse"),
    "ServiceBackend": ("kronos.services.backend", "ServiceBackend"),
    "ServiceConfig": ("kronos.services.backend", "ServiceConfig"),
    "ServiceRegistry": ("kronos.services.registry", "ServiceRegistry"),
    "iModel": ("kronos.services.imodel", "iModel"),
    "Endpoint": ("kronos.services.endpoint", "Endpoint"),
    "EndpointConfig": ("kronos.services.endpoint", "EndpointConfig"),
    "APICalling": ("kronos.services.endpoint", "APICalling"),
    "HookRegistry": ("kronos.services.hook", "HookRegistry"),
    "HookEvent": ("kronos.services.hook", "HookEvent"),
    "HookPhase": ("kronos.services.hook", "HookPhase"),
}

_LOADED: dict[str, object] = {}


def __getattr__(name: str) -> object:
    """Lazy import attributes on first access."""
    if name in _LOADED:
        return _LOADED[name]

    if name in _LAZY_IMPORTS:
        from importlib import import_module

        module_name, attr_name = _LAZY_IMPORTS[name]
        module = import_module(module_name)
        value = getattr(module, attr_name)
        _LOADED[name] = value
        return value

    raise AttributeError(f"module 'kronos.services' has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return all available attributes for autocomplete."""
    return list(__all__)


# TYPE_CHECKING block for static analysis
if TYPE_CHECKING:
    from .backend import Calling, NormalizedResponse, ServiceBackend, ServiceConfig
    from .endpoint import APICalling, Endpoint, EndpointConfig
    from .hook import HookEvent, HookPhase, HookRegistry
    from .imodel import iModel
    from .registry import ServiceRegistry

__all__ = (
    "APICalling",
    "Calling",
    "Endpoint",
    "EndpointConfig",
    "HookEvent",
    "HookPhase",
    "HookRegistry",
    "NormalizedResponse",
    "ServiceBackend",
    "ServiceConfig",
    "ServiceRegistry",
    "iModel",
)
