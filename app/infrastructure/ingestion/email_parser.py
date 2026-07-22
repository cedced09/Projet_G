import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser

URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
ROOM_COUNT_PATTERN = re.compile(r"(\d+)\s*pi[eè]ce", re.IGNORECASE)
BEDROOM_COUNT_PATTERN = re.compile(r"(\d+)\s*chambre", re.IGNORECASE)
SURFACE_PATTERN = re.compile(r"(\d[\d\s\u202f\xa0]*)\s*m[²2]", re.IGNORECASE)
PRICE_PATTERN = re.compile(r"(\d[\d\s\u202f\xa0]*)\s*€")


@dataclass(frozen=True)
class EmailListingCandidate:
    source_url: str
    title: str | None = None
    raw_location: str | None = None
    municipality: str | None = None
    current_price_cents: int | None = None
    room_count: int | None = None
    living_area_m2: Decimal | None = None
    land_area_m2: Decimal | None = None
    bedroom_count: int | None = None
    has_pool: bool | None = None


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
    listing_candidates: tuple[EmailListingCandidate, ...]


def parse_email_alert(uid: str, raw_message: bytes) -> EmailAlert:
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    body_text, html_text = _extract_body_parts(message)
    listing_candidates = tuple(extract_listing_candidates_from_html(html_text))
    return EmailAlert(
        uid=uid,
        message_id=_header_as_text(message, "Message-ID"),
        sender=parseaddr(_header_as_text(message, "From") or "")[1],
        subject=_header_as_text(message, "Subject") or "Alerte email immobiliere",
        sent_at=_parse_date(_header_as_text(message, "Date")),
        body_text=body_text,
        urls=tuple(extract_urls(body_text)),
        listing_candidates=listing_candidates,
        listing_urls=tuple(candidate.source_url for candidate in listing_candidates),
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
    return [candidate.source_url for candidate in extract_listing_candidates_from_html(html)]


def extract_listing_candidates_from_html(html: str) -> list[EmailListingCandidate]:
    parser = ListingLinkParser()
    parser.feed(html)
    return parser.listing_candidates()


def is_real_listing_candidate(candidate: EmailListingCandidate) -> bool:
    return any(
        value is not None
        for value in (
            candidate.current_price_cents,
            candidate.room_count,
            candidate.living_area_m2,
            candidate.land_area_m2,
            candidate.bedroom_count,
        )
    )


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
        self._texts_by_listing: dict[int, dict[str, list[str]]] = {}
        self._current_listing: int | None = None
        self._current_link_type: str | None = None

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
        self._texts_by_listing.setdefault(listing_number, {})
        self._texts_by_listing[listing_number].setdefault(link_type, [])
        self._current_listing = listing_number
        self._current_link_type = link_type

    def handle_data(self, data: str) -> None:
        if self._current_listing is None or self._current_link_type is None:
            return
        clean_data = _normalize_text(data)
        if clean_data:
            self._texts_by_listing[self._current_listing][self._current_link_type].append(
                clean_data
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a":
            self._current_listing = None
            self._current_link_type = None

    def listing_urls(self) -> list[str]:
        return [candidate.source_url for candidate in self.listing_candidates()]

    def listing_candidates(self) -> list[EmailListingCandidate]:
        priority = ("adimage", "adbutton", "adtype", "adprice", "adcriteria", "adlocation")
        candidates: list[EmailListingCandidate] = []
        seen: set[str] = set()
        for listing_number in sorted(self._links_by_listing):
            links = self._links_by_listing[listing_number]
            url = None
            for link_type in priority:
                candidate_url = links.get(link_type)
                if candidate_url is not None and candidate_url not in seen:
                    url = candidate_url
                    seen.add(candidate_url)
                    break
            if url is None:
                continue
            texts = self._texts_by_listing.get(listing_number, {})
            candidates.append(_candidate_from_parts(url, texts))
        return candidates


def _candidate_from_parts(
    source_url: str,
    texts_by_type: dict[str, list[str]],
) -> EmailListingCandidate:
    title = _joined_text(texts_by_type.get("adtype", []))
    price_text = _joined_text(texts_by_type.get("adprice", []))
    criteria_text = _joined_text(texts_by_type.get("adcriteria", []))
    location_text = _joined_text(texts_by_type.get("adlocation", []))
    all_text = " ".join(value for values in texts_by_type.values() for value in values)
    surfaces = _extract_surfaces(criteria_text or title or all_text)
    return EmailListingCandidate(
        source_url=source_url,
        title=title or None,
        raw_location=location_text or None,
        municipality=_extract_municipality(location_text),
        current_price_cents=_extract_price_cents(price_text),
        room_count=_extract_first_int(ROOM_COUNT_PATTERN, criteria_text, title, all_text),
        living_area_m2=surfaces[0] if surfaces else None,
        land_area_m2=surfaces[1] if len(surfaces) > 1 else None,
        bedroom_count=_extract_first_int(BEDROOM_COUNT_PATTERN, title, criteria_text, all_text),
        has_pool=True if re.search(r"\bpiscine\b", all_text, re.IGNORECASE) else None,
    )


def _joined_text(values: list[str]) -> str:
    return _normalize_text(" ".join(values))


def _normalize_text(value: str) -> str:
    return unescape(re.sub(r"\s+", " ", value)).strip()


def _extract_price_cents(value: str) -> int | None:
    match = PRICE_PATTERN.search(value)
    if match is None:
        return None
    return int(_digits(match.group(1))) * 100


def _extract_surfaces(value: str) -> list[Decimal]:
    return [Decimal(_digits(match)) for match in SURFACE_PATTERN.findall(value)]


def _extract_first_int(pattern: re.Pattern[str], *values: str) -> int | None:
    for value in values:
        match = pattern.search(value)
        if match is not None:
            return int(match.group(1))
    return None


def _extract_municipality(value: str) -> str | None:
    clean_value = _normalize_text(re.sub(r"\(\d{5}\)", "", value))
    return clean_value or None


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


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
