from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo

import streamlit as st
from sqlalchemy.orm import Session

from app.application.email_ingestion_service import EmailIngestionService
from app.application.listing_service import (
    HtmlAutoDownloadNotAllowedError,
    ListingNotFoundError,
    ListingService,
    PropertyNotFoundError,
)
from app.application.property_service import PropertyService
from app.domain.enums import PropertyStatus
from app.infrastructure.db.session import build_session_factory
from app.infrastructure.ingestion.imap_client import (
    EmailAuthenticationError,
    EmailConfigurationError,
)
from app.infrastructure.storage.browser_preview import BrowserPreviewError, open_html_preview
from app.infrastructure.storage.local_file_dialog import LocalFileDialogError, select_html_file
from app.infrastructure.storage.local_html_archive import LocalHtmlArchiveError
from app.settings import Settings
from app.ui.pages.var_map import render_var_map_page


def _parse_int(value: str) -> int | None:
    clean_value = value.strip()
    if clean_value == "":
        return None
    return int(clean_value)


def _session_factory() -> Callable[[], Session]:
    return build_session_factory(Settings().database_url)


def _listing_service(session: Session) -> ListingService:
    return ListingService(session)


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
    for item in rows:
        with st.container(border=True):
            title_col, details_col, action_col = st.columns([5, 4, 3], vertical_alignment="center")
            with title_col:
                html_badge = _html_icon_badge(item.primary_listing_html_saved_at)
                st.markdown(
                    f"**{item.primary_listing_public_id or 'Sans annonce'} · "
                    f"{item.internal_title}** {html_badge}",
                    unsafe_allow_html=True,
                )
                st.caption(
                    " · ".join(
                        value
                        for value in [
                            _format_sources(item.sources),
                            item.municipality,
                            _format_euros(item.price_cents),
                            _format_datetime(item.last_seen_at),
                        ]
                        if value
                    )
                )
            with details_col:
                st.markdown(
                    _feature_chips(
                        [
                            ("Pièces", item.room_count),
                            ("Surface", _format_m2(item.living_area_m2)),
                            ("Terrain", _format_m2(item.land_area_m2)),
                            ("Chambres", item.bedroom_count),
                            ("Piscine", _format_bool(item.has_pool)),
                            ("Annonces", item.listing_count),
                        ]
                    ),
                    unsafe_allow_html=True,
                )
            with action_col:
                _property_open_actions(
                    session=session,
                    listing_id=item.primary_listing_id,
                    public_id=item.primary_listing_public_id,
                    source_url=item.primary_listing_url,
                )


def _email_ingestion(session: Session) -> None:
    st.subheader("Alertes email")
    if st.button("Importer les nouvelles alertes email"):
        try:
            result = EmailIngestionService(session).import_alerts()
        except (EmailAuthenticationError, EmailConfigurationError) as exc:
            st.error(str(exc))
            return
        st.success(
            "Import terminé : "
            f"{result.items_seen} URL vues, "
            f"{result.items_created} annonces créées, "
            f"{result.items_updated} annonces mises à jour, "
            f"{result.messages_ignored} emails ignorés, "
            f"{result.error_count} erreurs."
        )

    unlinked = _listing_service(session).list_unlinked()
    if not unlinked:
        st.info("Aucune annonce email non rattachée.")
        return

    st.caption("Annonces importées à qualifier")
    for item in unlinked:
        with st.container(border=True):
            title_col, details_col, action_col = st.columns([5, 4, 3], vertical_alignment="center")
            with title_col:
                st.markdown(
                    f"**{item.public_id} · {item.title}** "
                    f"{_html_icon_badge(item.page_html_saved_at)}",
                    unsafe_allow_html=True,
                )
                st.caption(
                    " · ".join(
                        value
                        for value in [
                            _format_source(item.source),
                            item.municipality or item.raw_location,
                            _format_euros(item.current_price_cents),
                            _format_datetime(item.last_seen_at),
                        ]
                        if value
                    )
                )
            with details_col:
                st.markdown(
                    _feature_chips(
                        [
                            ("Pièces", item.room_count),
                            ("Surface", _format_m2(item.living_area_m2)),
                            ("Terrain", _format_m2(item.land_area_m2)),
                            ("Chambres", item.bedroom_count),
                            ("Piscine", _format_bool(item.has_pool)),
                        ]
                    ),
                    unsafe_allow_html=True,
                )
            with action_col:
                open_col, html_col, register_col = st.columns(3)
                with open_col:
                    st.link_button("Ouvrir", str(item.source_url), use_container_width=True)
                with html_col:
                    _listing_html_popover(
                        session=session,
                        listing_id=item.id,
                        public_id=item.public_id,
                        saved_at=item.page_html_saved_at,
                    )
                with register_col:
                    if st.button(
                        "Créer bien",
                        key=f"register-{item.id}",
                        use_container_width=True,
                    ):
                        try:
                            property_read = _listing_service(session).register_listing_as_property(
                                item.id
                            )
                        except (ListingNotFoundError, PropertyNotFoundError) as exc:
                            st.error(str(exc))
                        else:
                            st.success(f"Bien enregistré : {property_read.internal_title}")
                            st.rerun()


def _listing_html_popover(
    *,
    session: Session,
    listing_id: UUID,
    public_id: str,
    saved_at: datetime | None,
) -> None:
    with st.popover("HTML", use_container_width=True):
        st.markdown(_html_status_badge(saved_at), unsafe_allow_html=True)
        if saved_at is not None:
            st.caption(f"Ajouté le {_format_datetime(saved_at)}")
        if st.button(
            "Télécharger depuis la source",
            key=f"download-source-{listing_id}",
            use_container_width=True,
        ):
            _download_html_from_source(session, listing_id)
        _html_import_controls(session, listing_id, key_prefix="listing")
        _download_saved_html(session, listing_id, public_id)


def _html_import_controls(session: Session, listing_id: UUID, *, key_prefix: str) -> None:
    if st.button(
        "Choisir et importer le HTML",
        key=f"{key_prefix}-local-html-import-{listing_id}",
        use_container_width=True,
    ):
        _select_and_import_local_html_archive(session, listing_id)
    st.caption(
        "Sélectionne le fichier HTML principal. "
        "Le dossier voisin créé par Chrome est archivé automatiquement."
    )


def _database_cleanup(session: Session) -> None:
    st.subheader("Nettoyage de la base")
    listing_service = _listing_service(session)
    property_service = PropertyService(session)
    properties = property_service.list_properties()
    unlinked = listing_service.list_unlinked()

    with st.expander("Supprimer des entrées de test"):
        st.caption("Chaque suppression nécessite de saisir SUPPRIMER.")

        if unlinked:
            listing_options = {
                f"{item.public_id} | {item.title} | {item.source} | {item.source_url}": item.id
                for item in unlinked
            }
            selected_listing = st.selectbox(
                "Annonce non rattachée à supprimer",
                options=list(listing_options.keys()),
            )
            listing_confirmation = st.text_input(
                "Confirmation annonce",
                key="delete_listing_confirmation",
                placeholder="SUPPRIMER",
            )
            if st.button("Supprimer cette annonce"):
                if listing_confirmation != "SUPPRIMER":
                    st.error("Saisis SUPPRIMER pour confirmer.")
                else:
                    try:
                        listing_service.delete_listing(listing_options[selected_listing])
                    except ListingNotFoundError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Annonce supprimée.")
                        st.rerun()
        else:
            st.info("Aucune annonce non rattachée à supprimer.")

        if properties:
            property_options = {
                (
                    f"{item.internal_title} | "
                    f"{item.municipality or 'localisation inconnue'} | "
                    f"{item.id}"
                ): item.id
                for item in properties
            }
            selected_property = st.selectbox(
                "Bien à supprimer avec ses annonces rattachées",
                options=list(property_options.keys()),
            )
            property_confirmation = st.text_input(
                "Confirmation bien",
                key="delete_property_confirmation",
                placeholder="SUPPRIMER",
            )
            if st.button("Supprimer ce bien"):
                if property_confirmation != "SUPPRIMER":
                    st.error("Saisis SUPPRIMER pour confirmer.")
                else:
                    try:
                        property_service.delete_property(property_options[selected_property])
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Bien supprimé.")
                        st.rerun()
        else:
            st.info("Aucun bien à supprimer.")


def _format_bool(value: bool | None) -> str:
    if value is True:
        return "Oui"
    if value is False:
        return "Non"
    return "Inconnu"


def _format_euros(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value / 100:,.0f} €".replace(",", " ")


def _format_m2(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == value.to_integral_value():
        return f"{int(value)} m²"
    return f"{value.normalize()} m²"


def _format_source(value: str | None) -> str | None:
    if value is None:
        return None
    if "seloger" in value.lower():
        return "SeLoger"
    if value == "manual":
        return "Manuel"
    return value


def _format_sources(value: str | None) -> str | None:
    if value is None:
        return None
    return ", ".join(
        source
        for source in dict.fromkeys(_format_source(item.strip()) for item in value.split(","))
        if source
    )


def _feature_chips(values: list[tuple[str, object | None]]) -> str:
    chips = [
        _feature_chip(label, value)
        for label, value in values
        if value is not None and value != "Inconnu"
    ]
    if not chips:
        return '<span style="color:#64748b;">Aucune caractéristique extraite</span>'
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">'
        + "".join(chips)
        + "</div>"
    )


def _feature_chip(label: str, value: object) -> str:
    return (
        '<span style="display:inline-flex;align-items:center;gap:4px;'
        "padding:5px 8px;border-radius:4px;background:#f8fafc;"
        "border:1px solid #dbe3ec;color:#243b53;font-size:0.9rem;"
        'line-height:1.15;">'
        f'<span style="font-weight:700;color:#627d98;">{escape(label)}</span>'
        f"<span>{escape(str(value))}</span>"
        "</span>"
    )


def _html_status_badge(saved_at: datetime | None) -> str:
    if saved_at is None:
        return (
            '<span style="display:inline-block;padding:4px 8px;border-radius:4px;'
            "background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;"
            'font-weight:700;">HTML à ajouter</span>'
        )
    return (
        '<span style="display:inline-block;padding:4px 8px;border-radius:4px;'
        "background:#ecfdf3;color:#166534;border:1px solid #bbf7d0;"
        'font-weight:700;">HTML enrichi</span>'
    )


def _download_saved_html(session: Session, listing_id: UUID, public_id: str) -> None:
    html = _listing_service(session).get_saved_html(listing_id)
    if html is None:
        return
    st.download_button(
        "Télécharger le HTML",
        data=html.encode("utf-8"),
        file_name=f"{public_id}.html",
        mime="text/html",
        key=f"download-{public_id}",
        use_container_width=True,
    )


def _download_html_from_source(session: Session, listing_id: UUID) -> None:
    settings = Settings()
    try:
        _listing_service(session).download_and_enrich_listing_from_source(
            listing_id,
            allowed_domains=settings.html_auto_download_allowed_domains,
        )
    except HtmlAutoDownloadNotAllowedError as exc:
        st.warning(str(exc))
    except ListingNotFoundError as exc:
        st.error(str(exc))
    except RuntimeError as exc:
        st.error(f"Téléchargement impossible : {exc}")
    else:
        st.success("HTML téléchargé, archivé et analysé.")
        st.rerun()


def _import_local_html_archive(session: Session, listing_id: UUID, local_html_path: Path) -> None:
    try:
        _listing_service(session).enrich_listing_from_local_html_file(
            listing_id,
            local_html_path,
        )
    except (ListingNotFoundError, LocalHtmlArchiveError) as exc:
        st.error(str(exc))
    except OSError as exc:
        st.error(f"Lecture impossible : {exc}")
    else:
        st.success("HTML local et dossier associé archivés.")
        st.rerun()


def _select_and_import_local_html_archive(session: Session, listing_id: UUID) -> None:
    try:
        html_path = select_html_file(Settings().html_import_directories)
    except LocalFileDialogError as exc:
        st.error(str(exc))
        return
    if html_path is None:
        st.info("Import annulé.")
        return
    _import_local_html_archive(session, listing_id, html_path)


def _property_open_actions(
    *,
    session: Session,
    listing_id: UUID | None,
    public_id: str | None,
    source_url: str | None,
) -> None:
    open_col, saved_col = st.columns(2)
    if source_url is not None:
        with open_col:
            st.link_button("Site web", source_url, use_container_width=True)
        with saved_col:
            _open_saved_html_button(session=session, listing_id=listing_id, public_id=public_id)
    else:
        st.warning("Aucune URL source.")
        with saved_col:
            _open_saved_html_button(session=session, listing_id=listing_id, public_id=public_id)


def _open_saved_html_button(
    *,
    session: Session,
    listing_id: UUID | None,
    public_id: str | None,
) -> None:
    if st.button(
        "Sauvegarde",
        key=f"open-saved-html-{public_id or listing_id or 'none'}",
        disabled=listing_id is None,
        use_container_width=True,
    ):
        if listing_id is None or public_id is None:
            st.info("Aucun HTML sauvegardé pour ce bien.")
            return
        html = _listing_service(session).get_renderable_saved_html(listing_id)
        if html is None:
            st.info("Aucun HTML sauvegardé pour ce bien.")
            return
        try:
            open_html_preview(
                html,
                public_id,
                preview_dir=Path("data/html-preview"),
            )
        except (BrowserPreviewError, OSError) as exc:
            st.error(str(exc))


def _compact_html_indicator(saved_at: datetime | None) -> str:
    if saved_at is None:
        return (
            '<span title="Aucun HTML sauvegardé" '
            'style="display:inline-block;padding:3px 7px;border-radius:4px;'
            "background:#f8fafc;color:#64748b;border:1px solid #cbd5e1;"
            'font-weight:700;">HTML absent</span>'
        )
    return (
        '<span title="HTML sauvegardé" '
        'style="display:inline-block;padding:3px 7px;border-radius:4px;'
        "background:#ecfdf3;color:#166534;border:1px solid #bbf7d0;"
        'font-weight:700;">HTML dispo</span>'
    )


def _html_icon_badge(saved_at: datetime | None) -> str:
    if saved_at is None:
        return (
            '<span title="Aucun HTML sauvegardé" '
            'style="display:inline-block;margin-left:6px;padding:2px 6px;'
            "border-radius:4px;background:#fff7ed;color:#9a3412;"
            "border:1px solid #fed7aa;font-size:0.75rem;font-weight:800;"
            'vertical-align:middle;">HTML -</span>'
        )
    return (
        '<span title="HTML sauvegardé" '
        'style="display:inline-block;margin-left:6px;padding:2px 6px;'
        "border-radius:4px;background:#ecfdf3;color:#166534;"
        "border:1px solid #bbf7d0;font-size:0.75rem;font-weight:800;"
        'vertical-align:middle;">HTML OK</span>'
    )


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    months = {
        1: "janvier",
        2: "février",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "août",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "décembre",
    }
    local_value = value.astimezone(ZoneInfo("Europe/Paris")) if value.tzinfo else value
    return (
        f"{local_value.day} {months[local_value.month]} "
        f"{local_value.hour:02d}h{local_value.minute:02d}"
    )


def main() -> None:
    st.set_page_config(page_title="Gite Agent", layout="wide")
    st.title("Gite Agent")
    page = st.sidebar.radio("Page", ["Tableau de bord", "Carte du Var", "Nettoyage"])
    session_factory = _session_factory()
    with session_factory() as session:
        if page == "Carte du Var":
            render_var_map_page(session)
        elif page == "Nettoyage":
            _database_cleanup(session)
        else:
            _email_ingestion(session)
            _properties_table(session)


if __name__ == "__main__":
    main()
