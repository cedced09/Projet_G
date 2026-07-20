import imaplib
from typing import Any

import pytest

from app.infrastructure.ingestion.imap_client import EmailAuthenticationError, ImapEmailClient
from app.settings import Settings


class FailingImapClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def __enter__(self) -> FailingImapClient:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def login(self, username: str, password: str) -> None:
        raise imaplib.IMAP4.error(b"[AUTHENTICATIONFAILED] Invalid credentials")


def test_imap_authentication_error_is_readable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(imaplib, "IMAP4_SSL", FailingImapClient)
    client = ImapEmailClient(
        Settings(
            email_imap_host="imap.example.invalid",
            email_imap_username="alerts@example.invalid",
            email_imap_password="bad-password",
        )
    )

    with pytest.raises(EmailAuthenticationError):
        list(client.fetch_raw_messages())
