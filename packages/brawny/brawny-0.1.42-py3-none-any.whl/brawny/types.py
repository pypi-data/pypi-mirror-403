"""Shared runtime types for brawny."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ClaimedIntent:
    """Minimal context for a claimed intent."""

    intent_id: UUID
    claim_token: str
    claimed_by: str | None
    lease_expires_at: datetime | None
    claimed_at: datetime
