import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser

URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


@dataclass(frozen=True)
class EmailAlert:
    uid: str
    message_id: str | None
    sender: str
    subject: str
    sent_at: datetime | None
    body_text: str
    urls: tuple[str, ...]
    listing_urls: tuple[str, ...]


def parse_email_alert(uid: str, raw_message: bytes) -> EmailAlert:
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    body_text, html_text = _extract_body_parts(message)
    return EmailAlert(
        uid=uid,
        message_id=_header_as_text(message, "Message-ID"),
        sender=parseaddr(_header_as_text(message, "From") or "")[1],
        subject=_header_as_text(message, "Subject") or "Alerte email immobiliere",
        sent_at=_parse_date(_header_as_text(message, "Date")),
        body_text=body_text,
        urls=tuple(extract_urls(body_text)),
        listing_urls=tuple(extract_listing_urls_from_html(html_text)),
    )


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(").,;]'")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def source_from_sender(sender: str) -> str:
    domain = sender.rsplit("@", maxsplit=1)[-1].lower()
    return domain or "email"


def extract_listing_urls_from_html(html: str) -> list[str]:
    parser = ListingLinkParser()
    parser.feed(html)
    return parser.listing_urls()


def _header_as_text(message: Message, name: str) -> str | None:
    value = message.get(name)
    return str(value) if value is not None else None


def _parse_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class ListingLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._links_by_listing: dict[int, dict[str, str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attributes = {name.lower(): value for name, value in attrs if value is not None}
        name = attributes.get("name", "")
        href = attributes.get("href")
        if href is None:
            return

        match = re.match(r"^(adimage|adbutton|adtype|adprice|adcriteria|adlocation)(\d+)_", name)
        if match is None:
            return

        link_type = match.group(1)
        listing_number = int(match.group(2))
        self._links_by_listing.setdefault(listing_number, {})
        self._links_by_listing[listing_number].setdefault(link_type, href)

    def listing_urls(self) -> list[str]:
        priority = ("adimage", "adbutton", "adtype", "adprice", "adcriteria", "adlocation")
        urls: list[str] = []
        seen: set[str] = set()
        for listing_number in sorted(self._links_by_listing):
            links = self._links_by_listing[listing_number]
            for link_type in priority:
                url = links.get(link_type)
                if url is not None and url not in seen:
                    seen.add(url)
                    urls.append(url)
                    break
        return urls


def _extract_body_parts(message: Message) -> tuple[str, str]:
    if message.is_multipart():
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            payload = _part_text(part)
            if payload is None:
                continue
            if part.get_content_type() == "text/plain":
                plain_parts.append(payload)
            elif part.get_content_type() == "text/html":
                html_parts.append(payload)
        html_text = "\n".join(html_parts)
        body_text = "\n".join(plain_parts) if plain_parts else _html_to_text(html_text)
        return body_text, html_text

    payload = _part_text(message)
    if payload is None:
        return "", ""
    if message.get_content_type() == "text/html":
        return _html_to_text(payload), payload
    return payload, ""


def _part_text(part: Message) -> str | None:
    payload = part.get_payload(decode=True)
    if not isinstance(payload, bytes):
        raw_payload = part.get_payload()
        return str(raw_payload) if raw_payload is not None else None
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _html_to_text(html: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html)
    return unescape(re.sub(r"\s+", " ", without_tags))
