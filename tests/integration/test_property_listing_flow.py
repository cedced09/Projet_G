from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.application.listing_service import DuplicateListingError, ListingService
from app.application.property_service import PropertyService
from app.domain.entities import ListingCreate, PropertyCreate
from app.domain.enums import PropertyStatus, PropertyType


def test_create_property_with_listing_and_list_it(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

    property_read = property_service.create_property(
        PropertyCreate(
            internal_title="Domaine test",
            property_type=PropertyType.ESTATE,
            municipality="Toulon",
            price_cents=275000000,
            living_area_m2=Decimal("620"),
            land_area_m2=Decimal("18000"),
            bedroom_count=14,
            accommodation_unit_count=6,
        )
    )
    listing = listing_service.create_listing(
        ListingCreate(
            property_id=property_read.id,
            source="manual",
            source_url="https://example.invalid/listing/123",
            title="Domaine test",
            raw_location="Var",
            current_price_cents=275000000,
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    rows = property_service.list_properties(status=PropertyStatus.NEW)

    assert listing.property_id == property_read.id
    assert listing.public_id == "ANN-0001"
    assert len(rows) == 1
    assert rows[0].internal_title == "Domaine test"
    assert rows[0].listing_count == 1
    assert rows[0].first_seen_at == seen_at
    assert rows[0].last_seen_at == seen_at


def test_duplicate_listing_url_is_rejected(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    property_read = property_service.create_property(PropertyCreate(internal_title="Domaine test"))
    listing_data = ListingCreate(
        property_id=property_read.id,
        source="manual",
        source_url="https://example.invalid/listing/123",
        title="Domaine test",
        first_seen_at=seen_at,
        last_seen_at=seen_at,
    )

    listing_service.create_listing(listing_data)

    with pytest.raises(DuplicateListingError):
        listing_service.create_listing(listing_data)


def test_delete_unlinked_listing(session: Session) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/unlinked",
            title="Annonce orpheline",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    listing_service.delete_listing(listing.id)

    assert listing_service.list_unlinked() == []


def test_delete_property_cascades_attached_listings(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    property_read = property_service.create_property(PropertyCreate(internal_title="A supprimer"))
    listing_service.create_listing(
        ListingCreate(
            property_id=property_read.id,
            source="manual",
            source_url="https://example.invalid/listing/attached",
            title="Annonce rattachée",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    property_service.delete_property(property_read.id)

    assert property_service.list_properties() == []
    assert listing_service.list_for_property(property_read.id) == []


def test_register_unlinked_listing_as_property(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/imported",
            title="Annonce importée",
            description="Description depuis email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    property_read = listing_service.register_listing_as_property(listing.id)

    assert property_read.internal_title == "Annonce importée"
    assert property_service.list_properties()[0].listing_count == 1
    assert listing_service.list_unlinked() == []
