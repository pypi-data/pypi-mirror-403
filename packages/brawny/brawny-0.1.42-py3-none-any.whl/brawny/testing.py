"""Testing utilities for jobs with implicit context.

Provides helpers to set up the implicit context for unit testing jobs
without running the full framework.

Usage:
    from brawny.testing import job_context

    def test_my_job():
        job = MyJob()
        with job_context(job, block_number=1000) as ctx:
            result = job.check(ctx)
            assert result is not None
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Literal
from unittest.mock import MagicMock

from brawny._context import _job_ctx, _current_job, set_check_block, reset_check_block
from brawny.jobs.kv import InMemoryJobKVStore
from brawny.model.contexts import BlockContext, CheckContext

if TYPE_CHECKING:
    from brawny.jobs.base import Job


@contextmanager
def job_context(
    job: Job,
    block_number: int = 1000,
    chain_id: int = 1,
    block_hash: str | None = None,
    timestamp: int | None = None,
    rpc: Any | None = None,
    contract_system: Any | None = None,
    kv: Any | None = None,
    phase: Literal["check", "build", "alert"] = "check",
) -> Generator[CheckContext, None, None]:
    """Set up implicit context for testing job hooks.

    Creates a CheckContext and sets the contextvars so that implicit
    context functions (contract, trigger, tx, block) work correctly.

    Args:
        job: The job instance to test
        block_number: Block number for the context (default 1000)
        chain_id: Chain ID (default 1)
        block_hash: Block hash (default generates one)
        timestamp: Block timestamp (default 1700000000)
        rpc: RPC manager (default MagicMock)
        contract_system: Contract system for ContractFactory (default None)
        kv: KV store (default InMemoryJobKVStore)
        phase: Which phase to simulate. "check" pins reads to block_number,
               "build"/"alert" use latest (default: "check")

    Yields:
        The CheckContext for additional assertions or setup

    Example:
        from brawny import Contract, trigger
        from brawny.testing import job_context

        def test_harvest_check():
            job = HarvestJob()
            with job_context(job, block_number=12345) as ctx:
                # Implicit context is now available
                result = job.check(ctx)
                assert result is not None
    """
    from brawny.alerts.contracts import SimpleContractFactory

    block = BlockContext(
        number=block_number,
        timestamp=timestamp or 1700000000,
        hash=block_hash or ("0x" + "ab" * 32),
        base_fee=0,
        chain_id=chain_id,
    )

    # Build ContractFactory if contract_system provided
    contracts = SimpleContractFactory(contract_system) if contract_system else None

    ctx = CheckContext(
        block=block,
        kv=kv or InMemoryJobKVStore(),
        job_id=job.job_id,
        rpc=rpc or MagicMock(),
        http=MagicMock(),
        logger=MagicMock(),
        contracts=contracts,
        _db=None,
    )

    ctx_token = _job_ctx.set(ctx)
    job_token = _current_job.set(job)

    # Only pin block in check phase (matches real runner behavior)
    check_block_token = set_check_block(block_number) if phase == "check" else None

    try:
        yield ctx
    finally:
        if check_block_token is not None:
            reset_check_block(check_block_token)
        _job_ctx.reset(ctx_token)
        _current_job.reset(job_token)
