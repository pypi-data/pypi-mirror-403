"""Alert routing resolution.

Resolves named targets to chat IDs for Telegram alerts.
Could be extended for webhooks later.

Policy: Startup fails hard, runtime logs + drops.
- Startup validation catches typos during normal deployment
- Runtime unknown names log error and are skipped (not raised)
- This prevents hot-edited typos from crashing hook execution
"""

from __future__ import annotations

from brawny.logging import get_logger

logger = get_logger(__name__)

def is_chat_id(s: str) -> bool:
    """Check if string looks like a raw Telegram chat ID.

    Handles:
    - Supergroups/channels: -100...
    - Basic groups: negative ints -12345
    - User IDs: positive ints
    """
    return s.lstrip("-").isdigit()


def resolve_targets(
    target: str | list[str] | None,
    chats: dict[str, str],
    default: list[str],
    *,
    job_id: str | None = None,
) -> list[str]:
    """Resolve target(s) to deduplicated list of chat IDs.

    Policy: Startup fails hard, runtime logs + drops.
    - Startup validation catches typos during normal deployment
    - Runtime unknown names log error and are skipped (not raised)
    - This prevents hot-edited typos from crashing hook execution

    Args:
        target: Chat name, raw ID, list of either, or None
        chats: Name -> chat_id mapping from config
        default: Default chat names/IDs if target is None
        job_id: Optional job ID for logging context

    Returns:
        Deduplicated list of resolved chat IDs (preserves order).
        Unknown names are logged and skipped, not raised.
    """
    if target is None:
        targets = default
    elif isinstance(target, str):
        targets = [target]
    else:
        targets = target

    # Resolve names to IDs, dedupe while preserving order
    seen: set[str] = set()
    result: list[str] = []

    for t in targets:
        t = t.strip()
        if not t:
            continue

        # Resolve: raw ID passes through, named chat looks up, unknown logs + skips
        if is_chat_id(t):
            chat_id = t
        elif t in chats:
            chat_id = chats[t]
        else:
            # Log and skip unknown names (don't crash hooks at runtime)
            logger.error(
                "alert.routing.unknown_target",
                target=t,
                job_id=job_id,
                valid_names=sorted(chats.keys()),
            )
            continue

        if chat_id not in seen:
            seen.add(chat_id)
            result.append(chat_id)

    return result


def validate_targets(
    target: str | list[str] | None,
    valid_names: set[str],
    *,
    allow_ids: bool = True,
) -> list[str]:
    """Validate that all non-ID targets are valid chat names.

    Used at startup for hard failure on unknown names.

    Args:
        target: Chat name, raw ID, list of either, or None
        valid_names: Set of valid chat names from config

    Returns:
        List of invalid names (empty if all valid)
    """
    if target is None:
        return []

    targets = [target] if isinstance(target, str) else target
    invalid: list[str] = []

    for t in targets:
        t = t.strip()
        if not t:
            continue
        if is_chat_id(t):
            if not allow_ids:
                invalid.append(t)
            continue
        if t not in valid_names:
            invalid.append(t)

    return invalid
