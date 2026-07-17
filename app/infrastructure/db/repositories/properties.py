from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import PropertyCreate
from app.domain.enums import PropertyStatus
from app.infrastructure.db.models import ListingModel, PropertyModel


class PropertyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, data: PropertyCreate) -> PropertyModel:
        model = PropertyModel(**data.model_dump())
        self._session.add(model)
        self._session.flush()
        return model

    def get(self, property_id: UUID) -> PropertyModel | None:
        return self._session.get(PropertyModel, property_id)

    def list(
        self,
        *,
        text: str | None = None,
        status: PropertyStatus | None = None,
        min_land_area_m2: int | None = None,
        source: str | None = None,
    ) -> list[tuple[PropertyModel, int, datetime | None, datetime | None]]:
        stmt = (
            select(
                PropertyModel,
                func.count(ListingModel.id).label("listing_count"),
                func.min(ListingModel.first_seen_at).label("first_seen_at"),
                func.max(ListingModel.last_seen_at).label("last_seen_at"),
            )
            .outerjoin(ListingModel)
            .group_by(PropertyModel.id)
            .order_by(PropertyModel.created_at.desc())
        )
        if text:
            pattern = f"%{text}%"
            stmt = stmt.where(
                PropertyModel.internal_title.ilike(pattern)
                | PropertyModel.municipality.ilike(pattern)
                | PropertyModel.description.ilike(pattern)
            )
        if status:
            stmt = stmt.where(PropertyModel.status == status)
        if min_land_area_m2 is not None:
            stmt = stmt.where(PropertyModel.land_area_m2 >= min_land_area_m2)
        if source:
            stmt = stmt.where(ListingModel.source == source)
        return [(row[0], row[1], row[2], row[3]) for row in self._session.execute(stmt).all()]
