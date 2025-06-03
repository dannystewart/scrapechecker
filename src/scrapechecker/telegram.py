"""Send Telegram messages."""

from __future__ import annotations

import requests
from polykit.log import PolyLog


class TelegramSender:
    """Send messages to one or more Telegram users. You must supply an API token and chat ID(s)."""

    def __init__(self, token: str, chat_ids: str | list[str]):
        self.logger = PolyLog.get_logger()
        self.token: str = token

        # Handle both single chat ID and comma-separated list
        if isinstance(chat_ids, str):
            # Split by comma and strip whitespace
            self.chat_ids: list[str] = [chat_id.strip() for chat_id in chat_ids.split(",")]
        else:
            self.chat_ids = chat_ids

        self.url: str = f"https://api.telegram.org/bot{self.token}"
        self.logger.debug("Initialized TelegramSender for %d chat(s)", len(self.chat_ids))

    def call_api(self, api_method: str, payload: dict[str, str] | None = None) -> dict[str, str]:
        """Make a POST request to the Telegram API using the specified method and payload.

        Args:
            api_method: The API method to call.
            payload: The payload to send to the API. Defaults to None.

        Returns:
            The response data in JSON if the request is successful.

        Raises:
            Exception: If the request to the Telegram API fails.
        """
        url = f"{self.url}/{api_method}"
        payload = dict(payload.items()) if payload else {}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response_data = response.json()
            if not response_data.get("ok"):
                error_msg = response_data.get("description", "Unknown error.")
                self.logger.error("Failed to call %s: %s", api_method, error_msg)
                self.logger.debug("Code %s: %s", response.status_code, response_data)
                msg = f"Failed to call {api_method}: {error_msg}"
                raise Exception(msg)
            return response_data
        except requests.RequestException as e:
            self.logger.warning("Request to Telegram API failed: %s", str(e))
            msg = f"Request to Telegram API failed: {e}"
            raise Exception(msg) from e

    def send_message(self, message: str, parse_mode: str = "HTML", log: bool = False) -> bool:
        """Send a message to all configured Telegram users.

        Args:
            message: The message to send.
            parse_mode: The parse mode to use for message formatting. Supports "Markdown",
                        "MarkdownV2", or "HTML". Defaults to "HTML".
            log: Whether to log a successful send. Defaults to False.

        Returns:
            True if the message was sent successfully to all recipients, False if any failed.
        """
        success_count = 0
        total_count = len(self.chat_ids)

        for chat_id in self.chat_ids:
            payload = {"chat_id": chat_id, "text": message}

            if parse_mode:
                payload["parse_mode"] = parse_mode

            try:
                self.call_api("sendMessage", payload)
                success_count += 1
                if log:
                    self.logger.debug("Message sent successfully to chat ID: %s", chat_id)
            except requests.exceptions.RequestException as e:
                self.logger.error("Failed to send message to chat ID %s: %s", chat_id, str(e))

        if log and success_count > 0:
            self.logger.info(
                "Telegram message sent to %d/%d recipients.", success_count, total_count
            )

        return success_count == total_count
