from dataclasses import dataclass


@dataclass(frozen=True)
class ListingMapMarker:
    public_id: str
    title: str
    source_url: str
    municipality: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class UnmappedListing:
    public_id: str | None
    title: str
    municipality: str | None
    reason: str


@dataclass(frozen=True)
class ListingMap:
    markers: list[ListingMapMarker]
    unmapped: list[UnmappedListing]
