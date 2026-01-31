# Copyright (c) 2025 - 2026, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

"""Core primitives with lazy loading for fast import."""

from __future__ import annotations

from typing import TYPE_CHECKING

# Lazy import mapping
_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    # broadcaster
    "Broadcaster": ("kronos.core.broadcaster", "Broadcaster"),
    # element
    "Element": ("kronos.core.element", "Element"),
    # event
    "Event": ("kronos.core.event", "Event"),
    "EventStatus": ("kronos.core.event", "EventStatus"),
    "Execution": ("kronos.core.event", "Execution"),
    # eventbus
    "EventBus": ("kronos.core.eventbus", "EventBus"),
    "Handler": ("kronos.core.eventbus", "Handler"),
    # flow
    "Flow": ("kronos.core.flow", "Flow"),
    # graph
    "Edge": ("kronos.core.graph", "Edge"),
    "EdgeCondition": ("kronos.core.graph", "EdgeCondition"),
    "Graph": ("kronos.core.graph", "Graph"),
    # node
    "DEFAULT_NODE_CONFIG": ("kronos.core.node", "DEFAULT_NODE_CONFIG"),
    "NODE_REGISTRY": ("kronos.core.node", "NODE_REGISTRY"),
    "PERSISTABLE_NODE_REGISTRY": ("kronos.core.node", "PERSISTABLE_NODE_REGISTRY"),
    "Node": ("kronos.core.node", "Node"),
    "NodeConfig": ("kronos.core.node", "NodeConfig"),
    "create_node": ("kronos.core.node", "create_node"),
    "generate_ddl": ("kronos.core.node", "generate_ddl"),
    # phrase
    "PHRASE_REGISTRY": ("kronos.core.phrase", "PHRASE_REGISTRY"),
    "Phrase": ("kronos.core.phrase", "Phrase"),
    "PhraseConfig": ("kronos.core.phrase", "PhraseConfig"),
    "PhraseError": ("kronos.core.phrase", "PhraseError"),
    "RequirementNotMet": ("kronos.core.phrase", "RequirementNotMet"),
    "create_phrase": ("kronos.core.phrase", "create_phrase"),
    "get_phrase": ("kronos.core.phrase", "get_phrase"),
    "list_phrases": ("kronos.core.phrase", "list_phrases"),
    # pile
    "Pile": ("kronos.core.pile", "Pile"),
    # processor
    "Executor": ("kronos.core.processor", "Executor"),
    "Processor": ("kronos.core.processor", "Processor"),
    # progression
    "Progression": ("kronos.core.progression", "Progression"),
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

    raise AttributeError(f"module 'kronos.core' has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return all available attributes for autocomplete."""
    return list(__all__)


# TYPE_CHECKING block for static analysis
if TYPE_CHECKING:
    from .broadcaster import Broadcaster
    from .element import Element
    from .event import Event, EventStatus, Execution
    from .eventbus import EventBus, Handler
    from .flow import Flow
    from .graph import Edge, EdgeCondition, Graph
    from .node import (
        DEFAULT_NODE_CONFIG,
        NODE_REGISTRY,
        PERSISTABLE_NODE_REGISTRY,
        Node,
        NodeConfig,
        create_node,
        generate_ddl,
    )
    from .phrase import (
        PHRASE_REGISTRY,
        Phrase,
        PhraseConfig,
        PhraseError,
        RequirementNotMet,
        create_phrase,
        get_phrase,
        list_phrases,
    )
    from .pile import Pile
    from .processor import Executor, Processor
    from .progression import Progression

__all__ = [
    # constants
    "DEFAULT_NODE_CONFIG",
    "NODE_REGISTRY",
    "PERSISTABLE_NODE_REGISTRY",
    "PHRASE_REGISTRY",
    # classes
    "Broadcaster",
    "Edge",
    "EdgeCondition",
    "Element",
    "Event",
    "EventBus",
    "EventStatus",
    "Execution",
    "Executor",
    "Flow",
    "Graph",
    "Handler",
    "Node",
    "NodeConfig",
    "Phrase",
    "PhraseConfig",
    "PhraseError",
    "Pile",
    "Processor",
    "Progression",
    "RequirementNotMet",
    # functions
    "create_node",
    "create_phrase",
    "generate_ddl",
    "get_phrase",
    "list_phrases",
]
