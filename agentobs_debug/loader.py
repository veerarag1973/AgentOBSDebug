"""
loader.py — Load AgentOBS events from supported sources.

The module MUST use tracium.stream.EventStream for all loading.
It MUST NOT reimplement event parsing.

SDK note
--------
The AgentOBS SDK is installed as `agentobs` (pip install agentobs) and imported
as `tracium`.  JSONL loading is provided by EventStream.from_file(), which
deserialises each line with Event.from_json() internally.
"""

from __future__ import annotations

from tracium.event import Event
from tracium.stream import EventStream

from agentobs_debug.errors import CorruptEventError, TraceNotFoundError


def load_events(path: str) -> EventStream:
    """Load events from a JSONL file using the AgentOBS EventStream.

    Delegates all parsing to ``tracium.stream.EventStream.from_file()``.

    Parameters
    ----------
    path:
        Path to a ``.jsonl`` file produced by an AgentOBS exporter.

    Returns
    -------
    EventStream
        An immutable stream of ``Event`` objects ready for inspection.

    Raises
    ------
    CorruptEventError
        If the file cannot be opened or contains a malformed event line.
    """
    try:
        return EventStream.from_file(path)
    except FileNotFoundError as exc:
        raise CorruptEventError(f"Events file not found: {path!r}") from exc
    except OSError as exc:
        raise CorruptEventError(f"Cannot read events file {path!r}: {exc}") from exc
    except Exception as exc:
        raise CorruptEventError(
            f"Failed to parse events from {path!r}: {exc}"
        ) from exc


def _filter_by_trace(stream: EventStream, trace_id: str) -> list[Event]:
    """Return all events in *stream* that belong to *trace_id*.

    Parameters
    ----------
    stream:
        Source EventStream (previously loaded with :func:`load_events`).
    trace_id:
        32-character hex OpenTelemetry trace ID.

    Raises
    ------
    TraceNotFoundError
        If no events with the given ``trace_id`` exist in the stream.
    """
    events = [e for e in stream if e.trace_id == trace_id]
    if not events:
        raise TraceNotFoundError(
            f"No events found for trace_id={trace_id!r}. "
            "Check that the correct JSONL file is loaded."
        )
    return events
