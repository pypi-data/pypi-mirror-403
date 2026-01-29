"""Sentry collector for sloplog."""

import logging
from typing import Callable, cast

from ..core import PartialValue, WideEventBase, LogMessageLevel
from .base import LogCollectorClient, flatten_object


class SentryCollector(LogCollectorClient):
    """
    Collector that sends events through a logger configured with Sentry's logging
    integration (e.g. Sentry LoggingIntegration).

    Attributes are flattened to dot-notation keys and passed directly as extra
    kwargs for better queryability in Sentry.
    """

    _LEVELS: dict[LogMessageLevel, int] = {
        "trace": logging.DEBUG,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
        "fatal": logging.CRITICAL,
    }

    def __init__(
        self,
        logger: logging.Logger,
        level: LogMessageLevel = "info",
        level_selector: Callable[
            [WideEventBase, dict[str, PartialValue]], LogMessageLevel
        ]
        | None = None,
        message: str = "wide-event",
        flatten_attributes: bool = True,
    ):
        """
        Initialize the Sentry collector.

        Args:
            logger: Python logger configured with Sentry LoggingIntegration
            level: Default log level for events (default: "info")
            level_selector: Optional function to derive log level per event
            message: Log message to use (default: "wide-event")
            flatten_attributes: If True, flatten nested attributes to dot-notation
                keys for better queryability in Sentry (e.g., `error.message`,
                `spans.0.name`). Default: True
        """
        self._logger = logger
        self._level = level
        self._level_selector = level_selector
        self._message = message
        self._flatten_attributes = flatten_attributes

    async def flush(
        self, event: WideEventBase, partials: dict[str, PartialValue]
    ) -> None:
        combined = {
            **event.to_dict(),
            **partials,
        }

        # Flatten nested attributes to dot-notation for better Sentry queryability
        attributes = (
            flatten_object(combined)
            if self._flatten_attributes
            else combined
        )

        level = cast(
            LogMessageLevel,
            self._level_selector(event, partials)
            if self._level_selector is not None
            else self._level,
        )
        level_no = self._LEVELS.get(level, logging.INFO)

        # Pass flattened attributes directly as extra kwargs (not under "sloplog")
        self._logger.log(level_no, self._message, extra=attributes)


def sentry_collector(
    logger: logging.Logger,
    level: LogMessageLevel = "info",
    level_selector: Callable[[WideEventBase, dict[str, PartialValue]], LogMessageLevel]
    | None = None,
    message: str = "wide-event",
    flatten_attributes: bool = True,
) -> SentryCollector:
    """
    Create a collector that sends events via the configured logger.

    Args:
        logger: Python logger configured with Sentry LoggingIntegration
        level: Default log level for events (default: "info")
        level_selector: Optional function to derive log level per event
        message: Log message to use (default: "wide-event")
        flatten_attributes: If True, flatten nested attributes to dot-notation
            keys for better queryability in Sentry. Default: True
    """
    return SentryCollector(
        logger=logger,
        level=level,
        level_selector=level_selector,
        message=message,
        flatten_attributes=flatten_attributes,
    )
