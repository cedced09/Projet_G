from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate
from app.infrastructure.db.models import ListingModel


class ListingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, data: ListingCreate) -> ListingModel:
        payload = data.model_dump()
        payload["source_url"] = str(data.source_url)
        model = ListingModel(**payload)
        self._session.add(model)
        self._session.flush()
        return model

    def list_for_property(self, property_id: UUID) -> list[ListingModel]:
        stmt = (
            select(ListingModel)
            .where(ListingModel.property_id == property_id)
            .order_by(ListingModel.first_seen_at.desc())
        )
        return list(self._session.scalars(stmt).all())
