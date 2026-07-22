from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities import PropertyCreate, PropertyRead
from app.domain.enums import PropertyStatus
from app.infrastructure.db.repositories.properties import PropertyRepository


def _as_utc(value: object) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class PropertyService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._properties = PropertyRepository(session)

    def create_property(self, data: PropertyCreate) -> PropertyRead:
        property_model = self._properties.add(data)
        self._session.commit()
        return PropertyRead.model_validate(property_model)

    def get_property(self, property_id: UUID) -> PropertyRead | None:
        property_model = self._properties.get(property_id)
        if property_model is None:
            return None
        return PropertyRead.model_validate(property_model)

    def delete_property(self, property_id: UUID) -> None:
        property_model = self._properties.get(property_id)
        if property_model is None:
            raise ValueError(f"Property {property_id} does not exist.")
        self._properties.delete(property_model)
        self._session.commit()

    def list_properties(
        self,
        *,
        text: str | None = None,
        status: PropertyStatus | None = None,
        min_land_area_m2: int | None = None,
        source: str | None = None,
    ) -> list[PropertyRead]:
        rows = self._properties.list(
            text=text,
            status=status,
            min_land_area_m2=min_land_area_m2,
            source=source,
        )
        result: list[PropertyRead] = []
        for property_model, listing_count, first_seen_at, last_seen_at in rows:
            sources = sorted({listing.source for listing in property_model.listings})
            listings = sorted(
                property_model.listings,
                key=lambda listing: listing.created_at,
            )
            payload: dict[str, Any] = {
                **property_model.__dict__,
                "listing_count": listing_count,
                "sources": ", ".join(sources) if sources else None,
                "primary_listing_id": listings[0].id if listings else None,
                "primary_listing_public_id": listings[0].public_id if listings else None,
                "primary_listing_url": listings[0].source_url if listings else None,
                "primary_listing_html_saved_at": (
                    _as_utc(listings[0].page_html_saved_at) if listings else None
                ),
                "first_seen_at": _as_utc(first_seen_at),
                "last_seen_at": _as_utc(last_seen_at),
            }
            result.append(PropertyRead.model_validate(payload))
        return result
