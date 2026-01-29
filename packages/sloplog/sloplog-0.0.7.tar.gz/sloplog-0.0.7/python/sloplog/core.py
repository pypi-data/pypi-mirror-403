"""Core types for sloplog wide events."""

from dataclasses import dataclass
from typing import TypedDict, Any, Literal, cast
from importlib.metadata import PackageNotFoundError, version

# Type definitions

# EventPartial is a dict with a required "type" key and arbitrary additional fields
EventPartial = dict[str, Any]
"""
An event partial is a structured bit of data added to a wide event.
Each partial has a type discriminator and arbitrary additional fields.
"""

PartialValue = EventPartial | list[EventPartial]
"""Either a single partial or a list of repeatable partials."""

LogMessageLevel = Literal["trace", "debug", "info", "warn", "error", "fatal"]
"""Allowed levels for log_message and logger-based collectors."""


class _ServiceRequired(TypedDict):
    """Required service fields"""

    name: str


class Service(_ServiceRequired, total=False):
    """
    Service information - where an event is emitted from.

    sloplogVersion and sloplogLanguage are auto-populated when omitted.
    """

    version: str
    sloplogVersion: str
    sloplogLanguage: str


def _sloplog_version() -> str:
    try:
        return version("sloplog")
    except PackageNotFoundError:
        return "0.0.0"


SLOPLOG_VERSION = _sloplog_version()
SLOPLOG_LANGUAGE = "python"


def service(details: Service) -> Service:
    """Create a Service payload with sloplog defaults applied."""
    payload = cast(Service, dict(details))
    payload.setdefault("sloplogVersion", SLOPLOG_VERSION)
    payload.setdefault("sloplogLanguage", SLOPLOG_LANGUAGE)
    return payload


# Import Originator type for type hints
from .originator import Originator


@dataclass
class WideEventBase:
    """The base structure of a wide event (without partials)."""

    event_id: str
    trace_id: str
    service: Service
    originator: Originator

    def to_dict(self) -> dict[str, Any]:
        """Convert the base event to a dict with wire-format keys."""
        return {
            "eventId": self.event_id,
            "traceId": self.trace_id,
            "service": dict(self.service),
            "originator": dict(self.originator),
        }


__all__ = [
    "EventPartial",
    "PartialValue",
    "LogMessageLevel",
    "Service",
    "service",
    "SLOPLOG_VERSION",
    "SLOPLOG_LANGUAGE",
    "WideEventBase",
]
