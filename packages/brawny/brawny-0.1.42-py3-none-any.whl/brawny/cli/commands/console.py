"""Interactive console for contract exploration (brownie-style).

Mirrors brownie console ergonomics:
- Contract("0x...") - Get contract handle
- chain.height - Current block number
- chain[-1] - Most recent block
- Wei("1 ether") - Unit conversion

Uses prompt_toolkit for dropdown completion and syntax highlighting.
"""

from __future__ import annotations

import atexit
import code
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers.python import PythonLexer
from pygments.styles import get_style_by_name

# ANSI color codes (Brownie-style)
_BASE = "\x1b[0;"
_COLORS = {
    "red": "31", "green": "32", "yellow": "33", "blue": "34",
    "magenta": "35", "cyan": "36", "white": "37",
}
_RESET = f"{_BASE}m"


def _color(color_str: str) -> str:
    """Return ANSI escape code for color."""
    if not color_str:
        return _RESET
    parts = color_str.split()
    if len(parts) == 2 and parts[0] == "bright":
        return f"{_BASE}1;{_COLORS.get(parts[1], '37')}m"
    elif len(parts) == 2 and parts[0] == "dark":
        return f"{_BASE}2;{_COLORS.get(parts[1], '37')}m"
    return f"{_BASE}{_COLORS.get(color_str, '37')}m"


def _format_tb(exc: Exception, start: int | None = None) -> str:
    """Format exception with colorized traceback (Brownie-style).

    Args:
        exc: The exception to format
        start: Starting frame index (skip internal frames)
    """
    if isinstance(exc, SyntaxError) and exc.text is not None:
        return _format_syntaxerror(exc)

    base_path = str(Path(".").absolute())
    tb_lines = traceback.format_tb(exc.__traceback__)
    tb_lines = [line.replace("./", "") for line in tb_lines]

    # Skip internal frames if start is specified
    if start is not None:
        tb_lines = tb_lines[start:]

    formatted = []
    for line in tb_lines:
        parts = line.split("\n")
        if len(parts) >= 1:
            info = parts[0].replace(base_path, ".")
            code_line = parts[1].strip() if len(parts) > 1 else ""

            # Parse: '  File "path", line N, in func'
            info = info.strip()
            if info.startswith("File"):
                # Extract components
                try:
                    # File "path", line N, in func
                    file_part = info.split('"')[1] if '"' in info else "?"
                    line_match = re.search(r'line (\d+)', info)
                    line_num = line_match.group(1) if line_match else "?"
                    func_match = re.search(r'in (\w+)', info)
                    func_name = func_match.group(1) if func_match else "?"

                    # Shorten site-packages paths
                    if "site-packages/" in file_part:
                        file_part = file_part.split("site-packages/")[1]

                    formatted_line = (
                        f"  {_color('dark white')}File {_color('bright magenta')}\"{file_part}\""
                        f"{_color('dark white')}, line {_color('bright blue')}{line_num}"
                        f"{_color('dark white')}, in {_color('bright cyan')}{func_name}{_RESET}"
                    )
                    if code_line:
                        formatted_line += f"\n    {code_line}"
                    formatted.append(formatted_line)
                except (IndexError, ValueError, TypeError):
                    formatted.append(line.rstrip())
            else:
                formatted.append(line.rstrip())

    # Add exception line
    exc_name = type(exc).__name__
    exc_msg = str(exc)
    formatted.append(f"{_color('bright red')}{exc_name}{_RESET}: {exc_msg}")

    return "\n".join(formatted)


def _format_syntaxerror(exc: SyntaxError) -> str:
    """Format SyntaxError with colorized output."""
    base_path = str(Path(".").absolute())
    filename = (exc.filename or "<console>").replace(base_path, ".")
    lineno = exc.lineno or 1
    text = exc.text or ""
    offset = exc.offset or 0

    # Calculate caret position
    if text:
        stripped = text.lstrip()
        offset = offset + len(stripped) - len(text) + 3

    result = (
        f"  {_color('dark white')}File {_color('bright magenta')}\"{filename}\""
        f"{_color('dark white')}, line {_color('bright blue')}{lineno}{_RESET}\n"
    )
    if text:
        result += f"    {text.strip()}\n"
        result += f"{' ' * offset}^\n"
    result += f"{_color('bright red')}SyntaxError{_RESET}: {exc.msg}"
    return result


def _assert_console_allowed(config) -> None:
    """Enforce console safety gates."""
    if os.environ.get("BRAWNY_ALLOW_CONSOLE") != "1":
        raise click.ClickException("BRAWNY_ALLOW_CONSOLE=1 is required")
    if not config.debug.allow_console:
        raise click.ClickException("debug.allow_console must be true")
    if not sys.stdin.isatty():
        raise click.ClickException("Console requires an interactive TTY")


def _resolve_completion_base(locals_dict: dict, base: str) -> Any:
    """Resolve completion base without executing descriptors/properties."""
    import inspect

    parts = base.split(".")
    if not parts or not re.match(r"^[A-Za-z_]\\w*$", parts[0]):
        raise ValueError("invalid base")
    obj = locals_dict[parts[0]]
    if len(parts) == 1:
        return obj
    if len(parts) > 2:
        raise ValueError("unsafe depth")
    attr = parts[1]
    if not re.match(r"^[A-Za-z_]\\w*$", attr):
        raise ValueError("invalid attr")
    candidate = inspect.getattr_static(obj, attr)
    if hasattr(candidate, "__get__"):
        raise ValueError("unsafe attr")
    return candidate


class ConsoleCompleter(Completer):
    """Dropdown tab-completion for the console (mirrors Brownie)."""

    def __init__(self, console: "BrawnyConsole"):
        self.console = console

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        try:
            # Find the expression being completed (handles foo.bar, func(arg.attr, etc.)
            match = re.search(r"([a-zA-Z_][\w\.]*)?$", text)
            if not match:
                return

            expr = match.group(1) or ""

            if "." in expr:
                # Attribute completion
                base, partial = expr.rsplit(".", 1)

                try:
                    obj = _resolve_completion_base(self.console.locals, base)
                except (KeyError, AttributeError, ValueError, TypeError):
                    return

                for attr in dir(obj):
                    if attr.startswith(partial):
                        # Skip private unless explicitly typing _
                        if attr.startswith("_") and not partial.startswith("_"):
                            continue

                        suffix = ""
                        try:
                            import inspect

                            val = inspect.getattr_static(obj, attr)
                            if callable(val) and not isinstance(val, property):
                                suffix = "("
                        except (AttributeError, ValueError, TypeError):
                            suffix = ""

                        yield Completion(attr + suffix, start_position=-len(partial))
            else:
                # Namespace completion
                for name in self.console.locals:
                    if name.startswith(expr):
                        if name.startswith("_") and not expr.startswith("_"):
                            continue
                        yield Completion(name, start_position=-len(expr))
        except (AttributeError, KeyError, ValueError, TypeError):
            pass  # Fail silently - no completions


class BrawnyConsole(code.InteractiveConsole):
    """Brownie-style interactive console with colorized tracebacks."""

    def __init__(self, locals_dict: dict, history_file: str):
        super().__init__(locals_dict)

        # Setup prompt_toolkit session
        style = style_from_pygments_cls(get_style_by_name("monokai"))
        self._formatter = Terminal256Formatter(style="monokai")

        self.prompt_session = PromptSession(
            completer=ConsoleCompleter(self),
            lexer=PygmentsLexer(PythonLexer),
            history=FileHistory(history_file),
            enable_history_search=True,
            style=style,
        )

    def raw_input(self, prompt: str = "") -> str:
        """Use prompt_toolkit for input with completion."""
        return self.prompt_session.prompt(prompt)

    def showsyntaxerror(self, filename: str | None = None) -> None:
        """Display syntax error with colorized output."""
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            tb = _format_tb(exc_info[1])
            self.write(tb + "\n")
        else:
            super().showsyntaxerror(filename)

    def showtraceback(self) -> None:
        """Display traceback with colorized output (skip internal frames)."""
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            tb = _format_tb(exc_info[1], start=1)
            self.write(tb + "\n")
        else:
            super().showtraceback()

    def runsource(self, source: str, filename: str = "<input>", symbol: str = "single") -> bool:
        """Execute source with expression result highlighting."""
        try:
            code_obj = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            self.showsyntaxerror(filename)
            return False

        if code_obj is None:
            # Incomplete input - need more lines
            return True

        # Try to capture return value for expression highlighting
        try:
            self.compile(source, filename, "eval")
            # It's an expression - wrap it to capture result
            wrapped_code = self.compile(f"__ret_value__ = {source}", filename, "exec")
            self.runcode(wrapped_code)
            if "__ret_value__" in self.locals and self.locals["__ret_value__"] is not None:
                result = self.locals.pop("__ret_value__")
                result_str = repr(result)
                highlighted = highlight(result_str, PythonLexer(), self._formatter)
                self.write(highlighted)
            return False
        except (SyntaxError, ValueError, TypeError):
            pass

        # Not an expression - run as statement
        self.runcode(code_obj)
        return False


@click.command("console", hidden=True)
@click.option("--config", "config_path", default="./config.yaml", help="Path to config.yaml")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def console(config_path: str, debug: bool) -> None:
    """Interactive Python console with contract helpers.

    Brownie-style interface for contract exploration.

    Examples:

        brawny console

        brawny console --debug
    """
    import logging
    import structlog

    if not os.path.exists(config_path):
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    from brawny.config import Config

    config = Config.from_yaml(config_path)
    config, _ = config.apply_env_overrides()

    _assert_console_allowed(config)

    # Suppress all logs during startup for clean console UX
    # Must configure both stdlib logging AND structlog to silence output
    if not debug:
        # Set root logger to CRITICAL to filter everything
        logging.basicConfig(level=logging.CRITICAL, force=True)
        # Configure structlog with filter_by_level so it respects logging levels
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,  # This respects logging.CRITICAL
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=False,  # Allow reconfiguration later
        )
    else:
        from brawny.logging import setup_logging, LogFormat
        setup_logging(log_level="DEBUG", log_format=LogFormat.TEXT)

    from brawny.logging import get_logger

    import socket

    allow_env = os.environ.get("BRAWNY_ALLOW_CONSOLE") == "1"
    logger = get_logger(__name__)
    logger.warning(
        "console.opened",
        user=os.environ.get("USER", "unknown"),
        hostname=socket.gethostname(),
        allow_env=allow_env,
        config_allow=config.debug.allow_console,
        tty=sys.stdin.isatty(),
    )

    from brawny.alerts.contracts import ContractSystem
    from brawny._rpc.clients import BroadcastClient
    from brawny.config.routing import resolve_default_read_group

    rpc_group = resolve_default_read_group(config)
    rpc_endpoints = config.rpc_groups[rpc_group].endpoints
    chain_id = config.chain_id

    if not rpc_endpoints:
        click.echo("No RPC endpoints configured", err=True)
        sys.exit(1)

    # Create broadcast client with selected endpoints
    from brawny._rpc.retry_policy import broadcast_policy

    rpc = BroadcastClient(
        endpoints=rpc_endpoints,
        timeout_seconds=config.rpc_timeout_seconds,
        max_retries=config.rpc_max_retries,
        retry_backoff_base=config.rpc_retry_backoff_base,
        retry_policy=broadcast_policy(config),
    )

    # ContractSystem uses global ABI cache at ~/.brawny/abi_cache.db
    contract_system = ContractSystem(rpc, config)
    block_number = rpc.get_block_number()

    # Set console context so Contract()/interface/web3 work in REPL
    from brawny._context import ActiveContext, set_console_context
    set_console_context(ActiveContext(
        rpc=rpc,
        contract_system=contract_system,
        chain_id=chain_id,
        network_name=None,
        rpc_group=rpc_group,
    ))

    # Initialize global singletons for Brownie-style access
    from brawny.accounts import _init_accounts, accounts
    from brawny.history import _init_history, history
    from brawny.chain import _init_chain, chain

    _init_accounts()  # Lazy - keystores loaded via accounts.load()
    _init_history()
    _init_chain(rpc, chain_id)

    # Brownie-style Contract function (capitalized to match brownie convention)
    def Contract(address: str, abi: list | None = None):
        """Get a contract handle for the given address.

        Mirrors brownie's Contract() interface.

        Args:
            address: Contract address (0x...)
            abi: Optional ABI override (if None, fetched from Etherscan)

        Returns:
            ContractHandle with brownie-style interface

        Example:
            >>> keeper = Contract("0x1234...")
            >>> keeper.canWork()  # uses latest block
            True
            >>> keeper.canWork(block_identifier=21000000)  # historical
            False
            >>> keeper.work.encode_input()
            '0x322e78f1'
        """
        # No block_identifier = uses "latest" (current block at call time)
        return contract_system.handle(address=address, abi=abi)

    # Brownie-style constants
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  # Common placeholder

    # Import Wei from api (DRY - shared implementation)
    from brawny.api import Wei
    from brawny.multicall import multicall

    # Build REPL namespace (mirrors brownie's __all__ exports)
    from brawny.interfaces import interface
    namespace = {
        # Core (brownie-style names)
        "Contract": Contract,
        "chain": chain,
        "accounts": accounts,
        "history": history,
        "Wei": Wei,
        "multicall": multicall,
        "web3": rpc.web3,  # Direct Web3 instance (not proxy - console has direct rpc)
        "interface": interface,
        # Constants
        "ZERO_ADDRESS": ZERO_ADDRESS,
        "ETH_ADDRESS": ETH_ADDRESS,
        # brawny specific
        "rpc": rpc,
    }

    # Clean banner
    rpc_display = rpc_endpoints[0].split("@")[-1] if "@" in rpc_endpoints[0] else rpc_endpoints[0]
    rpc_display = rpc_display.replace("https://", "").replace("http://", "")

    click.echo()
    click.echo(f"  · chain   {click.style(str(chain_id), fg='cyan')}")
    click.echo(f"  · block   {click.style(str(block_number), fg='cyan')}")
    click.echo(f"  · rpc     {click.style(rpc_display, dim=True)}")
    click.echo()

    # Re-enable logging for REPL (errors should be visible)
    if not debug:
        logging.disable(logging.NOTSET)

    # Run Brownie-style REPL with colorized tracebacks
    history_file = os.path.expanduser("~/.brawny_history")
    namespace.setdefault("__builtins__", __builtins__)

    shell = BrawnyConsole(namespace, history_file)
    shell.interact(banner="", exitmsg="")


def _start_anvil_fork(rpc_url: str, chain_id: int, port: int = 8545, block: int | None = None) -> str:
    """Start Anvil forking from given RPC.

    Args:
        rpc_url: RPC endpoint to fork from
        chain_id: Chain ID for the fork
        port: Local port for Anvil (default 8545)
        block: Optional block number to fork at

    Returns:
        Local RPC URL (http://127.0.0.1:port)
    """
    import socket

    # Check if port is available (avoid cryptic errors)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            click.echo(f"Port {port} already in use. Use --port to specify another.", err=True)
            sys.exit(1)

    cmd = [
        "anvil",
        "--fork-url", rpc_url,
        "--port", str(port),
        "--chain-id", str(chain_id),
        "--silent",  # Suppress Anvil's own output
    ]
    if block is not None:
        cmd.extend(["--fork-block-number", str(block)])

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        click.echo("Anvil not found. Install foundry: https://getfoundry.sh", err=True)
        sys.exit(1)

    # Register cleanup
    atexit.register(proc.terminate)

    # Poll until Anvil is ready (more reliable than sleep)
    local_url = f"http://127.0.0.1:{port}"
    import httpx
    for _ in range(20):  # 10 second timeout
        if proc.poll() is not None:
            click.echo("Anvil failed to start", err=True)
            sys.exit(1)
        try:
            resp = httpx.post(
                local_url,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                timeout=0.5,
            )
            if resp.status_code == 200:
                break
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    else:
        click.echo("Anvil failed to start (timeout)", err=True)
        proc.terminate()
        sys.exit(1)

    return local_url


def register(main) -> None:
    """Register console command with main CLI."""
    main.add_command(console)
