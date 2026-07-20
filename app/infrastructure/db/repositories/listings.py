import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate
from app.infrastructure.db.models import ListingModel

PUBLIC_ID_PATTERN = re.compile(r"^ANN-(\d+)$")


class ListingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, data: ListingCreate) -> ListingModel:
        payload = data.model_dump()
        payload["source_url"] = str(data.source_url)
        payload["public_id"] = self._next_public_id()
        model = ListingModel(**payload)
        self._session.add(model)
        self._session.flush()
        return model

    def get_by_source_url(self, source_url: str) -> ListingModel | None:
        stmt = select(ListingModel).where(ListingModel.source_url == source_url)
        return self._session.scalar(stmt)

    def get(self, listing_id: UUID) -> ListingModel | None:
        return self._session.get(ListingModel, listing_id)

    def touch_seen(self, listing: ListingModel, last_seen_at: datetime) -> ListingModel:
        listing.last_seen_at = last_seen_at
        self._session.flush()
        return listing

    def attach_to_property(self, listing: ListingModel, property_id: UUID) -> ListingModel:
        listing.property_id = property_id
        self._session.flush()
        return listing

    def list_for_property(self, property_id: UUID) -> list[ListingModel]:
        stmt = (
            select(ListingModel)
            .where(ListingModel.property_id == property_id)
            .order_by(ListingModel.first_seen_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def list_unlinked(self) -> list[ListingModel]:
        stmt = (
            select(ListingModel)
            .where(ListingModel.property_id.is_(None))
            .order_by(ListingModel.first_seen_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def delete(self, listing: ListingModel) -> None:
        self._session.delete(listing)
        self._session.flush()

    def _next_public_id(self) -> str:
        public_ids = self._session.scalars(select(ListingModel.public_id)).all()
        max_number = 0
        for public_id in public_ids:
            match = PUBLIC_ID_PATTERN.match(public_id)
            if match is not None:
                max_number = max(max_number, int(match.group(1)))
        return f"ANN-{max_number + 1:04d}"
