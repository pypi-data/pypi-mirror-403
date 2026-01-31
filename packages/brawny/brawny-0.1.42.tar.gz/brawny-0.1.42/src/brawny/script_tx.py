"""Transaction broadcasting for standalone scripts.

Simpler flow than job-based execution:
- No intent persistence
- No replacement/monitoring
- Direct broadcast and wait
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import time

from brawny.tx.utils import normalize_tx_dict
from brawny.logging import get_logger, log_unexpected

if TYPE_CHECKING:
    from brawny.keystore import Keystore
    from brawny._rpc.clients import BroadcastClient
    from brawny.jobs.base import TxReceipt


logger = get_logger(__name__)


class TransactionBroadcaster:
    """Broadcasts transactions for script context.

    Uses brawny RPC infrastructure (retry, failover) but
    simpler execution flow than job-based TxExecutor.
    """

    def __init__(
        self,
        rpc: "BroadcastClient",
        keystore: "Keystore",
        chain_id: int,
        timeout_seconds: int = 120,
        poll_interval: float = 1.0,
    ) -> None:
        self._rpc = rpc
        self._keystore = keystore
        self._chain_id = chain_id
        self._timeout = timeout_seconds
        self._poll_interval = poll_interval

    def transfer(
        self,
        sender: str,
        to: str,
        value: int,
        gas_limit: int | None = None,
        gas_price: int | None = None,
        max_fee_per_gas: int | None = None,
        max_priority_fee_per_gas: int | None = None,
        data: str | None = None,
        nonce: int | None = None,
        private_key: bytes | None = None,
    ) -> "TxReceipt":
        """Send a transfer transaction.

        Args:
            sender: Sender address
            to: Recipient address
            value: Amount in wei
            gas_limit: Optional gas limit
            gas_price: Optional legacy gas price
            max_fee_per_gas: Optional EIP-1559 max fee
            max_priority_fee_per_gas: Optional EIP-1559 priority fee
            data: Optional calldata
            nonce: Optional nonce override
            private_key: Optional private key for signing (from Account).
                        If None, uses the keystore to sign.

        Returns:
            Transaction receipt on confirmation

        Raises:
            TransactionRevertedError: If transaction reverts
            TransactionTimeoutError: If confirmation times out
        """
        from brawny.history import _add_to_history

        # Build transaction
        tx = self._build_transaction(
            sender=sender,
            to=to,
            value=value,
            data=data or "0x",
            gas_limit=gas_limit,
            gas_price=gas_price,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            nonce=nonce,
        )

        # Sign and broadcast
        receipt = self._sign_and_broadcast(tx, sender, private_key)

        # Add to history
        _add_to_history(receipt)

        return receipt

    def transact(
        self,
        sender: str,
        to: str,
        data: str,
        value: int = 0,
        gas_limit: int | None = None,
        gas_price: int | None = None,
        max_fee_per_gas: int | None = None,
        max_priority_fee_per_gas: int | None = None,
        nonce: int | None = None,
        private_key: bytes | None = None,
    ) -> "TxReceipt":
        """Send a contract transaction.

        Args:
            sender: Sender address
            to: Contract address
            data: Encoded calldata
            value: Optional ETH value in wei
            gas_limit: Optional gas limit
            gas_price: Optional legacy gas price
            max_fee_per_gas: Optional EIP-1559 max fee
            max_priority_fee_per_gas: Optional EIP-1559 priority fee
            nonce: Optional nonce override
            private_key: Optional private key for signing (from Account).
                        If None, uses the keystore to sign.

        Returns:
            Transaction receipt on confirmation
        """
        from brawny.history import _add_to_history

        tx = self._build_transaction(
            sender=sender,
            to=to,
            value=value,
            data=data,
            gas_limit=gas_limit,
            gas_price=gas_price,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            nonce=nonce,
        )

        receipt = self._sign_and_broadcast(tx, sender, private_key)
        _add_to_history(receipt)

        return receipt

    def _build_transaction(
        self,
        sender: str,
        to: str,
        value: int,
        data: str,
        gas_limit: int | None,
        gas_price: int | None,
        max_fee_per_gas: int | None,
        max_priority_fee_per_gas: int | None,
        nonce: int | None,
    ) -> dict[str, Any]:
        """Build transaction dictionary."""
        tx: dict[str, Any] = {
            "from": sender,
            "to": to,
            "value": value,
            "data": data,
            "chainId": self._chain_id,
        }

        # Nonce
        if nonce is None:
            nonce = self._rpc.get_transaction_count(sender, "pending")
        tx["nonce"] = nonce

        # Gas price (EIP-1559 or legacy)
        if max_fee_per_gas is not None:
            tx["maxFeePerGas"] = max_fee_per_gas
            tx["maxPriorityFeePerGas"] = max_priority_fee_per_gas or 0
            tx["type"] = 2
        elif gas_price is not None:
            tx["gasPrice"] = gas_price
        else:
            # Auto gas price
            try:
                base_fee = self._rpc.get_block("latest").get("baseFeePerGas")
                if base_fee:
                    # EIP-1559
                    priority = self._rpc.call("eth_maxPriorityFeePerGas")
                    tx["maxFeePerGas"] = base_fee * 2 + int(priority, 16)
                    tx["maxPriorityFeePerGas"] = int(priority, 16)
                    tx["type"] = 2
                else:
                    tx["gasPrice"] = self._rpc.get_gas_price()
            except Exception as e:
                # RECOVERABLE fall back to legacy gas price if fee lookup fails.
                log_unexpected(
                    logger,
                    "script_tx.gas_fee_lookup_failed",
                    error=str(e)[:200],
                )
                tx["gasPrice"] = self._rpc.get_gas_price()

        # Gas limit
        if gas_limit is None:
            estimate_tx = {k: v for k, v in tx.items() if k != "nonce"}
            gas_limit = self._rpc.estimate_gas(estimate_tx)
            gas_limit = gas_limit * 1.1  # 10% buffer
        tx["gas"] = gas_limit

        return normalize_tx_dict(tx)

    def _sign_and_broadcast(
        self,
        tx: dict[str, Any],
        sender: str,
        private_key: bytes | None = None,
    ) -> "TxReceipt":
        """Sign transaction and broadcast, waiting for receipt.

        Args:
            tx: Transaction dictionary
            sender: Sender address
            private_key: Optional private key for direct signing (from Account).
                        If None, uses the keystore to sign.
        """
        from brawny.jobs.base import TxReceipt
        from brawny.scripting import TransactionRevertedError, TransactionTimeoutError
        from eth_account import Account as EthAccount

        # Sign - either with private key or keystore
        if private_key is not None:
            signed = EthAccount.sign_transaction(tx, private_key)
        else:
            signed = self._keystore.sign_transaction(tx, sender)

        # Broadcast (handle both old and new eth-account attribute names)
        raw_tx = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = self._rpc.send_raw_transaction(raw_tx)

        # Wait for receipt
        start = time.time()
        while True:
            receipt_data = self._rpc.get_transaction_receipt(tx_hash)
            if receipt_data is not None:
                # Handle status as hex string or int
                status = receipt_data["status"]
                if isinstance(status, str):
                    status = int(status, 16)

                # Handle block_number as hex string or int
                block_number = receipt_data["blockNumber"]
                if isinstance(block_number, str):
                    block_number = int(block_number, 16)

                # Handle gas_used as hex string or int
                gas_used = receipt_data["gasUsed"]
                if isinstance(gas_used, str):
                    gas_used = int(gas_used, 16)

                receipt = TxReceipt(
                    transaction_hash=receipt_data["transactionHash"],
                    block_number=block_number,
                    block_hash=receipt_data["blockHash"],
                    status=status,
                    gas_used=gas_used,
                    logs=receipt_data.get("logs", []),
                )

                if receipt.status == 0:
                    raise TransactionRevertedError(tx_hash)

                return receipt

            if time.time() - start > self._timeout:
                raise TransactionTimeoutError(tx_hash, self._timeout)

            time.sleep(self._poll_interval)


# Global broadcaster instance
_broadcaster: TransactionBroadcaster | None = None


def _init_broadcaster(
    rpc: "BroadcastClient",
    keystore: "Keystore",
    chain_id: int,
) -> None:
    """Initialize global broadcaster."""
    global _broadcaster
    _broadcaster = TransactionBroadcaster(rpc, keystore, chain_id)


def _get_broadcaster() -> TransactionBroadcaster:
    """Get broadcaster singleton."""
    if _broadcaster is None:
        raise RuntimeError(
            "Transaction broadcaster not initialized. "
            "Run within script context."
        )
    return _broadcaster
