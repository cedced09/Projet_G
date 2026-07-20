from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import ListingCreate, ListingRead, PropertyCreate, PropertyRead
from app.infrastructure.db.repositories.listings import ListingRepository
from app.infrastructure.db.repositories.properties import PropertyRepository


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
            )
        )
        self._listings.attach_to_property(listing, property_model.id)
        self._session.commit()
        return PropertyRead.model_validate(property_model)
