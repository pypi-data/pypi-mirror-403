"""Event decoding for the Alerts extension.

Provides receipt-scoped event decoding with named attribute access.
Events are ONLY decoded from receipt logs, never from block-wide scans.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterator

from eth_abi import decode as abi_decode
from eth_utils import event_abi_to_log_topic, to_checksum_address
from hexbytes import HexBytes

from brawny.alerts.errors import (
    EventNotFoundError,
    ReceiptRequiredError,
)
from brawny.logging import get_logger, log_unexpected
from brawny.tx_hash import normalize_tx_hash

if TYPE_CHECKING:
    from brawny.jobs.base import TxReceipt


logger = get_logger(__name__)


class AttributeDict(dict):
    """Dictionary that allows attribute-style access to values.

    Used for accessing decoded event arguments by name.

    Example:
        event.args.amount  # Instead of event.args['amount']
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No attribute or key '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


@dataclass
class LogEntry:
    """Raw log entry from transaction receipt."""

    address: str
    topics: list[str]
    data: str
    block_number: int
    transaction_hash: str
    log_index: int
    block_hash: str = ""
    removed: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LogEntry:
        """Create from receipt log dictionary."""
        return cls(
            address=d.get("address", ""),
            topics=[t if isinstance(t, str) else t.hex() for t in d.get("topics", [])],
            data=d.get("data", "0x"),
            block_number=d.get("blockNumber", 0),
            transaction_hash=normalize_tx_hash(d.get("transactionHash", "")) or "",
            log_index=d.get("logIndex", 0),
            block_hash=d.get("blockHash", ""),
            removed=d.get("removed", False),
        )


@dataclass
class DecodedEvent:
    """A decoded event from transaction receipt logs.

    Attributes:
        name: Event name (e.g., 'Transfer')
        args: Named access to event parameters via AttributeDict
        address: Contract address that emitted the event
        tx_hash: Transaction hash
        log_index: Position in the transaction logs
        block_number: Block number containing the transaction
        raw_log: Original log entry for advanced use
    """

    name: str
    args: AttributeDict
    address: str
    tx_hash: str
    log_index: int
    block_number: int
    raw_log: LogEntry


class EventAccessor:
    """Provides access to decoded events from receipt logs.

    Events are scoped to:
    1. Only from ctx.receipt.logs (not block-wide)
    2. Only from the specific contract address

    Usage:
        vault.events["Deposit"][0]  # Index access
        vault.events.one("Deposit")  # Assert exactly one
        vault.events.first("Deposit")  # First or None
        vault.events.all("Deposit")  # List of all matching
    """

    def __init__(
        self,
        address: str,
        abi: list[dict[str, Any]],
        receipt: TxReceipt | None,
    ) -> None:
        self._address = to_checksum_address(address)
        self._abi = abi
        self._receipt = receipt
        self._event_abis = self._build_event_map()
        self._decoded_cache: dict[str, list[DecodedEvent]] | None = None

    def _build_event_map(self) -> dict[str, dict[str, Any]]:
        """Build mapping from event name to ABI entry."""
        events = {}
        for item in self._abi:
            if item.get("type") == "event":
                name = item.get("name", "")
                if name:
                    events[name] = item
        return events

    def _ensure_receipt(self) -> None:
        """Ensure receipt is available for event access."""
        if self._receipt is None:
            raise ReceiptRequiredError()

    def _decode_all_events(self) -> dict[str, list[DecodedEvent]]:
        """Decode all events from receipt logs for this contract."""
        if self._decoded_cache is not None:
            return self._decoded_cache

        self._ensure_receipt()
        result: dict[str, list[DecodedEvent]] = {}

        for log_dict in self._receipt.logs:
            log = LogEntry.from_dict(log_dict)

            # Filter by contract address
            try:
                log_address = to_checksum_address(log.address)
            except ValueError:
                logger.debug(
                    "events.invalid_log_address",
                    address=log.address,
                    tx_hash=log.transaction_hash,
                )
                continue
            if log_address != self._address:
                continue

            # Skip if no topics (anonymous event)
            if not log.topics:
                continue

            topic0 = log.topics[0]
            if topic0.startswith("0x"):
                topic0 = topic0[2:]
            topic0 = topic0.lower()

            # Find matching event ABI
            for event_name, event_abi in self._event_abis.items():
                expected_sig = event_abi_to_log_topic(event_abi)
                expected_sig_hex = expected_sig.hex().lower()

                if topic0 == expected_sig_hex:
                    try:
                        decoded = self._decode_log(log, event_name, event_abi)
                        if event_name not in result:
                            result[event_name] = []
                        result[event_name].append(decoded)
                    except Exception as e:
                        # RECOVERABLE decoding failures skip individual logs.
                        log_unexpected(
                            logger,
                            "events.decode_log_failed",
                            event_name=event_name,
                            tx_hash=log.transaction_hash,
                            log_index=log.log_index,
                            error=str(e)[:200],
                        )
                        continue
                    break

        self._decoded_cache = result
        return result

    def _decode_log(
        self,
        log: LogEntry,
        event_name: str,
        event_abi: dict[str, Any],
    ) -> DecodedEvent:
        """Decode a single log entry."""
        inputs = event_abi.get("inputs", [])

        # Separate indexed and non-indexed parameters
        indexed_inputs = [i for i in inputs if i.get("indexed", False)]
        non_indexed_inputs = [i for i in inputs if not i.get("indexed", False)]

        # Decode indexed parameters from topics (skip topic0 which is signature)
        indexed_values = []
        for i, param in enumerate(indexed_inputs):
            topic_index = i + 1  # +1 because topic0 is the event signature
            if topic_index < len(log.topics):
                topic = log.topics[topic_index]
                if topic.startswith("0x"):
                    topic = topic[2:]
                # Indexed parameters are 32 bytes each
                topic_bytes = bytes.fromhex(topic)
                indexed_values.append(
                    self._decode_indexed_param(param["type"], topic_bytes)
                )
            else:
                indexed_values.append(None)

        # Decode non-indexed parameters from data
        non_indexed_values = []
        if non_indexed_inputs and log.data and log.data != "0x":
            data_bytes = bytes.fromhex(log.data[2:] if log.data.startswith("0x") else log.data)
            if data_bytes:
                types = [i["type"] for i in non_indexed_inputs]
                try:
                    non_indexed_values = list(abi_decode(types, data_bytes))
                except Exception as e:
                    # RECOVERABLE decoding failures fall back to None values.
                    log_unexpected(
                        logger,
                        "events.decode_non_indexed_failed",
                        event_name=event_name,
                        tx_hash=log.transaction_hash,
                        log_index=log.log_index,
                        error=str(e)[:200],
                    )
                    non_indexed_values = [None] * len(non_indexed_inputs)

        # Build args dict
        args = AttributeDict()
        indexed_idx = 0
        non_indexed_idx = 0

        for param in inputs:
            name = param.get("name", f"arg{indexed_idx + non_indexed_idx}")
            if param.get("indexed", False):
                value = indexed_values[indexed_idx] if indexed_idx < len(indexed_values) else None
                indexed_idx += 1
            else:
                value = non_indexed_values[non_indexed_idx] if non_indexed_idx < len(non_indexed_values) else None
                non_indexed_idx += 1

            # Convert bytes to hex strings for readability
            if isinstance(value, bytes):
                value = HexBytes(value)
            args[name] = value

        tx_hash = normalize_tx_hash(log.transaction_hash) or ""

        return DecodedEvent(
            name=event_name,
            args=args,
            address=self._address,
            tx_hash=tx_hash,
            log_index=log.log_index,
            block_number=log.block_number,
            raw_log=log,
        )

    def _decode_indexed_param(self, param_type: str, data: bytes) -> Any:
        """Decode an indexed parameter from topic bytes."""
        # For dynamic types (string, bytes, arrays), indexed params are just keccak256 hashes
        if param_type in ("string", "bytes") or param_type.endswith("[]"):
            return HexBytes(data)

        # For static types, decode normally
        try:
            decoded = abi_decode([param_type], data.rjust(32, b"\x00"))
            return decoded[0] if decoded else None
        except Exception:
            # RECOVERABLE decoding failures fall back to raw data.
            log_unexpected(
                logger,
                "events.decode_indexed_failed",
                param_type=param_type,
            )
            return HexBytes(data)

    def __getitem__(self, event_name: str) -> list[DecodedEvent]:
        """Get all events with the given name.

        Args:
            event_name: Name of the event (e.g., 'Transfer')

        Returns:
            List of decoded events, in log_index order

        Raises:
            KeyError: If event name is not in the ABI
            ReceiptRequiredError: If accessed outside alert_confirmed context
        """
        if event_name not in self._event_abis:
            available = list(self._event_abis.keys())
            raise KeyError(
                f"Event '{event_name}' not found in ABI for {self._address}. "
                f"Available events: {available}"
            )

        decoded = self._decode_all_events()
        return decoded.get(event_name, [])

    def one(self, event_name: str) -> DecodedEvent:
        """Get exactly one event with the given name.

        Args:
            event_name: Name of the event

        Returns:
            The single decoded event

        Raises:
            EventNotFoundError: If zero or more than one event found
        """
        events = self[event_name]
        if len(events) == 0:
            decoded = self._decode_all_events()
            available = list(decoded.keys())
            raise EventNotFoundError(event_name, self._address, available)
        if len(events) > 1:
            raise EventNotFoundError(
                event_name,
                self._address,
                [f"{event_name} (found {len(events)}, expected 1)"],
            )
        return events[0]

    def first(self, event_name: str) -> DecodedEvent | None:
        """Get the first event with the given name, or None.

        Args:
            event_name: Name of the event

        Returns:
            The first decoded event or None if not found
        """
        events = self[event_name]
        return events[0] if events else None

    def get(self, event_name: str, default: DecodedEvent | None = None) -> DecodedEvent | None:
        """Get the first event with the given name, or return default.

        Args:
            event_name: Name of the event
            default: Value to return when no events are found
        """
        events = self[event_name]
        return events[0] if events else default

    def count(self, event_name: str) -> int:
        """Count events with the given name."""
        return len(self[event_name])

    def all(self, event_name: str) -> list[DecodedEvent]:
        """Get all events with the given name.

        Alias for __getitem__ with clearer intent.

        Args:
            event_name: Name of the event

        Returns:
            List of decoded events (may be empty)
        """
        return self[event_name]

    def __iter__(self) -> Iterator[DecodedEvent]:
        """Iterate over all decoded events from this contract."""
        decoded = self._decode_all_events()
        all_events: list[DecodedEvent] = []
        for event_list in decoded.values():
            all_events.extend(event_list)
        # Sort by log_index for consistent ordering
        all_events.sort(key=lambda e: e.log_index)
        return iter(all_events)

    def __len__(self) -> int:
        """Return total number of decoded events from this contract."""
        decoded = self._decode_all_events()
        return sum(len(events) for events in decoded.values())

    @property
    def available(self) -> list[str]:
        """List all event names that were found in the receipt."""
        decoded = self._decode_all_events()
        return list(decoded.keys())

    @property
    def defined(self) -> list[str]:
        """List all event names defined in the ABI."""
        return list(self._event_abis.keys())


# =============================================================================
# Brownie-Compatible Event Containers
# =============================================================================


class _EventItem:
    """Container for one or more events with the same name.

    Brownie-compatible access patterns:
        events["Transfer"][0]        # First Transfer event
        events["Transfer"]["amount"] # Field from first Transfer
        len(events["Transfer"])      # Count of Transfer events
        "amount" in events["Transfer"]  # Check field exists
    """

    def __init__(
        self,
        name: str,
        events: list[dict[str, Any]],
        addresses: list[str],
        positions: list[int],
    ):
        self.name = name
        self._events = events
        self._addresses = addresses
        self.pos = tuple(positions)

    @property
    def address(self) -> str | None:
        """Contract address. None if events from multiple addresses."""
        unique = set(self._addresses)
        return self._addresses[0] if len(unique) == 1 else None

    def __getitem__(self, key: int | str) -> Any:
        if isinstance(key, int):
            return self._events[key]
        return self._events[0][key]

    def __len__(self) -> int:
        return len(self._events)

    def __contains__(self, key: str) -> bool:
        return key in self._events[0] if self._events else False

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._events)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _EventItem):
            return self._events == other._events
        return False

    def keys(self):
        return self._events[0].keys() if self._events else []

    def values(self):
        return self._events[0].values() if self._events else []

    def items(self):
        return self._events[0].items() if self._events else []

    def __repr__(self) -> str:
        if len(self._events) == 1:
            return f"<{self.name} {dict(self._events[0])}>"
        return f"<{self.name} [{len(self._events)} events]>"


class EventDict:
    """Brownie-compatible event container.

    Hybrid dict/list access:
        events[0]              # First event by position
        events["Transfer"]     # All Transfer events (_EventItem)
        events["Transfer"][0]  # First Transfer event
        len(events)            # Total event count
        "Transfer" in events   # Check if event type exists
        for event in events:   # Iterate all events
    """

    def __init__(self, events: list[dict[str, Any]] | None = None):
        self._ordered: list[_EventItem] = []
        self._by_name: dict[str, _EventItem] = {}

        if events:
            self._build_index(events)

    def _build_index(self, events: list[dict[str, Any]]) -> None:
        """Build internal indexes from decoded events."""
        by_name: dict[str, list[dict[str, Any]]] = {}
        by_name_addrs: dict[str, list[str]] = {}
        by_name_pos: dict[str, list[int]] = {}

        for i, event in enumerate(events):
            name = event.get("_name", "Unknown")
            if name not in by_name:
                by_name[name] = []
                by_name_addrs[name] = []
                by_name_pos[name] = []

            # Extract event args (everything except _name and _address)
            args = {k: v for k, v in event.items() if not k.startswith("_")}

            by_name[name].append(args)
            by_name_addrs[name].append(event.get("_address", ""))
            by_name_pos[name].append(i)

        # Build _EventItem for each name
        for name in by_name:
            item = _EventItem(
                name=name,
                events=by_name[name],
                addresses=by_name_addrs[name],
                positions=by_name_pos[name],
            )
            self._by_name[name] = item

        # Build ordered list (one _EventItem per event occurrence)
        for i, event in enumerate(events):
            name = event.get("_name", "Unknown")
            idx = by_name_pos[name].index(i)
            single_item = _EventItem(
                name=name,
                events=[by_name[name][idx]],
                addresses=[by_name_addrs[name][idx]],
                positions=[i],
            )
            self._ordered.append(single_item)

    def __getitem__(self, key: int | str) -> _EventItem:
        if isinstance(key, int):
            return self._ordered[key]
        if key not in self._by_name:
            raise KeyError(f"Event '{key}' not found. Available: {list(self._by_name.keys())}")
        return self._by_name[key]

    def __len__(self) -> int:
        return len(self._ordered)

    def __contains__(self, key: str) -> bool:
        return key in self._by_name

    def __iter__(self) -> Iterator[_EventItem]:
        return iter(self._ordered)

    def __bool__(self) -> bool:
        return len(self._ordered) > 0

    def count(self, name: str) -> int:
        """Count events of a specific type."""
        if name not in self._by_name:
            return 0
        return len(self._by_name[name])

    def keys(self):
        return self._by_name.keys()

    def values(self):
        return self._by_name.values()

    def items(self):
        return self._by_name.items()

    def __repr__(self) -> str:
        if not self._ordered:
            return "<EventDict (empty)>"
        names = [f"{k}({len(v)})" for k, v in self._by_name.items()]
        return f"<EventDict {', '.join(names)}>"


def decode_logs(
    logs: list[dict[str, Any]],
    contract_system: Any,
) -> EventDict:
    """Decode receipt logs into EventDict.

    Args:
        logs: Raw logs from transaction receipt
        contract_system: For ABI resolution

    Returns:
        EventDict with all decoded events
    """
    if not logs:
        return EventDict([])

    # Get unique addresses and resolve ABIs
    addresses = {log.get("address") for log in logs if log.get("address")}
    abis_by_addr: dict[str, list[dict[str, Any]]] = {}

    for addr in addresses:
        if addr:
            try:
                resolved = contract_system.resolver().resolve(addr)
                abis_by_addr[addr.lower()] = resolved.abi
            except Exception as e:
                # RECOVERABLE ABI resolution failures fall back to empty ABI.
                log_unexpected(
                    logger,
                    "events.abi_resolve_failed",
                    address=addr,
                    error=str(e)[:200],
                )
                abis_by_addr[addr.lower()] = []

    # Build topic -> event ABI mapping
    topic_to_event: dict[bytes, tuple[str, dict[str, Any]]] = {}
    for addr, abi in abis_by_addr.items():
        for item in abi:
            if item.get("type") == "event":
                topic = event_abi_to_log_topic(item)
                topic_to_event[topic] = (addr, item)

    # Decode each log
    decoded_events: list[dict[str, Any]] = []
    for log in logs:
        topics = log.get("topics", [])
        if not topics:
            continue

        # Get first topic (event signature)
        topic0 = topics[0]
        if isinstance(topic0, (bytes, HexBytes)):
            topic0_bytes = bytes(topic0)
        elif isinstance(topic0, str):
            topic0_bytes = bytes.fromhex(topic0[2:] if topic0.startswith("0x") else topic0)
        else:
            continue

        if topic0_bytes not in topic_to_event:
            continue

        _, event_abi = topic_to_event[topic0_bytes]

        try:
            decoded = _decode_single_event(log, event_abi)
            decoded["_address"] = log.get("address", "")
            decoded["_name"] = event_abi["name"]
            decoded_events.append(decoded)
        except Exception as e:
            # RECOVERABLE decoding failures skip individual logs.
            log_unexpected(
                logger,
                "events.decode_event_failed",
                event_name=event_abi.get("name"),
                tx_hash=normalize_tx_hash(log.get("transactionHash")),
                log_index=log.get("logIndex"),
                error=str(e)[:200],
            )
            continue

    return EventDict(decoded_events)


def _decode_single_event(log: dict[str, Any], event_abi: dict[str, Any]) -> dict[str, Any]:
    """Decode a single event log into a flat dict."""
    topics = log.get("topics", [])
    data = log.get("data", "0x")

    if isinstance(data, (bytes, HexBytes)):
        data_bytes = bytes(data)
    elif isinstance(data, str):
        data_bytes = bytes.fromhex(data[2:] if data.startswith("0x") else data) if data and data != "0x" else b""
    else:
        data_bytes = b""

    # Separate indexed and non-indexed inputs
    indexed_inputs = [inp for inp in event_abi.get("inputs", []) if inp.get("indexed")]
    non_indexed_inputs = [inp for inp in event_abi.get("inputs", []) if not inp.get("indexed")]

    # Decode indexed params from topics (skip topic[0] which is signature)
    indexed_values: list[Any] = []
    for i, inp in enumerate(indexed_inputs):
        if i + 1 < len(topics):
            topic = topics[i + 1]
            if isinstance(topic, str):
                topic = bytes.fromhex(topic[2:] if topic.startswith("0x") else topic)
            elif isinstance(topic, (bytes, HexBytes)):
                topic = bytes(topic)

            # For dynamic types, indexed params are just hashes
            if inp["type"] in ("string", "bytes") or inp["type"].endswith("[]"):
                indexed_values.append(HexBytes(topic))
            else:
                try:
                    decoded = abi_decode([inp["type"]], topic.rjust(32, b"\x00"))
                    indexed_values.append(decoded[0])
                except Exception:
                    # RECOVERABLE decoding failures fall back to raw topic.
                    log_unexpected(
                        logger,
                        "events.decode_indexed_failed",
                        param_type=inp.get("type"),
                    )
                    indexed_values.append(HexBytes(topic))
        else:
            indexed_values.append(None)

    # Decode non-indexed params from data
    non_indexed_values: list[Any] = []
    if non_indexed_inputs and data_bytes:
        types = [inp["type"] for inp in non_indexed_inputs]
        try:
            non_indexed_values = list(abi_decode(types, data_bytes))
        except Exception:
            # RECOVERABLE decoding failures fall back to None values.
            log_unexpected(
                logger,
                "events.decode_non_indexed_failed",
                event_name=event_abi.get("name"),
            )
            non_indexed_values = [None] * len(non_indexed_inputs)

    # Build result dict
    result: dict[str, Any] = {}
    idx_i, non_idx_i = 0, 0
    for inp in event_abi.get("inputs", []):
        name = inp.get("name", f"arg{idx_i + non_idx_i}")
        if inp.get("indexed"):
            value = indexed_values[idx_i] if idx_i < len(indexed_values) else None
            idx_i += 1
        else:
            value = non_indexed_values[non_idx_i] if non_idx_i < len(non_indexed_values) else None
            non_idx_i += 1

        # Convert bytes to HexBytes for consistency
        if isinstance(value, bytes) and not isinstance(value, HexBytes):
            value = HexBytes(value)
        result[name] = value

    return result
