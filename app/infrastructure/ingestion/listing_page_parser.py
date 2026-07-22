import json
import re
from dataclasses import dataclass
from decimal import Decimal
from html import unescape
from html.parser import HTMLParser
from typing import Any

NUMBER_PATTERN = r"(?:\d{1,3}(?:[ \u202f\xa0]\d{3})+|\d+)"
PRICE_PATTERN = re.compile(rf"({NUMBER_PATTERN})\s*€")
ROOM_COUNT_PATTERN = re.compile(r"(\d+)\s*pi[eè]ces?", re.IGNORECASE)
BEDROOM_COUNT_PATTERN = re.compile(r"(\d+)\s*chambres?", re.IGNORECASE)
SURFACE_PATTERN = re.compile(rf"({NUMBER_PATTERN})\s*m[²2]\b", re.IGNORECASE)
MUNICIPALITY_PATTERN = re.compile(r"([A-ZÀ-Ÿ][A-Za-zÀ-ÿ' -]+)\s*\(\d{5}\)")
TITLE_PATTERN = re.compile(
    r"\b((?:Maison/villa|Maison|Villa|Appartement|Propri[eé]t[eé]|Domaine)"
    r"\s+\d+\s*pi[eè]ces?\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ' -]+))\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ListingPageDetails:
    title: str | None = None
    description: str | None = None
    current_price_cents: int | None = None
    room_count: int | None = None
    living_area_m2: Decimal | None = None
    land_area_m2: Decimal | None = None
    bedroom_count: int | None = None
    has_pool: bool | None = None
    municipality: str | None = None


class PageHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.json_ld_parts: list[str] = []
        self.meta_title: str | None = None
        self.meta_description: str | None = None
        self._ignored_depth = 0
        self._in_json_ld_script = False
        self._json_ld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value for name, value in attrs if value is not None}
        if tag.lower() in {"style", "noscript"}:
            self._ignored_depth += 1
        if tag.lower() == "script":
            if attributes.get("type", "").lower() == "application/ld+json":
                self._in_json_ld_script = True
                self._json_ld_buffer = []
            else:
                self._ignored_depth += 1
        if tag.lower() == "meta":
            name = attributes.get("name", "").lower()
            prop = attributes.get("property", "").lower()
            content = attributes.get("content")
            if content and prop == "og:title":
                self.meta_title = _normalize_text(content)
            if content and (name == "description" or prop == "og:description"):
                self.meta_description = _normalize_text(content)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_json_ld_script:
            self._in_json_ld_script = False
            self.json_ld_parts.append("".join(self._json_ld_buffer))
            self._json_ld_buffer = []
            return
        if tag.lower() in {"style", "script", "noscript"} and self._ignored_depth > 0:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_json_ld_script:
            self._json_ld_buffer.append(data)
            return
        if self._ignored_depth > 0:
            return
        clean_data = _normalize_text(data)
        if clean_data:
            self.text_parts.append(clean_data)


def parse_listing_page_html(html: str) -> ListingPageDetails:
    parser = PageHtmlParser()
    parser.feed(html)
    page_text = _normalize_text(" | ".join(parser.text_parts))
    json_details = _details_from_json_ld(parser.json_ld_parts)
    text_details = _details_from_text(page_text)
    return ListingPageDetails(
        title=_first_meaningful_title(json_details.title, parser.meta_title, text_details.title),
        description=json_details.description or parser.meta_description,
        current_price_cents=json_details.current_price_cents or text_details.current_price_cents,
        room_count=json_details.room_count or text_details.room_count,
        living_area_m2=json_details.living_area_m2 or text_details.living_area_m2,
        land_area_m2=json_details.land_area_m2 or text_details.land_area_m2,
        bedroom_count=json_details.bedroom_count or text_details.bedroom_count,
        has_pool=(
            json_details.has_pool if json_details.has_pool is not None else text_details.has_pool
        ),
        municipality=json_details.municipality or text_details.municipality,
    )


def _details_from_json_ld(json_ld_parts: list[str]) -> ListingPageDetails:
    values: list[Any] = []
    for raw_json in json_ld_parts:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        values.extend(parsed if isinstance(parsed, list) else [parsed])

    flat_objects = [obj for value in values for obj in _walk_dicts(value)]
    title = _first_string(flat_objects, "name", "headline")
    description = _first_string(flat_objects, "description")
    municipality = _first_string(flat_objects, "addressLocality")
    price = _first_number(flat_objects, "price")
    room_count = _first_number(flat_objects, "numberOfRooms")
    return ListingPageDetails(
        title=title,
        description=description,
        current_price_cents=int(price * 100) if price is not None else None,
        room_count=int(room_count) if room_count is not None else None,
        municipality=municipality,
    )


def _details_from_text(text: str) -> ListingPageDetails:
    room_count = _extract_first_int(ROOM_COUNT_PATTERN, text)
    surfaces = [_surface_decimal(match, room_count) for match in SURFACE_PATTERN.findall(text)]
    municipality_match = MUNICIPALITY_PATTERN.search(text)
    title_match = TITLE_PATTERN.search(text)
    return ListingPageDetails(
        title=_normalize_text(title_match.group(1)) if title_match else None,
        current_price_cents=_extract_price_cents(text),
        room_count=room_count,
        living_area_m2=surfaces[0] if surfaces else None,
        land_area_m2=max(surfaces[1:]) if len(surfaces) > 1 else None,
        bedroom_count=_extract_first_int(BEDROOM_COUNT_PATTERN, text),
        has_pool=True if re.search(r"\bpiscine\b", text, re.IGNORECASE) else None,
        municipality=_extract_municipality(municipality_match, title_match),
    )


def _walk_dicts(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        result = [value]
        for nested_value in value.values():
            result.extend(_walk_dicts(nested_value))
        return result
    if isinstance(value, list):
        return [item for nested_value in value for item in _walk_dicts(nested_value)]
    return []


def _first_string(objects: list[dict[str, Any]], *keys: str) -> str | None:
    for obj in objects:
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return _normalize_text(value)
    return None


def _first_number(objects: list[dict[str, Any]], key: str) -> Decimal | None:
    for obj in objects:
        value = obj.get(key)
        if isinstance(value, int | float | str):
            clean_value = str(value).replace(",", ".")
            try:
                return Decimal(clean_value)
            except Exception:
                continue
    return None


def _extract_price_cents(value: str) -> int | None:
    match = PRICE_PATTERN.search(value)
    if match is None:
        return None
    return int(_digits(match.group(1))) * 100


def _extract_first_int(pattern: re.Pattern[str], value: str) -> int | None:
    match = pattern.search(value)
    return int(match.group(1)) if match is not None else None


def _extract_municipality(
    municipality_match: re.Match[str] | None,
    title_match: re.Match[str] | None,
) -> str | None:
    if municipality_match is not None:
        return _normalize_text(municipality_match.group(1))
    if title_match is not None:
        return _normalize_text(title_match.group(2)).title()
    return None


def _first_meaningful_title(*values: str | None) -> str | None:
    for value in values:
        if value is not None and not _is_generic_title(value):
            return value
    return None


def _is_generic_title(value: str) -> bool:
    normalized = _normalize_text(value).lower()
    return normalized in {"seloger", "se loger", "annonce immobilière", "annonce immobiliere"}


def _surface_decimal(value: str, room_count: int | None) -> Decimal:
    digit_groups = re.findall(r"\d+", value)
    if (
        room_count is not None
        and len(digit_groups) == 2
        and int(digit_groups[0]) == room_count
        and int("".join(digit_groups)) > 10_000
    ):
        return Decimal(digit_groups[1])
    return Decimal("".join(digit_groups))


def _normalize_text(value: str) -> str:
    return unescape(re.sub(r"\s+", " ", value)).strip()


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)
