# brawny

Block-driven Ethereum job and transaction execution framework, inspired by [eth-brownie](https://github.com/eth-brownie/brownie).

**Brownie-style ergonomics**: brawny mirrors Brownie's developer experience with familiar patterns—`accounts`, `Contract()`, `chain`, `history`, and an interactive console. If you've used Brownie, you'll feel right at home.

## Installation (Local Development)

```bash
# Clone and install the framework
git clone https://github.com/yearn/brawny.git
cd brawny
pip install -e .
```

## Quick Start

```bash
# Create a new keeper project
mkdir my-keeper && cd my-keeper
brawny init

# Install your project (brawny is already installed from above)
pip install -e .

# Configure
cp .env.example .env
# Edit .env: set RPC_URL and BRAWNY_KEYSTORE_PASSWORD_WORKER

# Import a signer key (will prompt for password)
brawny accounts import --name worker --private-key 0xYOUR_PRIVATE_KEY

# Run
brawny start
```

See `docs/quickstart.md` for a longer walkthrough.

## Project Structure

After `brawny init`, your project looks like:

```
my-keeper/
├── my_keeper/              # Your Python package
│   └── __init__.py
├── jobs/
│   ├── __init__.py
│   └── _examples.py        # Reference implementations (not registered)
├── interfaces/             # Place ABI JSON files here
├── monitoring/             # Prometheus + Grafana stack
│   ├── docker-compose.yml
│   └── grafana/...
├── pyproject.toml
├── config.yaml
├── .env.example
├── .gitignore
└── AGENTS.md               # AI agent guide for writing jobs
```

The `AGENTS.md` file contains a comprehensive guide for AI agents to generate correct, idiomatic jobs.

## Minimal Job Example

Create `jobs/harvester.py`:

```python
from brawny import Job, job, Contract, trigger, intent, block


@job(signer="worker")
class HarvestJob(Job):
    name = "Harvest Example"
    check_interval_blocks = 50
    vault_address = "0xYourVault"

    def check(self):
        vault = Contract(self.vault_address)
        pending = vault.pendingRewards()
        if pending > 1_000_000_000_000_000_000:
            return trigger(
                reason="Harvest pending rewards",
                data={"pending": pending},
                idempotency_parts=[block.number // 50],
            )
        return None

    def build_intent(self, trig):
        vault = Contract(self.vault_address)
        return intent(
            signer_address=self._signer_name,
            to_address=self.vault_address,
            data=vault.harvest.encode_input(),
            min_confirmations=2,
        )

    def alert_triggered(self, ctx):
        return f"Harvest triggered: {ctx.trigger.data['pending'] / 1e18:.4f}"

    def alert_confirmed(self, ctx):
        return f"Harvest confirmed: {ctx.tx.hash}"
```

## Docs

- `docs/quickstart.md`
- `docs/cli.md`
- `docs/job-lifecycle.md`
- `docs/alerts.md`
