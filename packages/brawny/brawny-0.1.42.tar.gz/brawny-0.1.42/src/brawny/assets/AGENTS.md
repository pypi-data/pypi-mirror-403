# Agent Guide: Build a Compliant brawny Job

This file is meant for user agents that generate new job files. It is a fast, practical spec.

## Golden Rules
- Avoid over-engineering.
- Aim for simplicity and elegance.

## Job File Checklist (Minimal)
- Location: `jobs/<job_name>.py`
- Import `Job` and `job`.
- Add `@job` decorator (omit it to hide a WIP job from discovery/validation).
- Implement `check()` (sync or async).
- If it sends a transaction, implement `build_intent()` (sync).

## Required vs Optional Hooks

### Required
- `check(self) -> Trigger | None` OR `check(self, ctx) -> Trigger | None`
  - Must return `trigger(...)` or `None`.
  - **Implicit style** `def check(self):` - use API helpers (`block`, `kv`, `Contract`, `ctx()`).
  - **Explicit style** `def check(self, ctx):` - ctx passed directly (param MUST be named 'ctx').
  - Can be async: `async def check(self)` or `async def check(self, ctx)`.

### Required only for tx jobs
- `build_intent(self, trigger) -> TxIntentSpec`
  - Build calldata and return `intent(...)`.
  - Only called if `trigger.tx_required` is True.

### Optional lifecycle hooks (for alerts and custom logic)
- `on_trigger(self, ctx: TriggerContext)` - Called when job triggers, BEFORE build_intent().
- `on_success(self, ctx: SuccessContext)` - Called after TX confirms.
- `on_failure(self, ctx: FailureContext)` - Called on failure (ctx.intent may be None pre-intent).

All hooks have `ctx.alert(message)` for sending alerts to job destinations.

## Job Class Attributes

### Required (auto-derived if not set and @job is used)
- `job_id: str` - Stable identifier (must not change).
- `name: str` - Human-readable name for logs/alerts.

### Optional scheduling
- `check_interval_blocks: int = 1` - Min blocks between check() calls.
- `check_timeout_seconds: int = 30` - Timeout for check().
- `build_timeout_seconds: int = 10` - Timeout for build_intent().
- `max_in_flight_intents: int | None = None` - Cap on active intents.

### Optional gas overrides (all values in wei)
- `max_fee: int | None = None` - Max fee cap for gating/txs (None = no gating).
- `priority_fee: int | None = None` - Tip override for this job.

### Optional send override
- `rpc: str | None = None` - Override broadcast endpoint for send only.

### Broadcast routing (via @job decorator)
Configure broadcast routing using the `@job` decorator:
```python
@job(job_id="arb_exec", rpc_group="flashbots", signer="hot1")
class ArbitrageExecutor(Job):
    ...
```
- `job_id` - Optional override (defaults to snake_case of class name).
- `rpc_group` - Name of RPC group for reads and broadcasts.
- `broadcast_group` - Name of RPC group for broadcasts (default: uses rpc.defaults.broadcast).
- `read_group` - Name of RPC group for read operations (default: uses rpc.defaults.read).
- `signer` - Name of signer alias (required for tx jobs).

Define RPC groups in config:
```yaml
rpc:
  groups:
    primary:
      endpoints:
        - https://eth.llamarpc.com
    private:
      endpoints:
        - https://rpc.flashbots.net
        - https://relay.flashbots.net
  defaults:
    read: primary
    broadcast: private
```

### Alert routing
- System/lifecycle alerts always route to `telegram.admin` (required).
- Job alerts (`ctx.alert()` / `alert()`) route to job destinations or defaults.
- `@job(alert_to="ops")` - Route alerts to a named chat in config.
- `@job(alert_to=["ops", "dev"])` - Route to multiple chats.
- Names must be defined in `telegram.chats`.
- If not specified, routes to `telegram.default`, then `telegram.public`.

## Core API (What to Use)

### Contract access (brownie-style)
```python
from brawny import Contract
vault = Contract(self.vault_address)  # By address
decimals = vault.decimals()            # View call
data = vault.harvest.encode_input()    # Get calldata
```

### Multicall (batch eth_call)
```python
from brawny import multicall, Contract

operator = Contract("0x...")
mc = Contract("0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696")
results = {}
with multicall(address=mc.address):
    for amt in amounts:
        results[amt] = operator.isProfitable(amt, crvusd)
```
- Default address can come from `BRAWNY_MULTICALL2` or `~/.brawny/network-config.yaml` (by chain_id).
- Pass `address=...` explicitly to override.

### JSON interfaces (brownie-style)
Place ABI JSON files in `./interfaces`, then:
```python
from brawny import interface
token = interface.IERC20("0x1234...")
balance = token.balanceOf("0xabc...")
```

### Job hook helpers (implicit context)
```python
from brawny import trigger, intent, block, gas_ok
return trigger(reason="...", data={...}, idempotency_parts=[block.number])
return intent(signer_address="worker", to_address=addr, data=calldata)
```

### Event access in lifecycle hooks
```python
def on_success(self, ctx: SuccessContext):
    if ctx.events:
        deposit = ctx.events[0]         # First decoded event
        amount = deposit["amount"]      # Field access
        ctx.alert(f"Deposited {amount}")
```

### Other context access
- `ctx()` - Get full CheckContext/BuildContext when using implicit style.
- `block.number`, `block.timestamp` - Current block info.
- `rpc.*` - RPC manager proxy (e.g., `rpc.get_gas_price()`).
- `ctx.http` - Approved HTTP client for external calls.
- `gas_ok()` - Check if current gas is below job's max_fee (async).
- `gas_quote()` - Get current base_fee (async).
- `kv.get(key, default=None)`, `kv.set(key, value)` - Persistent KV store (import from brawny).

### Network access
- External HTTP calls must use `ctx.http` (ApprovedHttpClient).
- Direct network calls via `requests`, `urllib`, or raw `httpx` are blocked by network_guard.

### Accounts
- Use `intent(signer_address=...)` with a signer alias or address.
- If you set `@job(signer="alias")`, use `self.signer` (alias) or `self.signer_address` (resolved address).
- The signer alias must exist in the accounts directory (`~/.brawny/accounts`).

## Example: Transaction Job

```python
from brawny import Job, job, Contract, trigger, intent, block

@job(signer="worker")
class MyKeeperJob(Job):
    job_id = "my_keeper"
    name = "My Keeper"
    check_interval_blocks = 1
    keeper_address = "0x..."

    def check(self, ctx):
        keeper = Contract(self.keeper_address)
        if keeper.canWork():
            return trigger(
                reason="Keeper can work",
                idempotency_parts=[block.number],
            )
        return None

    def build_intent(self, trig):
        keeper = Contract(self.keeper_address)
        return intent(
            signer_address=self.signer,
            to_address=self.keeper_address,
            data=keeper.work.encode_input(),
        )
```

## Example: Job with Custom Broadcast and Alerts

```python
from brawny import Job, Contract, trigger, intent, explorer_link
from brawny.jobs.registry import job

@job(rpc_group="flashbots", signer="treasury-signer", alert_to="private_ops")
class TreasuryJob(Job):
    """Critical treasury operations with dedicated RPC and private alerts."""

    name = "Treasury Operations"
    check_interval_blocks = 1
    treasury_address = "0x..."

    def check(self, ctx):
        treasury = Contract(self.treasury_address)
        if treasury.needsRebalance():
            return trigger(reason="Treasury needs rebalancing")
        return None

    def build_intent(self, trig):
        treasury = Contract(self.treasury_address)
        return intent(
            signer_address=self.signer,
            to_address=self.treasury_address,
            data=treasury.rebalance.encode_input(),
        )

    def on_success(self, ctx):
        ctx.alert(f"Treasury rebalanced: {explorer_link(ctx.receipt.transactionHash)}")
```

## Example: Monitor-Only Job (Implicit Context Style)

```python
from brawny import Job, job, Contract, trigger, kv

@job
class MonitorJob(Job):
    job_id = "monitor"
    name = "Monitor"

    def check(self):  # No ctx param - uses implicit context
        value = Contract("0x...").value()
        last = kv.get("last", 0)
        if value > last:
            kv.set("last", value)
            return trigger(
                reason="Value increased",
                data={"value": value},
                tx_required=False,
            )
        return None
```

## Natural-Language -> Job Translation Guide

When a user says:
- **"Check X every block"** -> `check_interval_blocks = 1`
- **"Only run if gas below Y"** -> set `max_fee` (wei) and use `await gas_ok()` in async check()
- **"Use signer Z"** -> `@job(signer="Z")` and use `self.signer` in `intent(...)`
- **"Alert on success/failure"** -> implement `on_success` / `on_failure` with `ctx.alert()`
- **"Remember last value"** -> use `kv.get/set` (import from brawny)
- **"Use Flashbots"** -> `@job(rpc_group="flashbots")` with flashbots group in config
- **"Send alerts to a channel"** -> `@job(alert_to="public")` with chat in config

## Failure Modes

The `on_failure` hook provides rich context about what failed and when.

### Failure Classification

**FailureType** (what failed):
- `SIMULATION_REVERTED` - TX would revert on-chain (permanent)
- `SIMULATION_NETWORK_ERROR` - RPC error during simulation (transient)
- `DEADLINE_EXPIRED` - Intent took too long (permanent)
- `SIGNER_FAILED` - Keystore/signer issue
- `NONCE_FAILED` - Couldn't reserve nonce
- `SIGN_FAILED` - Signing error
- `BROADCAST_FAILED` - RPC rejected transaction (transient)
- `TX_REVERTED` - On-chain revert (permanent)
- `NONCE_CONSUMED` - Nonce used by another transaction
- `CHECK_EXCEPTION` - job.check() raised an exception
- `BUILD_TX_EXCEPTION` - job.build_tx() raised an exception
- `UNKNOWN` - Fallback for unexpected failures

Note: A send-boundary simulation failure triggers a single admin alert to
`telegram.admin` with `reason_code=stale_pre_broadcast` (job `alert_to` is ignored).
If you add custom `on_failure` alerts, avoid duplicates.

**FailureStage** (when it failed):
- `PRE_BROADCAST` - Failed before reaching the chain
- `BROADCAST` - Failed during broadcast
- `POST_BROADCAST` - Failed after broadcast (on-chain)

### FailureContext in on_failure

```python
# FailureContext fields
ctx.intent               # TxIntent | None (None for pre-intent failures)
ctx.attempt              # TxAttempt | None
ctx.error                # Exception that caused failure
ctx.failure_type         # FailureType enum
ctx.failure_stage        # FailureStage | None
ctx.block                # BlockContext
ctx.kv                   # KVReader (read-only)
ctx.logger               # Bound logger

# FailureContext methods
ctx.alert(message)       # Send alert to job destinations
```

### Example: Handling Failures

```python
from brawny import Job, job
from brawny.model.errors import FailureType
from brawny.model.contexts import FailureContext

@job
class RobustJob(Job):
    job_id = "robust_job"
    name = "Robust Job"

    def on_failure(self, ctx: FailureContext):
        # Suppress alerts for transient failures
        if ctx.failure_type in (
            FailureType.SIMULATION_NETWORK_ERROR,
            FailureType.BROADCAST_FAILED,
        ):
            return  # No alert for transient failures

        # Detailed message for permanent failures
        if ctx.failure_type == FailureType.SIMULATION_REVERTED:
            ctx.alert(f"TX would revert: {ctx.error}")
        elif ctx.failure_type == FailureType.TX_REVERTED:
            ctx.alert(f"TX reverted on-chain: {ctx.error}")
        elif ctx.failure_type == FailureType.NONCE_CONSUMED:
            ctx.alert("Nonce conflict! Check signer activity.")
        elif ctx.failure_type == FailureType.CHECK_EXCEPTION:
            ctx.alert(f"check() crashed: {ctx.error}")
        elif ctx.failure_type == FailureType.BUILD_TX_EXCEPTION:
            ctx.alert(f"build_intent() crashed: {ctx.error}")
        else:
            ctx.alert(f"Failed ({ctx.failure_type.value}): {ctx.error}")
```

## Required Output from Agent
When generating a new job file, the agent must provide:
- File path
- Job class name
- `job_id` and `name`
- `check()` implementation
- `build_intent()` if tx required
- Any alert hooks requested
