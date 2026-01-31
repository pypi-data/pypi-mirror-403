"""Fee calculation helpers for transaction management.

Provides shared fee bumping logic used by executor and replacement modules.
"""

from __future__ import annotations

from brawny.model.types import GasParams


def bump_fees(
    old_params: GasParams,
    bump_percent: float,
    max_fee_cap: int | None = None,
) -> GasParams:
    """Calculate bumped gas fees for replacement transactions.

    Per Ethereum protocol, replacement must have at least 10% higher fees.
    This function applies the configured bump percentage and enforces
    maximum fee caps on both max_fee and priority_fee.

    Args:
        old_params: Previous gas parameters
        bump_percent: Percentage to bump fees (e.g., 15 for 15%)
        max_fee_cap: Optional max fee cap in wei. If set, both
                     max_fee_per_gas and max_priority_fee_per_gas
                     will not exceed this value.

    Returns:
        New GasParams with bumped fees
    """
    # Use integer arithmetic to avoid float precision issues with large values
    bump_numerator = 100 + int(bump_percent)

    new_max_fee = (old_params.max_fee_per_gas * bump_numerator) // 100
    new_priority_fee = (old_params.max_priority_fee_per_gas * bump_numerator) // 100

    # Enforce max fee cap on BOTH fees if specified (already in wei)
    if max_fee_cap is not None:
        new_max_fee = min(new_max_fee, max_fee_cap)
        new_priority_fee = min(new_priority_fee, max_fee_cap)

    # Ensure priority fee never exceeds max fee (protocol requirement)
    new_priority_fee = min(new_priority_fee, new_max_fee)

    return GasParams(
        gas_limit=old_params.gas_limit,  # Keep same
        max_fee_per_gas=new_max_fee,
        max_priority_fee_per_gas=new_priority_fee,
    )
