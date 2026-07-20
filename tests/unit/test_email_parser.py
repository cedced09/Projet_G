from datetime import UTC, datetime

from app.infrastructure.ingestion.email_parser import (
    extract_listing_urls_from_html,
    extract_urls,
    parse_email_alert,
    source_from_sender,
)


def test_extract_urls_keeps_order_and_removes_duplicates() -> None:
    text = (
        "Voir https://example.invalid/listing/1 puis "
        "https://example.invalid/listing/2. Et encore https://example.invalid/listing/1"
    )

    assert extract_urls(text) == [
        "https://example.invalid/listing/1",
        "https://example.invalid/listing/2",
    ]


def test_parse_email_alert_extracts_metadata_and_urls() -> None:
    raw_message = (
        b"From: Alertes <alerts@example.invalid>\r\n"
        b"Subject: Nouveaux domaines\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <abc@example.invalid>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"https://example.invalid/listing/1\r\n"
    )

    alert = parse_email_alert("42", raw_message)

    assert alert.sender == "alerts@example.invalid"
    assert alert.subject == "Nouveaux domaines"
    assert alert.sent_at == datetime(2026, 7, 20, 8, 0, tzinfo=UTC)
    assert alert.urls == ("https://example.invalid/listing/1",)
    assert source_from_sender(alert.sender) == "example.invalid"


def test_extract_listing_urls_from_seloger_html_prefers_ad_image_link() -> None:
    html = """
    <a href="https://click.by.seloger.com/?qs=logo" name="logo">logo</a>
    <a href="https://click.by.seloger.com/?qs=good" name="adimage1_1">image</a>
    <a href="https://click.by.seloger.com/?qs=price" name="adprice1_1">price</a>
    <a href="https://click.by.seloger.com/?qs=button" name="adbutton1_1">Voir l'annonce</a>
    <a href="https://click.by.seloger.com/?qs=footer" name="footer_privacy">privacy</a>
    """

    assert extract_listing_urls_from_html(html) == ["https://click.by.seloger.com/?qs=good"]


def test_parse_email_alert_uses_seloger_html_listing_link() -> None:
    raw_message = (
        b"From: SeLoger <annonces@alertes.seloger.com>\r\n"
        b"Subject: 1 nouvelle annonce : Var\r\n"
        b"Date: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
        b"Message-ID: <abc@example.invalid>\r\n"
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
        b'<a href="https://click.by.seloger.com/?qs=button" name="adbutton1_1">Voir</a>\r\n'
        b"--boundary--\r\n"
    )

    alert = parse_email_alert("42", raw_message)

    assert alert.urls == ("https://click.by.seloger.com/?qs=wrong",)
    assert alert.listing_urls == ("https://click.by.seloger.com/?qs=good",)
