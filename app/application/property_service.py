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
            payload: dict[str, Any] = {
                **property_model.__dict__,
                "listing_count": listing_count,
                "first_seen_at": _as_utc(first_seen_at),
                "last_seen_at": _as_utc(last_seen_at),
            }
            result.append(PropertyRead.model_validate(payload))
        return result
