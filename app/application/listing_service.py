from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate, ListingRead
from app.infrastructure.db.repositories.listings import ListingRepository
from app.infrastructure.db.repositories.properties import PropertyRepository


class PropertyNotFoundError(ValueError):
    pass


class DuplicateListingError(ValueError):
    pass


class ListingService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._listings = ListingRepository(session)
        self._properties = PropertyRepository(session)

    def create_listing(self, data: ListingCreate) -> ListingRead:
        if self._properties.get(data.property_id) is None:
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
