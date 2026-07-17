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
