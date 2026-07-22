from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.application.email_ingestion_service import EmailIngestionService
from app.application.listing_service import ListingService
from app.settings import Settings


class FakeEmailFetcher:
    def __init__(self, messages: list[tuple[str, bytes]]) -> None:
        self._messages = messages

    def fetch_raw_messages(self) -> Iterable[tuple[str, bytes]]:
        return self._messages


def test_email_ingestion_creates_unlinked_listings_and_is_idempotent(session: Session) -> None:
    raw_message = (
        b"From: Alertes <alerts@example.invalid>\r\n"
        b"Subject: Nouveaux domaines\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <abc@example.invalid>\r\n"
        b'Content-Type: multipart/alternative; boundary="boundary"\r\n'
        b"\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://example.invalid/listing/1\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b'<a href="https://example.invalid/listing/1" name="adimage1_1">image</a>\r\n'
        b'<a href="https://example.invalid/listing/price1" '
        b'name="adprice1_1">1 000 000 \xe2\x82\xac</a>\r\n'
        b'<a href="https://example.invalid/listing/criteria1" '
        b'name="adcriteria1_1">5 pieces &middot; 140 m2</a>\r\n'
        b'<a href="https://example.invalid/listing/2" name="adimage2_1">image</a>\r\n'
        b'<a href="https://example.invalid/listing/price2" '
        b'name="adprice2_1">1 300 000 \xe2\x82\xac</a>\r\n'
        b'<a href="https://example.invalid/listing/criteria2" '
        b'name="adcriteria2_1">7 pieces &middot; 200 m2</a>\r\n'
        b"--boundary--\r\n"
    )
    fetcher = FakeEmailFetcher([("42", raw_message)])

    settings = Settings(email_allowed_url_domains="example.invalid")
    first_result = EmailIngestionService(
        session, fetcher=fetcher, settings=settings
    ).import_alerts()
    second_result = EmailIngestionService(
        session, fetcher=fetcher, settings=settings
    ).import_alerts()
    unlinked = ListingService(session).list_unlinked()

    assert first_result.items_seen == 2
    assert first_result.items_created == 2
    assert first_result.items_updated == 0
    assert first_result.messages_ignored == 0
    assert second_result.items_seen == 2
    assert second_result.items_created == 0
    assert second_result.items_updated == 2
    assert len(unlinked) == 2
    assert {item.public_id for item in unlinked} == {"ANN-0001", "ANN-0002"}
    assert {str(item.source_url) for item in unlinked} == {
        "https://example.invalid/listing/1",
        "https://example.invalid/listing/2",
    }


def test_email_ingestion_ignores_unallowed_url_domains(session: Session) -> None:
    raw_message = (
        b"From: Google <no-reply@accounts.google.com>\r\n"
        b"Subject: Alerte de securite\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <security@example.invalid>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://accounts.google.com/security\r\n"
    )
    fetcher = FakeEmailFetcher([("43", raw_message)])
    settings = Settings(email_allowed_url_domains="seloger.com")

    result = EmailIngestionService(session, fetcher=fetcher, settings=settings).import_alerts()

    assert result.items_seen == 0
    assert result.items_created == 0
    assert ListingService(session).list_unlinked() == []


def test_email_ingestion_uses_subject_count_to_limit_tracking_links(session: Session) -> None:
    raw_message = (
        b"From: Alertes <alertes@seloger.com>\r\n"
        b"Subject: 1 nouvelle annonce : Var\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <seloger@example.invalid>\r\n"
        b'Content-Type: multipart/alternative; boundary="boundary"\r\n'
        b"\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://click.by.seloger.com/?qs=first\r\n"
        b"https://click.by.seloger.com/?qs=second\r\n"
        b"https://click.by.seloger.com/?qs=third\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b'<a href="https://click.by.seloger.com/?qs=first" name="adimage1_1">image</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=criteria" '
        b'name="adcriteria1_1">5 pieces &middot; 140 m2</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=second" name="adimage2_1">image</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=promo" name="adtype2_1">Pub</a>\r\n'
        b"--boundary--\r\n"
    )
    fetcher = FakeEmailFetcher([("44", raw_message)])
    settings = Settings(email_allowed_url_domains="seloger.com", email_max_listings_per_message=5)

    result = EmailIngestionService(session, fetcher=fetcher, settings=settings).import_alerts()
    unlinked = ListingService(session).list_unlinked()

    assert result.items_seen == 1
    assert result.items_created == 1
    assert len(unlinked) == 1
    assert str(unlinked[0].source_url) == "https://click.by.seloger.com/?qs=first"


def test_email_ingestion_ignores_seloger_promo_without_listing_characteristics(
    session: Session,
) -> None:
    raw_message = (
        b"From: Alertes <alertes@seloger.com>\r\n"
        b"Subject: Les conseils SeLoger du moment\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <seloger-promo@example.invalid>\r\n"
        b'Content-Type: multipart/alternative; boundary="boundary"\r\n'
        b"\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://click.by.seloger.com/?qs=promo\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b'<a href="https://click.by.seloger.com/?qs=promo" name="adimage1_1">image</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=type" name="adtype1_1">Conseils achat</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=button" name="adbutton1_1">Lire</a>\r\n'
        b"--boundary--\r\n"
    )
    fetcher = FakeEmailFetcher([("46", raw_message)])
    settings = Settings(email_allowed_url_domains="seloger.com")

    result = EmailIngestionService(session, fetcher=fetcher, settings=settings).import_alerts()

    assert result.items_seen == 0
    assert result.items_created == 0
    assert result.messages_ignored == 1
    assert ListingService(session).list_unlinked() == []


def test_email_ingestion_prefers_structured_seloger_html_listing_url(session: Session) -> None:
    raw_message = (
        b"From: Alertes <alertes@seloger.com>\r\n"
        b"Subject: 1 nouvelle annonce : Var\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <seloger-structured@example.invalid>\r\n"
        b'Content-Type: multipart/alternative; boundary="boundary"\r\n'
        b"\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://click.by.seloger.com/?qs=wrong\r\n"
        b"--boundary\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b'<a href="https://click.by.seloger.com/?qs=good" name="adimage1_1">image</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=price" '
        b'name="adprice1_1">1 800 000 \xe2\x82\xac</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=type" name="adtype1_1">Villa test</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=criteria" '
        b'name="adcriteria1_1">7 pieces &middot; 300 m2 &middot; 5 489 m2</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=location" '
        b'name="adlocation1_1">Trans-en-Provence (83720)</a>\r\n'
        b'<a href="https://click.by.seloger.com/?qs=button" name="adbutton1_1">Voir</a>\r\n'
        b"--boundary--\r\n"
    )
    fetcher = FakeEmailFetcher([("45", raw_message)])
    settings = Settings(
        email_allowed_url_domains="seloger.com",
        email_max_listings_per_message=5,
    )

    result = EmailIngestionService(session, fetcher=fetcher, settings=settings).import_alerts()
    unlinked = ListingService(session).list_unlinked()

    assert result.items_seen == 1
    assert result.items_created == 1
    assert len(unlinked) == 1
    assert str(unlinked[0].source_url) == "https://click.by.seloger.com/?qs=good"
    assert unlinked[0].title == "Villa test"
    assert unlinked[0].current_price_cents == 180000000
    assert unlinked[0].room_count == 7
    assert unlinked[0].living_area_m2 == 300
    assert unlinked[0].land_area_m2 == 5489
    assert unlinked[0].municipality == "Trans-en-Provence"
