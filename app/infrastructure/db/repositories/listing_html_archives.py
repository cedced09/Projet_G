import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.db.models import (
    ListingHtmlArchiveAssetModel,
    ListingHtmlArchiveModel,
    ListingModel,
)


@dataclass(frozen=True)
class HtmlAssetInput:
    relative_path: str
    content_bytes: bytes
    content_type: str


class ListingHtmlArchiveRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        listing: ListingModel,
        *,
        html: str,
        original_filename: str | None = None,
        assets: tuple[HtmlAssetInput, ...] = (),
    ) -> ListingHtmlArchiveModel:
        archive = self.get(listing.id)
        sha256 = hashlib.sha256(html.encode("utf-8")).hexdigest()
        saved_at = datetime.now(UTC)
        if archive is None:
            archive = ListingHtmlArchiveModel(
                listing_id=listing.id,
                content_html=html,
                sha256=sha256,
                saved_at=saved_at,
                original_filename=original_filename,
                content_type="text/html",
            )
            self._session.add(archive)
        else:
            archive.content_html = html
            archive.sha256 = sha256
            archive.saved_at = saved_at
            archive.original_filename = original_filename
            archive.content_type = "text/html"
        archive.assets.clear()
        for asset in assets:
            archive.assets.append(
                ListingHtmlArchiveAssetModel(
                    listing_id=listing.id,
                    relative_path=_normalize_relative_path(asset.relative_path),
                    content_bytes=asset.content_bytes,
                    content_type=asset.content_type,
                    sha256=hashlib.sha256(asset.content_bytes).hexdigest(),
                    saved_at=saved_at,
                )
            )
        self._session.flush()
        return archive

    def get(self, listing_id: UUID) -> ListingHtmlArchiveModel | None:
        return self._session.get(ListingHtmlArchiveModel, listing_id)


def _normalize_relative_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("/")
