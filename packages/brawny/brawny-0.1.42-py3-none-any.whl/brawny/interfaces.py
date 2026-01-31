"""Project interface support (Brownie-style JSON ABI interfaces)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brawny.logging import get_logger, log_unexpected

logger = get_logger(__name__)


def _load_json_abi(path: Path) -> list[dict[str, Any]]:
    """Load ABI list from a JSON file.

    Accepts either a raw ABI list or an artifact with an "abi" field.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("abi"), list):
        return data["abi"]
    raise ValueError("Interface JSON must be ABI list or object with 'abi' list")


@dataclass(frozen=True)
class InterfaceConstructor:
    """Constructor used to create Contract handles from a JSON ABI."""

    name: str
    abi: list[dict[str, Any]]
    selectors: dict[bytes, str] = field(init=False)

    def __post_init__(self) -> None:
        from eth_utils import function_signature_to_4byte_selector
        from brawny.alerts.abi_resolver import get_function_signature

        selectors: dict[bytes, str] = {}
        for item in self.abi:
            if item.get("type") != "function":
                continue
            signature = get_function_signature(item["name"], item.get("inputs", []))
            selectors[function_signature_to_4byte_selector(signature)] = item["name"]
        object.__setattr__(self, "selectors", selectors)

    def __call__(self, address: str):
        from brawny.api import Contract

        return Contract(address, abi=self.abi)

    def __repr__(self) -> str:
        return f"<InterfaceConstructor '{self.name}'>"

    def decode_input(self, calldata: str | bytes) -> tuple[str, list[Any]]:
        """Decode calldata for this interface.

        Returns:
            (function_signature, decoded_args)
        """
        from eth_abi import decode as abi_decode
        from eth_utils import function_signature_to_4byte_selector
        from hexbytes import HexBytes
        from brawny.alerts.abi_resolver import get_function_signature

        data = HexBytes(calldata)
        fn_selector = data[:4]

        abi = next(
            (
                item
                for item in self.abi
                if item.get("type") == "function"
                and function_signature_to_4byte_selector(
                    get_function_signature(item["name"], item.get("inputs", []))
                )
                == fn_selector
            ),
            None,
        )
        if abi is None:
            raise ValueError("Four byte selector does not match the ABI for this contract")

        function_sig = get_function_signature(abi["name"], abi.get("inputs", []))
        types_list = [inp["type"] for inp in abi.get("inputs", [])]
        decoded = list(abi_decode(types_list, data[4:])) if types_list else []
        return function_sig, decoded


class InterfaceContainer:
    """Container providing access to interfaces within ./interfaces."""

    def __init__(self, interfaces_dir: Path | None = None) -> None:
        self._interfaces_dir = interfaces_dir or (Path.cwd() / "interfaces")
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._interfaces_dir.is_dir():
            return

        for path in sorted(self._interfaces_dir.rglob("*.json")):
            name = path.stem
            try:
                abi = _load_json_abi(path)
            except Exception as exc:
                # RECOVERABLE invalid interface files are skipped.
                log_unexpected(
                    logger,
                    "interface.load_failed",
                    name=name,
                    path=str(path),
                    error=str(exc),
                )
                continue
            self._add(name, abi)

    def _add(self, name: str, abi: list[dict[str, Any]]) -> None:
        constructor = InterfaceConstructor(name, abi)
        setattr(self, name, constructor)

    def __getattr__(self, name: str):
        self._load()
        try:
            return self.__dict__[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __dir__(self) -> list[str]:
        self._load()
        return sorted(set(self.__dict__.keys()))


# Singleton instance (Brownie-style)
interface = InterfaceContainer()
