from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
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
    room_count: Mapped[int | None] = mapped_column(Integer)
    living_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    land_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    bedroom_count: Mapped[int | None] = mapped_column(Integer)
    has_pool: Mapped[bool | None]
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

    listings: Mapped[list[ListingModel]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class ListingModel(Base):
    __tablename__ = "listings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    public_id: Mapped[str] = mapped_column(String(20), unique=True)
    property_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(String(255))
    raw_location: Mapped[str | None] = mapped_column(Text)
    municipality: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    current_price_cents: Mapped[int | None] = mapped_column(BigInteger)
    room_count: Mapped[int | None] = mapped_column(Integer)
    living_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    land_area_m2: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    bedroom_count: Mapped[int | None] = mapped_column(Integer)
    has_pool: Mapped[bool | None]
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(json_type)
    page_html_path: Mapped[str | None] = mapped_column(Text)
    page_html_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    page_html_sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    property: Mapped[PropertyModel | None] = relationship(back_populates="listings")
    html_archive: Mapped[ListingHtmlArchiveModel | None] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )


class ListingHtmlArchiveModel(Base):
    __tablename__ = "listing_html_archives"

    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_html: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100), default="text/html")

    listing: Mapped[ListingModel] = relationship(back_populates="html_archive")
    assets: Mapped[list[ListingHtmlArchiveAssetModel]] = relationship(
        back_populates="archive",
        cascade="all, delete-orphan",
    )


class ListingHtmlArchiveAssetModel(Base):
    __tablename__ = "listing_html_archive_assets"
    __table_args__ = (
        UniqueConstraint("listing_id", "relative_path", name="uq_listing_html_asset_path"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("listing_html_archives.listing_id", ondelete="CASCADE"),
    )
    relative_path: Mapped[str] = mapped_column(Text)
    content_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    content_type: Mapped[str] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64))
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    archive: Mapped[ListingHtmlArchiveModel] = relationship(back_populates="assets")


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="running")
    items_seen: Mapped[int] = mapped_column(Integer, default=0)
    items_created: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_details: Mapped[list[dict[str, Any]] | None] = mapped_column(json_type)
