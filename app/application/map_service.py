from sqlalchemy.orm import Session

from app.domain.map import ListingMap, ListingMapMarker, UnmappedListing
from app.infrastructure.geocoding.var_communes import find_var_commune_coordinates

from .property_service import PropertyService


class MapService:
    def __init__(self, session: Session) -> None:
        self._properties = PropertyService(session)

    def list_var_listing_markers(self) -> ListingMap:
        markers: list[ListingMapMarker] = []
        unmapped: list[UnmappedListing] = []
        for property_read in self._properties.list_properties():
            title = property_read.internal_title
            public_id = property_read.primary_listing_public_id
            source_url = property_read.primary_listing_url
            coordinates = find_var_commune_coordinates(property_read.municipality)
            latitude = property_read.latitude
            longitude = property_read.longitude
            if coordinates is not None and (latitude is None or longitude is None):
                latitude = coordinates.latitude
                longitude = coordinates.longitude

            if public_id is None or source_url is None:
                unmapped.append(
                    UnmappedListing(
                        public_id=public_id,
                        title=title,
                        municipality=property_read.municipality,
                        reason="Aucune annonce principale cliquable.",
                    )
                )
                continue
            if latitude is None or longitude is None:
                unmapped.append(
                    UnmappedListing(
                        public_id=public_id,
                        title=title,
                        municipality=property_read.municipality,
                        reason=(
                            "Commune absente du référentiel local et coordonnées non renseignées."
                        ),
                    )
                )
                continue

            markers.append(
                ListingMapMarker(
                    public_id=public_id,
                    title=title,
                    source_url=source_url,
                    municipality=property_read.municipality or "Localisation inconnue",
                    latitude=latitude,
                    longitude=longitude,
                )
            )
        return ListingMap(markers=markers, unmapped=unmapped)
