import base64
import posixpath
import re
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate, ListingRead, PropertyCreate, PropertyRead
from app.infrastructure.db.models import ListingHtmlArchiveAssetModel, ListingModel, PropertyModel
from app.infrastructure.db.repositories.listing_html_archives import (
    HtmlAssetInput,
    ListingHtmlArchiveRepository,
)
from app.infrastructure.db.repositories.listings import ListingRepository
from app.infrastructure.db.repositories.properties import PropertyRepository
from app.infrastructure.ingestion.listing_page_parser import parse_listing_page_html
from app.infrastructure.storage.local_html_archive import load_local_html_archive
from app.infrastructure.web.page_downloader import download_page_html


class HtmlAutoDownloadNotAllowedError(ValueError):
    pass


class PropertyNotFoundError(ValueError):
    pass


class DuplicateListingError(ValueError):
    pass


class ListingNotFoundError(ValueError):
    pass


class ListingService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._listings = ListingRepository(session)
        self._properties = PropertyRepository(session)
        self._html_archives = ListingHtmlArchiveRepository(session)

    def create_listing(self, data: ListingCreate) -> ListingRead:
        if data.property_id is not None and self._properties.get(data.property_id) is None:
            raise PropertyNotFoundError(f"Property {data.property_id} does not exist.")
        try:
            listing = self._listings.add(data)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateListingError("A listing already exists for this URL.") from exc
        return ListingRead.model_validate(listing)

    def list_for_property(self, property_id: UUID) -> list[ListingRead]:
        return [
            ListingRead.model_validate(listing)
            for listing in self._listings.list_for_property(property_id)
        ]

    def list_unlinked(self) -> list[ListingRead]:
        return [ListingRead.model_validate(listing) for listing in self._listings.list_unlinked()]

    def delete_listing(self, listing_id: UUID) -> None:
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(f"Listing {listing_id} does not exist.")
        self._listings.delete(listing)
        self._session.commit()

    def register_listing_as_property(self, listing_id: UUID) -> PropertyRead:
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(f"Listing {listing_id} does not exist.")
        if listing.property_id is not None:
            property_model = self._properties.get(listing.property_id)
            if property_model is None:
                raise PropertyNotFoundError(f"Property {listing.property_id} does not exist.")
            return PropertyRead.model_validate(property_model)

        property_model = self._properties.add(
            PropertyCreate(
                internal_title=listing.title,
                description=listing.description,
                price_cents=listing.current_price_cents,
                room_count=listing.room_count,
                living_area_m2=listing.living_area_m2,
                land_area_m2=listing.land_area_m2,
                bedroom_count=listing.bedroom_count,
                has_pool=listing.has_pool,
                municipality=listing.municipality,
            )
        )
        self._listings.attach_to_property(listing, property_model.id)
        self._session.commit()
        return PropertyRead.model_validate(property_model)

    def enrich_listing_from_page_html(
        self,
        listing_id: UUID,
        html: str,
        *,
        assets: tuple[HtmlAssetInput, ...] = (),
        original_filename: str | None = None,
    ) -> ListingRead:
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(f"Listing {listing_id} does not exist.")
        saved_html = self._html_archives.save(
            listing,
            html=html,
            original_filename=original_filename,
            assets=assets,
        )
        details = parse_listing_page_html(html)
        updated_listing = self._listings.update_from_page_details(listing, details)
        updated_listing = self._listings.mark_page_html_saved(
            updated_listing,
            path=None,
            saved_at=saved_html.saved_at,
            sha256=saved_html.sha256,
        )
        if updated_listing.property_id is not None:
            property_model = self._properties.get(updated_listing.property_id)
            if property_model is not None:
                _copy_listing_details_to_property(updated_listing, property_model)
        self._session.commit()
        return ListingRead.model_validate(updated_listing)

    def enrich_listing_from_local_html_file(self, listing_id: UUID, html_path: Path) -> ListingRead:
        archive = load_local_html_archive(html_path)
        return self.enrich_listing_from_page_html(
            listing_id,
            archive.html,
            assets=archive.assets,
            original_filename=archive.original_filename,
        )

    def download_and_enrich_listing_from_source(
        self,
        listing_id: UUID,
        *,
        allowed_domains: str,
    ) -> ListingRead:
        listing = self._listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(f"Listing {listing_id} does not exist.")
        if not _url_is_allowed(listing.source_url, allowed_domains):
            raise HtmlAutoDownloadNotAllowedError(
                "Le téléchargement HTML automatique n'est pas autorisé pour ce domaine."
            )
        html = download_page_html(listing.source_url)
        return self.enrich_listing_from_page_html(listing_id, html)

    def sync_saved_html_files(self) -> int:
        return 0

    def get_saved_html(self, listing_id: UUID) -> str | None:
        archive = self._html_archives.get(listing_id)
        if archive is None:
            return None
        return archive.content_html

    def get_renderable_saved_html(self, listing_id: UUID) -> str | None:
        archive = self._html_archives.get(listing_id)
        if archive is None:
            return None
        assets_by_path = {
            _normalize_asset_path(asset.relative_path): asset for asset in archive.assets
        }
        assets_by_name = {
            posixpath.basename(asset.relative_path): asset for asset in archive.assets
        }
        return _inline_relative_assets(archive.content_html, assets_by_path, assets_by_name)


def _copy_listing_details_to_property(
    listing: ListingModel,
    property_model: PropertyModel,
) -> None:
    field_pairs = {
        "internal_title": "title",
        "description": "description",
        "price_cents": "current_price_cents",
        "room_count": "room_count",
        "living_area_m2": "living_area_m2",
        "land_area_m2": "land_area_m2",
        "bedroom_count": "bedroom_count",
        "has_pool": "has_pool",
        "municipality": "municipality",
    }
    for property_field, listing_field in field_pairs.items():
        value = getattr(listing, listing_field)
        if value is not None:
            setattr(property_model, property_field, value)


def _url_is_allowed(url: str, allowed_domains: str) -> bool:
    domains = tuple(item.strip().lower() for item in allowed_domains.split(",") if item.strip())
    if not domains:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def _inline_relative_assets(
    html: str,
    assets_by_path: dict[str, ListingHtmlArchiveAssetModel],
    assets_by_name: dict[str, ListingHtmlArchiveAssetModel],
) -> str:
    pattern = re.compile(r"""(?P<attr>\b(?:src|href)=["'])(?P<url>[^"']+)(?P<quote>["'])""")

    def replace(match: re.Match[str]) -> str:
        url = match.group("url")
        asset = _find_asset(url, assets_by_path, assets_by_name)
        if asset is None:
            return match.group(0)
        encoded = base64.b64encode(asset.content_bytes).decode("ascii")
        content_type = asset.content_type
        return f"{match.group('attr')}data:{content_type};base64,{encoded}{match.group('quote')}"

    return pattern.sub(replace, html)


def _find_asset(
    url: str,
    assets_by_path: dict[str, ListingHtmlArchiveAssetModel],
    assets_by_name: dict[str, ListingHtmlArchiveAssetModel],
) -> ListingHtmlArchiveAssetModel | None:
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc or url.startswith(("data:", "#", "mailto:", "tel:")):
        return None
    path = _normalize_asset_path(parsed.path)
    return assets_by_path.get(path) or assets_by_name.get(posixpath.basename(path))


def _normalize_asset_path(value: str) -> str:
    return posixpath.normpath(value.replace("\\", "/").lstrip("/"))
