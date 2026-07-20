import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlparse

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate
from app.infrastructure.db.repositories.ingestion_runs import IngestionRunRepository
from app.infrastructure.db.repositories.listings import ListingRepository
from app.infrastructure.ingestion.email_parser import parse_email_alert, source_from_sender
from app.infrastructure.ingestion.imap_client import ImapEmailClient
from app.settings import Settings

LISTING_COUNT_PATTERN = re.compile(r"\b(\d+)\s+nouvelle[s]?\s+annonce[s]?\b", re.IGNORECASE)


class RawEmailFetcher(Protocol):
    def fetch_raw_messages(self) -> Iterable[tuple[str, bytes]]: ...


@dataclass(frozen=True)
class EmailIngestionResult:
    items_seen: int
    items_created: int
    items_updated: int
    messages_ignored: int
    error_count: int


class EmailIngestionService:
    def __init__(
        self,
        session: Session,
        *,
        fetcher: RawEmailFetcher | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or Settings()
        self._fetcher = fetcher or ImapEmailClient(self._settings)
        self._listings = ListingRepository(session)
        self._runs = IngestionRunRepository(session)

    def import_alerts(self) -> EmailIngestionResult:
        started = datetime.now(UTC)
        run = self._runs.start("email")
        items_seen = 0
        items_created = 0
        items_updated = 0
        messages_ignored = 0
        errors: list[dict[str, Any]] = []

        for uid, raw_message in self._fetcher.fetch_raw_messages():
            try:
                alert = parse_email_alert(uid, raw_message)
                if not self._sender_is_allowed(alert.sender):
                    messages_ignored += 1
                    continue
                observed_at = alert.sent_at or started
                source_urls = alert.listing_urls or alert.urls
                listing_urls = self._listing_urls(alert.subject, source_urls)
                if not listing_urls:
                    messages_ignored += 1
                    continue
                for url in listing_urls:
                    items_seen += 1
                    listing = ListingCreate(
                        source=source_from_sender(alert.sender),
                        external_id=None,
                        source_url=url,
                        title=alert.subject,
                        raw_location=None,
                        description=alert.body_text[:4000] or None,
                        current_price_cents=None,
                        published_at=None,
                        first_seen_at=observed_at,
                        last_seen_at=observed_at,
                        raw_payload={
                            "email_uid": alert.uid,
                            "email_message_id": alert.message_id,
                            "email_sender": alert.sender,
                        },
                    )
                    existing = self._listings.get_by_source_url(str(listing.source_url))
                    if existing is not None:
                        self._listings.touch_seen(existing, observed_at)
                        items_updated += 1
                        continue
                    self._listings.add(listing)
                    items_created += 1
            except (ValueError, ValidationError, UnicodeError) as exc:
                errors.append({"uid": uid, "error": str(exc)})

        self._runs.finish(
            run,
            status="failed" if errors else "success",
            finished_at=datetime.now(UTC),
            items_seen=items_seen,
            items_created=items_created,
            items_updated=items_updated,
            error_details=errors,
        )
        self._session.commit()
        return EmailIngestionResult(
            items_seen=items_seen,
            items_created=items_created,
            items_updated=items_updated,
            messages_ignored=messages_ignored,
            error_count=len(errors),
        )

    def _sender_is_allowed(self, sender: str) -> bool:
        allowed_domains = _csv_values(self._settings.email_allowed_sender_domains)
        if not allowed_domains:
            return True
        sender_domain = source_from_sender(sender)
        return _domain_matches(sender_domain, allowed_domains)

    def _url_is_allowed(self, url: str) -> bool:
        allowed_domains = _csv_values(self._settings.email_allowed_url_domains)
        if not allowed_domains:
            return True
        parsed_host = (urlparse(url).hostname or "").lower()
        return _domain_matches(parsed_host, allowed_domains)

    def _listing_urls(self, subject: str, urls: tuple[str, ...]) -> tuple[str, ...]:
        allowed_urls = tuple(url for url in urls if self._url_is_allowed(url))
        if not allowed_urls:
            return ()

        expected_count = _expected_listing_count(subject)
        max_count = expected_count or self._settings.email_max_listings_per_message
        max_count = max(1, min(max_count, self._settings.email_max_listings_per_message))

        return allowed_urls[:max_count]


def _csv_values(value: str) -> tuple[str, ...]:
    return tuple(item.strip().lower() for item in value.split(",") if item.strip())


def _domain_matches(host: str, allowed_domains: tuple[str, ...]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains)


def _expected_listing_count(subject: str) -> int | None:
    match = LISTING_COUNT_PATTERN.search(subject)
    if match is None:
        return None
    return int(match.group(1))
