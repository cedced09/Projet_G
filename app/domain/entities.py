from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domain.enums import LocationPrecision, PropertyStatus, PropertyType


class PropertyCreate(BaseModel):
    internal_title: str = Field(min_length=1, max_length=255)
    property_type: PropertyType = PropertyType.OTHER
    description: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    living_area_m2: Decimal | None = Field(default=None, ge=0)
    land_area_m2: Decimal | None = Field(default=None, ge=0)
    bedroom_count: int | None = Field(default=None, ge=0)
    accommodation_unit_count: int | None = Field(default=None, ge=0)
    owner_area_separated: bool | None = None
    municipality: str | None = None
    postal_code: str | None = None
    department_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_precision: LocationPrecision | None = None


class PropertyRead(PropertyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PropertyStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    listing_count: int = 0
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class ListingCreate(BaseModel):
    property_id: UUID | None = None
    source: str = Field(min_length=1, max_length=100)
    external_id: str | None = None
    source_url: HttpUrl
    title: str = Field(min_length=1, max_length=255)
    raw_location: str | None = None
    description: str | None = None
    current_price_cents: int | None = Field(default=None, ge=0)
    published_at: datetime | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    raw_payload: dict[str, Any] | None = None


class ListingRead(ListingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    public_id: str
    removed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
