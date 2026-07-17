from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.domain.enums import LocationPrecision, PropertyStatus, PropertyType


def utc_now() -> datetime:
    return datetime.now(UTC)


def enum_values(
    enum_class: type[PropertyType] | type[PropertyStatus] | type[LocationPrecision],
) -> list[str]:
    return [item.value for item in enum_class]


class Base(DeclarativeBase):
    pass


json_type = JSON().with_variant(JSONB, "postgresql")


class PropertyModel(Base):
    __tablename__ = "properties"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    internal_title: Mapped[str] = mapped_column(String(255))
    property_type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType, native_enum=False, values_callable=enum_values),
        default=PropertyType.OTHER,
    )
    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, native_enum=False, values_callable=enum_values),
        default=PropertyStatus.NEW,
    )
    description: Mapped[str | None] = mapped_column(Text)
    price_cents: Mapped[int | None] = mapped_column(BigInteger)
    living_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    land_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    bedroom_count: Mapped[int | None] = mapped_column(Integer)
    accommodation_unit_count: Mapped[int | None] = mapped_column(Integer)
    owner_area_separated: Mapped[bool | None]
    municipality: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    department_code: Mapped[str | None] = mapped_column(String(10))
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    location_precision: Mapped[LocationPrecision | None] = mapped_column(
        Enum(LocationPrecision, native_enum=False, values_callable=enum_values)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listings: Mapped[list["ListingModel"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class ListingModel(Base):
    __tablename__ = "listings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    property_id: Mapped[UUID] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(String(255))
    raw_location: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    current_price_cents: Mapped[int | None] = mapped_column(BigInteger)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(json_type)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    property: Mapped[PropertyModel] = relationship(back_populates="listings")
