"""Custom exception hierarchy for agents.lock."""

from __future__ import annotations


class AgentsLockError(Exception):
    """Base exception for all agents.lock errors."""


class LockfileError(AgentsLockError):
    """Error related to lockfile parsing or structure."""


class ValidationError(AgentsLockError):
    """Error related to validation of entries or configuration."""


class CacheError(AgentsLockError):
    """Error related to git cache operations."""


class ResolveError(AgentsLockError):
    """Error related to source resolution."""


class RenderError(AgentsLockError):
    """Error related to client configuration rendering."""


class SyncError(AgentsLockError):
    """Error related to synchronization operations."""


class StateError(AgentsLockError):
    """Error related to state tracking."""
