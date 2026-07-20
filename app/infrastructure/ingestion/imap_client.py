import imaplib
from collections.abc import Iterator

from app.settings import Settings


class EmailConfigurationError(ValueError):
    pass


class EmailAuthenticationError(ValueError):
    pass


class ImapEmailClient:
    def __init__(self, settings: Settings) -> None:
        host = settings.email_imap_host
        if not host:
            raise EmailConfigurationError("EMAIL_IMAP_HOST doit etre renseigne dans .env.")
        if not settings.email_imap_username:
            raise EmailConfigurationError("EMAIL_IMAP_USERNAME doit etre renseigne dans .env.")
        if not settings.email_imap_password:
            raise EmailConfigurationError("EMAIL_IMAP_PASSWORD doit etre renseigne dans .env.")
        self._settings = settings
        self._host = host

    def fetch_raw_messages(self) -> Iterator[tuple[str, bytes]]:
        with imaplib.IMAP4_SSL(
            self._host,
            self._settings.email_imap_port,
        ) as client:
            try:
                client.login(
                    self._settings.email_imap_username or "",
                    self._settings.email_imap_password or "",
                )
            except imaplib.IMAP4.error as exc:
                raise EmailAuthenticationError(
                    "Authentification IMAP refusée. Vérifie l'adresse email, "
                    "le serveur IMAP et le mot de passe d'application."
                ) from exc
            client.select(self._settings.email_imap_folder)
            status, data = client.search(None, self._settings.email_imap_search)
            if status != "OK" or not data:
                return

            message_numbers = data[0].split()[: self._settings.email_import_limit]
            for message_number in message_numbers:
                fetch_status, fetch_data = client.fetch(message_number, "(RFC822)")
                if fetch_status != "OK":
                    continue
                for item in fetch_data:
                    if isinstance(item, tuple) and isinstance(item[1], bytes):
                        yield (message_number.decode("ascii", errors="ignore"), item[1])
