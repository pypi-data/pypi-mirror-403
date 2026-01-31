"""Telegram Bot API wrapper with strict parameter naming.

All method signatures use Telegram Bot API parameter names verbatim.
No aliases. No renaming.

See: https://core.telegram.org/bots/api

Usage in jobs:

    from brawny.telegram import telegram

    class MyJob(Job):
        def check(self, ctx):
            # Send a simple message
            telegram.send_message("Something happened!", chat_id="-100...")

            # Send with markdown
            telegram.send_message("*Bold*", chat_id="-100...", parse_mode="Markdown")

            # Disable link preview
            telegram.send_message("Check https://example.com", chat_id="-100...",
                                  disable_web_page_preview=False)

            # Silent notification
            telegram.send_message("Low priority", chat_id="-100...",
                                  disable_notification=True)

Configuration:
    Set in config.yaml:
        telegram:
          bot_token: "${TELEGRAM_BOT_TOKEN}"
          chats:
            ops: "-1001234567890"
            dev: "-1009876543210"
          default: ["ops"]
"""

from __future__ import annotations

import os  # Used by _LazyTelegram for TELEGRAM_BOT_TOKEN
from typing import Any

import httpx

from brawny.logging import get_logger
from brawny.network_guard import allow_network_calls

logger = get_logger(__name__)

# Module-level HTTP client for connection pooling
_http_client: httpx.Client | None = httpx.Client(timeout=30.0)


def close_http_client() -> None:
    """Close HTTP client on shutdown. Idempotent + safe in partial init."""
    global _http_client
    client, _http_client = _http_client, None
    if client is not None:
        client.close()


def _client() -> httpx.Client:
    """Get HTTP client, fail fast if closed."""
    if _http_client is None:
        raise RuntimeError("HTTP client is closed")
    return _http_client

# Telegram API limits
MAX_MESSAGE_LENGTH = 4096
TRUNCATION_SUFFIX = "\n...[truncated]"


def _truncate_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """Truncate message to fit Telegram's limit."""
    if len(text) <= max_length:
        return text
    suffix_len = len(TRUNCATION_SUFFIX)
    if max_length <= suffix_len:
        return text[:max_length]
    return text[: max_length - suffix_len] + TRUNCATION_SUFFIX


class TelegramBot:
    """Telegram Bot API wrapper.

    All methods use Telegram API parameter names verbatim.
    No aliases or renaming.

    See: https://core.telegram.org/bots/api
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: int = 30,
        default_parse_mode: str | None = "Markdown",
    ) -> None:
        """Initialize Telegram bot.

        Args:
            token: Bot token. Required for API calls.
            timeout: Request timeout in seconds.
            default_parse_mode: Default parse mode when not explicitly provided.
        """
        self._token = token
        self._timeout = timeout
        self._default_parse_mode = default_parse_mode

    @property
    def configured(self) -> bool:
        """Check if bot is configured with token."""
        return bool(self._token)

    @property
    def api_url(self) -> str:
        """Base URL for Telegram API."""
        return f"https://api.telegram.org/bot{self._token}"

    def _request(self, method: str, **params: Any) -> dict | bool | None:
        """Make a request to the Telegram API.

        Args:
            method: API method name (e.g., "sendMessage")
            **params: Method parameters

        Returns:
            API response (dict or bool depending on endpoint), or None on failure
        """
        if not self._token:
            # Silent no-op: startup already warned about missing bot_token
            return None

        # Extract chat_id for error logging before filtering
        chat_id = params.get("chat_id")

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            with allow_network_calls(reason="alerts"):
                response = _client().post(
                    f"{self.api_url}/{method}",
                    json=params,
                )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                logger.error(
                    "telegram.api_error",
                    method=method,
                    error=result.get("description"),
                    chat_id=chat_id,
                )
                return None

            return result.get("result")

        except httpx.TimeoutException:
            # Don't log full URL (contains bot token)
            logger.error(
                "telegram.timeout",
                method=method,
                chat_id=chat_id,
            )
            return None
        except httpx.HTTPStatusError as e:
            logger.error(
                "telegram.http_error",
                method=method,
                chat_id=chat_id,
                status=e.response.status_code,
            )
            return None
        except httpx.RequestError as e:
            logger.error(
                "telegram.request_failed",
                method=method,
                error=str(e)[:200],
                chat_id=chat_id,
            )
            return None

    def send_message(
        self,
        text: str,
        *,
        chat_id: str | int,
        parse_mode: str | None = None,
        disable_web_page_preview: bool | None = None,
        disable_notification: bool | None = None,
        message_thread_id: int | None = None,
        reply_to_message_id: int | None = None,
    ) -> dict | None:
        """Send a text message.

        https://core.telegram.org/bots/api#sendmessage

        Args:
            text: Message text (up to 4096 characters, auto-truncated)
            chat_id: Target chat ID (required)
            parse_mode: "Markdown", "MarkdownV2", "HTML", or None
            disable_web_page_preview: Disable link previews
            disable_notification: Send without notification sound
            message_thread_id: Thread ID for forum topics
            reply_to_message_id: Message ID to reply to

        Returns:
            Message object from Telegram API, or None on failure
        """
        if parse_mode is None:
            parse_mode = self._default_parse_mode
        return self._request(
            "sendMessage",
            chat_id=chat_id,
            text=_truncate_message(text),
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            message_thread_id=message_thread_id,
            reply_to_message_id=reply_to_message_id,
        )

    def send_photo(
        self,
        *,
        chat_id: str | int,
        photo: str,
        caption: str | None = None,
        parse_mode: str | None = None,
        disable_notification: bool | None = None,
    ) -> dict | None:
        """Send a photo.

        https://core.telegram.org/bots/api#sendphoto

        Args:
            chat_id: Target chat ID (required)
            photo: Photo URL or file_id
            caption: Optional caption
            parse_mode: Caption parse mode
            disable_notification: Send without notification sound

        Returns:
            Message object or None
        """
        if parse_mode is None:
            parse_mode = self._default_parse_mode
        return self._request(
            "sendPhoto",
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )

    def send_document(
        self,
        *,
        chat_id: str | int,
        document: str,
        caption: str | None = None,
        parse_mode: str | None = None,
        disable_notification: bool | None = None,
    ) -> dict | None:
        """Send a document.

        https://core.telegram.org/bots/api#senddocument

        Args:
            chat_id: Target chat ID (required)
            document: Document URL or file_id
            caption: Optional caption
            parse_mode: Caption parse mode
            disable_notification: Send without notification sound

        Returns:
            Message object or None
        """
        if parse_mode is None:
            parse_mode = self._default_parse_mode
        return self._request(
            "sendDocument",
            chat_id=chat_id,
            document=document,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )

    def edit_message_text(
        self,
        text: str,
        *,
        chat_id: str | int,
        message_id: int,
        parse_mode: str | None = None,
        disable_web_page_preview: bool | None = None,
    ) -> dict | None:
        """Edit a message's text.

        https://core.telegram.org/bots/api#editmessagetext

        Args:
            text: New message text
            chat_id: Chat containing the message
            message_id: ID of message to edit
            parse_mode: Text parse mode
            disable_web_page_preview: Disable link previews

        Returns:
            Edited message object or None
        """
        if parse_mode is None:
            parse_mode = self._default_parse_mode
        return self._request(
            "editMessageText",
            chat_id=chat_id,
            message_id=message_id,
            text=_truncate_message(text),
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )

    def delete_message(
        self,
        *,
        chat_id: str | int,
        message_id: int,
    ) -> bool:
        """Delete a message.

        https://core.telegram.org/bots/api#deletemessage

        Args:
            chat_id: Chat containing the message
            message_id: ID of message to delete

        Returns:
            True if deleted successfully
        """
        result = self._request(
            "deleteMessage",
            chat_id=chat_id,
            message_id=message_id,
        )
        return result is True

    def pin_chat_message(
        self,
        *,
        chat_id: str | int,
        message_id: int,
        disable_notification: bool | None = None,
    ) -> bool:
        """Pin a message in a chat.

        https://core.telegram.org/bots/api#pinchatmessage

        Args:
            chat_id: Chat containing the message
            message_id: ID of message to pin
            disable_notification: Pin without notification

        Returns:
            True if pinned successfully
        """
        result = self._request(
            "pinChatMessage",
            chat_id=chat_id,
            message_id=message_id,
            disable_notification=disable_notification,
        )
        return result is True

    def get_me(self) -> dict | None:
        """Get bot information.

        https://core.telegram.org/bots/api#getme

        Returns:
            Bot user object or None
        """
        return self._request("getMe")

    def get_chat(self, *, chat_id: str | int) -> dict | None:
        """Get chat information.

        https://core.telegram.org/bots/api#getchat

        Args:
            chat_id: Chat to get info for

        Returns:
            Chat object or None
        """
        return self._request("getChat", chat_id=chat_id)



class _LazyTelegram:
    """Lazy proxy for TelegramBot that initializes on first access.

    This defers TelegramBot creation until first use, ensuring environment
    variables from .env are loaded before reading TELEGRAM_BOT_TOKEN.
    """

    _instance: TelegramBot | None = None

    def _get_instance(self) -> TelegramBot:
        if self._instance is None:
            self._instance = TelegramBot(token=os.environ.get("TELEGRAM_BOT_TOKEN"))
        return self._instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)


# Global instance using environment variables
# Users can import and use directly: from brawny.telegram import telegram
telegram: TelegramBot = _LazyTelegram()  # type: ignore[assignment]


def get_telegram(token: str | None = None) -> TelegramBot:
    """Get a Telegram bot instance.

    Use this to create a bot with custom configuration.
    For the default instance, just import `telegram` directly.

    Args:
        token: Bot token (defaults to env var)

    Returns:
        TelegramBot instance
    """
    if token:
        return TelegramBot(token=token)
    return telegram._get_instance()  # type: ignore[union-attr]
