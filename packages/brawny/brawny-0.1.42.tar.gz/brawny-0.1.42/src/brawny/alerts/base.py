"""Alert formatting helpers.

Provides utilities for formatting alert messages with explorer links
and proper escaping for Telegram MarkdownV2.
"""

from __future__ import annotations


# Explorer URLs for different chains
EXPLORER_URLS = {
    1: "https://etherscan.io",
    5: "https://goerli.etherscan.io",
    11155111: "https://sepolia.etherscan.io",
    17000: "https://holesky.etherscan.io",
    137: "https://polygonscan.com",
    80001: "https://mumbai.polygonscan.com",
    80002: "https://amoy.polygonscan.com",
    42161: "https://arbiscan.io",
    421613: "https://goerli.arbiscan.io",
    421614: "https://sepolia.arbiscan.io",
    10: "https://optimistic.etherscan.io",
    420: "https://goerli-optimism.etherscan.io",
    11155420: "https://sepolia-optimism.etherscan.io",
    8453: "https://basescan.org",
    84531: "https://goerli.basescan.org",
    84532: "https://sepolia.basescan.org",
    43114: "https://snowtrace.io",
    56: "https://bscscan.com",
    250: "https://ftmscan.com",
    100: "https://gnosisscan.io",
    324: "https://era.zksync.network",
    534352: "https://scrollscan.com",
    59144: "https://lineascan.build",
    81457: "https://blastscan.io",
}


def get_explorer_url(chain_id: int) -> str:
    """Get block explorer URL for chain.

    Args:
        chain_id: Chain ID

    Returns:
        Explorer base URL
    """
    return EXPLORER_URLS.get(chain_id, "https://etherscan.io")


def format_tx_link(tx_hash: str, chain_id: int = 1) -> str:
    """Format transaction link for explorer.

    Args:
        tx_hash: Transaction hash
        chain_id: Chain ID

    Returns:
        Markdown formatted link
    """
    explorer = get_explorer_url(chain_id)
    return f"[View Transaction]({explorer}/tx/{tx_hash})"


def format_address_link(address: str, chain_id: int = 1) -> str:
    """Format address link for explorer.

    Args:
        address: Ethereum address
        chain_id: Chain ID

    Returns:
        Markdown formatted link
    """
    explorer = get_explorer_url(chain_id)
    return f"[{address[:10]}...]({explorer}/address/{address})"


# MarkdownV2 special characters that need escaping
_MARKDOWN_V2_SPECIAL = r"_*[]()~`>#+=|{}.!-"


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for MarkdownV2
    """
    result = []
    for char in text:
        if char in _MARKDOWN_V2_SPECIAL:
            result.append("\\")
        result.append(char)
    return "".join(result)


def shorten(hex_string: str, prefix: int = 6, suffix: int = 4) -> str:
    """Shorten a hex string (address or hash) for display.

    Args:
        hex_string: Full hex string (e.g., 0x1234...abcd)
        prefix: Characters to keep at start (including 0x)
        suffix: Characters to keep at end

    Returns:
        Shortened string like "0x1234...abcd"

    Example:
        >>> shorten("0x1234567890abcdef1234567890abcdef12345678")
        "0x1234...5678"
    """
    if not hex_string or len(hex_string) <= prefix + suffix + 3:
        return hex_string
    return f"{hex_string[:prefix]}...{hex_string[-suffix:]}"


def explorer_link(
    hash_or_address: str,
    chain_id: int = 1,
    label: str | None = None,
) -> str:
    """Create a Markdown explorer link with emoji.

    Automatically detects if input is a tx hash or address.

    Args:
        hash_or_address: Transaction hash or address
        chain_id: Chain ID for explorer URL
        label: Custom label (default: "🔗 View on Explorer")

    Returns:
        Markdown formatted link like "[🔗 View on Explorer](url)"

    Example:
        >>> explorer_link("0xabc123...")
        "[🔗 View on Explorer](https://etherscan.io/tx/0xabc123...)"
    """
    explorer = get_explorer_url(chain_id)

    # Detect type: tx hash is 66 chars, address is 42 chars
    if len(hash_or_address) == 66:
        path = f"tx/{hash_or_address}"
    else:
        path = f"address/{hash_or_address}"

    url = f"{explorer}/{path}"
    display = label or "🔗 View on Explorer"

    return f"[{display}]({url})"
