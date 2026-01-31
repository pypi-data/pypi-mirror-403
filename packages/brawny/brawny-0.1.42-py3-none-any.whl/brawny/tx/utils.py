"""Transaction utilities."""

# Fields that must be integers for Ethereum transactions
TX_INT_FIELDS = {
    "nonce",
    "gas",
    "gasPrice",
    "maxFeePerGas",
    "maxPriorityFeePerGas",
    "chainId",
    "value",
    "type",
}


def normalize_tx_dict(tx: dict) -> dict:
    """
    Normalize transaction dict for signing.

    Converts numeric fields to integers (allows brownie-like float inputs).
    """
    result = dict(tx)
    for field in TX_INT_FIELDS:
        if field in result and result[field] is not None:
            result[field] = int(result[field])
    return result
