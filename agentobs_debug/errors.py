"""
Exception hierarchy for agentobs-debug.

All public exceptions are rooted at AgentOBSDebugError so callers can
catch the broad base class or any specific subclass.
"""


class AgentOBSDebugError(Exception):
    """Base exception for all agentobs-debug errors."""


class TraceNotFoundError(AgentOBSDebugError):
    """Raised when no events matching the requested trace_id are found in the stream."""


class CorruptEventError(AgentOBSDebugError):
    """Raised when an event source (e.g. a JSONL file) contains malformed data."""


class InvalidSpanHierarchyError(AgentOBSDebugError):
    """Raised when the span parent/child relationships cannot be resolved."""
