from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.application import listing_service as listing_service_module
from app.application.listing_service import (
    DuplicateListingError,
    HtmlAutoDownloadNotAllowedError,
    ListingService,
)
from app.application.map_service import MapService
from app.application.property_service import PropertyService
from app.domain.entities import ListingCreate, PropertyCreate
from app.domain.enums import PropertyStatus, PropertyType
from app.infrastructure.db.repositories.listing_html_archives import HtmlAssetInput


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
            current_price_cents=180000000,
            room_count=7,
            living_area_m2=Decimal("300"),
            land_area_m2=Decimal("5489"),
            bedroom_count=5,
            has_pool=True,
            municipality="Trans-en-Provence",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    property_read = listing_service.register_listing_as_property(listing.id)

    assert property_read.internal_title == "Annonce importée"
    assert property_read.price_cents == 180000000
    assert property_read.room_count == 7
    assert property_read.living_area_m2 == Decimal("300")
    assert property_read.land_area_m2 == Decimal("5489")
    assert property_read.bedroom_count == 5
    assert property_read.has_pool is True
    assert property_read.municipality == "Trans-en-Provence"
    assert property_service.list_properties()[0].listing_count == 1
    assert property_service.list_properties()[0].primary_listing_public_id == "ANN-0001"
    assert listing_service.list_unlinked() == []


def test_enrich_listing_from_page_html(session: Session) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/page",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    html = """
    <html><body>
      Villa enrichie 8 pièces 4 chambres 320 m² 6000 m² piscine
      Trans-en-Provence (83720) 1 900 000 €
    </body></html>
    """

    enriched = listing_service.enrich_listing_from_page_html(listing.id, html)

    assert enriched.current_price_cents == 190000000
    assert enriched.room_count == 8
    assert enriched.bedroom_count == 4
    assert enriched.living_area_m2 == Decimal("320")
    assert enriched.land_area_m2 == Decimal("6000")
    assert enriched.has_pool is True
    assert enriched.municipality == "Trans-en-Provence"


def test_enrich_listing_from_page_html_archives_html(session: Session) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/page-archive",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    html = "<html><body>Maison 5 pièces 140 m² Toulon (83000)</body></html>"

    enriched = listing_service.enrich_listing_from_page_html(listing.id, html)

    assert enriched.page_html_saved_at is not None
    assert enriched.page_html_sha256 is not None
    assert enriched.page_html_sha256 == sha256(html.encode("utf-8")).hexdigest()
    assert enriched.page_html_path is None
    assert listing_service.get_saved_html(listing.id) == html

    rows = PropertyService(session).list_properties()
    assert rows == []


def test_enrich_listing_from_page_html_archives_associated_assets(
    session: Session,
) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/page-assets",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    html = '<html><body><img src="annonce_fichiers/photo.jpg"></body></html>'

    listing_service.enrich_listing_from_page_html(
        listing.id,
        html,
        assets=(
            HtmlAssetInput(
                relative_path="annonce_fichiers/photo.jpg",
                content_bytes=b"image-bytes",
                content_type="image/jpeg",
            ),
        ),
    )

    rendered_html = listing_service.get_renderable_saved_html(listing.id)

    assert rendered_html is not None
    assert 'src="data:image/jpeg;base64,aW1hZ2UtYnl0ZXM="' in rendered_html


def test_enrich_listing_from_local_html_file_archives_sibling_directory(
    session: Session,
) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="email",
            source_url="https://example.invalid/listing/local-html",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    base_path = Path("tests/_tmp_manual") / uuid4().hex
    try:
        base_path.mkdir(parents=True)
        html_path = base_path / "annonce.html"
        asset_dir = base_path / "annonce_fichiers"
        asset_dir.mkdir()
        html_path.write_text(
            """
            <html><body>
              Maison 5 pièces 140 m² Toulon (83000)
              <img src="annonce_fichiers/photo.jpg">
            </body></html>
            """,
            encoding="utf-8",
        )
        (asset_dir / "photo.jpg").write_bytes(b"photo")

        enriched = listing_service.enrich_listing_from_local_html_file(listing.id, html_path)
    finally:
        rmtree(base_path, ignore_errors=True)
    rendered_html = listing_service.get_renderable_saved_html(listing.id)

    assert enriched.room_count == 5
    assert enriched.living_area_m2 == Decimal("140")
    assert rendered_html is not None
    assert 'src="data:image/jpeg;base64,cGhvdG8="' in rendered_html


def test_download_and_enrich_listing_from_allowed_source(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="authorized",
            source_url="https://source.example/listing/page",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    html = "<html><body>Maison 5 pièces 140 m² Toulon (83000)</body></html>"
    monkeypatch.setattr(listing_service_module, "download_page_html", lambda url: html)

    enriched = listing_service.download_and_enrich_listing_from_source(
        listing.id,
        allowed_domains="source.example",
    )

    assert enriched.room_count == 5
    assert enriched.living_area_m2 == Decimal("140")
    assert listing_service.get_saved_html(listing.id) == html


def test_download_and_enrich_listing_rejects_unallowed_source(session: Session) -> None:
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    listing = listing_service.create_listing(
        ListingCreate(
            source="blocked",
            source_url="https://blocked.example/listing/page",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    with pytest.raises(HtmlAutoDownloadNotAllowedError):
        listing_service.download_and_enrich_listing_from_source(
            listing.id,
            allowed_domains="source.example",
        )

    assert listing_service.get_saved_html(listing.id) is None


def test_enrich_attached_listing_updates_property_summary(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    property_read = property_service.create_property(PropertyCreate(internal_title="Titre email"))
    listing = listing_service.create_listing(
        ListingCreate(
            property_id=property_read.id,
            source="alertes.seloger.com",
            source_url="https://example.invalid/listing/attached-page",
            title="Titre email",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )
    html = """
    <html>
      <head><meta property="og:title" content="Villa SeLoger"></head>
      <body>
        Villa SeLoger 11 pièces 6 chambres 296 m² 1200 m² piscine
        Toulon (83000) 950 000 €
      </body>
    </html>
    """

    listing_service.enrich_listing_from_page_html(listing.id, html)

    rows = property_service.list_properties()
    assert rows[0].internal_title == "Villa SeLoger"
    assert rows[0].price_cents == 95000000
    assert rows[0].room_count == 11
    assert rows[0].living_area_m2 == Decimal("296")
    assert rows[0].land_area_m2 == Decimal("1200")
    assert rows[0].bedroom_count == 6
    assert rows[0].has_pool is True
    assert rows[0].municipality == "Toulon"
    assert rows[0].sources == "alertes.seloger.com"


def test_property_list_exposes_primary_listing_html_metadata(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    property_read = property_service.create_property(PropertyCreate(internal_title="Bien"))
    listing = listing_service.create_listing(
        ListingCreate(
            property_id=property_read.id,
            source="alertes.seloger.com",
            source_url="https://example.invalid/listing/with-html",
            title="Bien",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    listing_service.enrich_listing_from_page_html(
        listing.id,
        "<html><body>Maison 5 pièces 140 m² Toulon (83000)</body></html>",
    )

    rows = property_service.list_properties()
    assert rows[0].primary_listing_url == "https://example.invalid/listing/with-html"
    assert rows[0].primary_listing_id == listing.id
    assert rows[0].primary_listing_html_saved_at is not None


def test_map_service_places_property_from_var_commune(session: Session) -> None:
    property_service = PropertyService(session)
    listing_service = ListingService(session)
    seen_at = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
    property_read = property_service.create_property(
        PropertyCreate(
            internal_title="Maison/villa 11 pièces COLLOBRIERES",
            municipality="Collobrières",
        )
    )
    listing_service.create_listing(
        ListingCreate(
            property_id=property_read.id,
            source="alertes.seloger.com",
            source_url="https://example.invalid/listing/collobrieres",
            title="Maison/villa 11 pièces COLLOBRIERES",
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
    )

    listing_map = MapService(session).list_var_listing_markers()

    assert listing_map.unmapped == []
    assert len(listing_map.markers) == 1
    assert listing_map.markers[0].public_id == "ANN-0001"
    assert listing_map.markers[0].municipality == "Collobrières"
    assert listing_map.markers[0].source_url == "https://example.invalid/listing/collobrieres"
