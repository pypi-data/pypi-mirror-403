"""Event decoding types and helpers.

DecodedEvent is a frozen dataclass representing a single decoded log event.
Helper functions are pure functions, not methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class DecodedEvent:
    """Single decoded log event. Immutable.

    Use Mapping[str, Any] for args to ensure immutability.
    The args are wrapped with MappingProxyType at construction.
    """

    address: str
    event_name: str
    args: Mapping[str, Any]  # Immutable - use MappingProxyType when constructing
    log_index: int
    tx_hash: str
    block_number: int

    @classmethod
    def create(
        cls,
        address: str,
        event_name: str,
        args: dict[str, Any],
        log_index: int,
        tx_hash: str,
        block_number: int,
    ) -> DecodedEvent:
        """Create a DecodedEvent with immutable args.

        Wraps the args dict in MappingProxyType to ensure immutability.
        """
        return cls(
            address=address,
            event_name=event_name,
            args=MappingProxyType(args),
            log_index=log_index,
            tx_hash=tx_hash,
            block_number=block_number,
        )


def find_event(events: list[DecodedEvent], event_name: str) -> DecodedEvent | None:
    """Find the first event matching the given name.

    Args:
        events: List of decoded events
        event_name: Name of event to find

    Returns:
        First matching event, or None if not found
    """
    for event in events:
        if event.event_name == event_name:
            return event
    return None


def events_by_name(events: list[DecodedEvent], event_name: str) -> list[DecodedEvent]:
    """Get all events matching the given name.

    Args:
        events: List of decoded events
        event_name: Name of events to find

    Returns:
        List of matching events (may be empty)
    """
    return [e for e in events if e.event_name == event_name]


def events_by_address(events: list[DecodedEvent], address: str) -> list[DecodedEvent]:
    """Get all events emitted by the given address.

    Args:
        events: List of decoded events
        address: Contract address (case-insensitive comparison)

    Returns:
        List of matching events (may be empty)
    """
    addr_lower = address.lower()
    return [e for e in events if e.address.lower() == addr_lower]
