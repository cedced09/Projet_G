from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import streamlit as st
from sqlalchemy.orm import Session

from app.application.listing_service import (
    DuplicateListingError,
    ListingService,
    PropertyNotFoundError,
)
from app.application.property_service import PropertyService
from app.domain.entities import ListingCreate, PropertyCreate
from app.domain.enums import PropertyStatus, PropertyType
from app.domain.value_objects import euro_to_cents
from app.infrastructure.db.session import build_session_factory
from app.settings import Settings


def _parse_decimal(value: str) -> Decimal | None:
    clean_value = value.strip().replace(" ", "").replace(",", ".")
    if clean_value == "":
        return None
    try:
        return Decimal(clean_value)
    except InvalidOperation:
        raise ValueError("La valeur numerique est invalide.") from None


def _parse_int(value: str) -> int | None:
    clean_value = value.strip()
    if clean_value == "":
        return None
    return int(clean_value)


def _session_factory() -> Callable[[], Session]:
    return build_session_factory(Settings().database_url)


def _create_manual_property(session: Session) -> None:
    st.subheader("Créer un bien")
    with st.form("create_property"):
        internal_title = st.text_input("Titre interne")
        property_type = st.selectbox(
            "Type de bien",
            options=list(PropertyType),
            format_func=lambda item: item.value,
        )
        municipality = st.text_input("Commune ou zone")
        price_eur = st.text_input("Prix affiché en euros")
        living_area = st.text_input("Surface habitable en m²")
        land_area = st.text_input("Surface du terrain en m²")
        bedroom_count = st.text_input("Nombre de chambres")
        accommodation_unit_count = st.text_input("Nombre d'unités d'hébergement")
        description = st.text_area("Description libre")
        source = st.text_input("Source", value="manual")
        source_url = st.text_input("URL de l'annonce")
        submitted = st.form_submit_button("Enregistrer")

    if not submitted:
        return

    try:
        now = datetime.now(UTC)
        property_data = PropertyCreate(
            internal_title=internal_title,
            property_type=property_type,
            municipality=municipality or None,
            price_cents=euro_to_cents(_parse_decimal(price_eur)),
            living_area_m2=_parse_decimal(living_area),
            land_area_m2=_parse_decimal(land_area),
            bedroom_count=_parse_int(bedroom_count),
            accommodation_unit_count=_parse_int(accommodation_unit_count),
            description=description or None,
        )
        property_read = PropertyService(session).create_property(property_data)
        listing_data = ListingCreate(
            property_id=property_read.id,
            source=source,
            source_url=source_url,
            title=internal_title,
            raw_location=municipality or None,
            description=description or None,
            current_price_cents=property_data.price_cents,
            first_seen_at=now,
            last_seen_at=now,
        )
        ListingService(session).create_listing(listing_data)
    except (ValueError, DuplicateListingError, PropertyNotFoundError) as exc:
        st.error(str(exc))
        return

    st.success("Bien et annonce enregistrés.")


def _add_listing(session: Session) -> None:
    properties = PropertyService(session).list_properties()
    if not properties:
        return

    st.subheader("Ajouter une annonce à un bien")
    property_options = {f"{item.internal_title} ({item.id})": item.id for item in properties}
    with st.form("add_listing"):
        selected = st.selectbox("Bien", options=list(property_options.keys()))
        title = st.text_input("Titre de l'annonce")
        source = st.text_input("Source de l'annonce", value="manual")
        source_url = st.text_input("URL source")
        price_eur = st.text_input("Prix en euros")
        raw_location = st.text_input("Localisation brute")
        description = st.text_area("Description de l'annonce")
        submitted = st.form_submit_button("Ajouter l'annonce")

    if not submitted:
        return

    try:
        now = datetime.now(UTC)
        ListingService(session).create_listing(
            ListingCreate(
                property_id=property_options[selected],
                title=title,
                source=source,
                source_url=source_url,
                current_price_cents=euro_to_cents(_parse_decimal(price_eur)),
                raw_location=raw_location or None,
                description=description or None,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
    except (ValueError, DuplicateListingError, PropertyNotFoundError) as exc:
        st.error(str(exc))
        return

    st.success("Annonce ajoutée.")


def _properties_table(session: Session) -> None:
    st.subheader("Biens enregistrés")
    with st.expander("Filtres", expanded=True):
        text = st.text_input("Texte")
        status_value = st.selectbox(
            "Statut",
            options=[""] + [status.value for status in PropertyStatus],
        )
        min_land_area = st.text_input("Terrain minimum en m²")
        source = st.text_input("Source")

    status = PropertyStatus(status_value) if status_value else None
    min_land = _parse_int(min_land_area)
    rows = PropertyService(session).list_properties(
        text=text or None,
        status=status,
        min_land_area_m2=min_land,
        source=source or None,
    )
    st.dataframe(
        [
            {
                "Titre": item.internal_title,
                "Commune": item.municipality,
                "Prix": item.price_cents,
                "Terrain": item.land_area_m2,
                "Surface": item.living_area_m2,
                "Statut": item.status.value,
                "Score": None,
                "Première observation": item.first_seen_at,
                "Dernière observation": item.last_seen_at,
                "Annonces": item.listing_count,
            }
            for item in rows
        ],
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    st.set_page_config(page_title="Gite Agent", layout="wide")
    st.title("Gite Agent")
    session_factory = _session_factory()
    with session_factory() as session:
        _create_manual_property(session)
        _add_listing(session)
        _properties_table(session)


if __name__ == "__main__":
    main()
