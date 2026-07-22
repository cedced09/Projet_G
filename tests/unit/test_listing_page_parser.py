from decimal import Decimal

from app.infrastructure.ingestion.listing_page_parser import parse_listing_page_html


def test_parse_listing_page_html_extracts_json_ld_and_text_details() -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Villa avec piscine">
        <script type="application/ld+json">
          {
            "name": "Villa Trans-en-Provence",
            "description": "Belle villa avec piscine",
            "offers": {"price": 1800000},
            "address": {"addressLocality": "Trans-en-Provence"}
          }
        </script>
      </head>
      <body>
        7 pièces 5 chambres 300 m² 5 489 m² piscine
      </body>
    </html>
    """

    details = parse_listing_page_html(html)

    assert details.title == "Villa Trans-en-Provence"
    assert details.description == "Belle villa avec piscine"
    assert details.current_price_cents == 180000000
    assert details.room_count == 7
    assert details.bedroom_count == 5
    assert details.living_area_m2 == Decimal("300")
    assert details.land_area_m2 == Decimal("5489")
    assert details.has_pool is True
    assert details.municipality == "Trans-en-Provence"


def test_parse_listing_page_html_keeps_adjacent_fields_separated() -> None:
    html = """
    <html>
      <body>
        <span>11 pièces</span>
        <span>296 m²</span>
        <span>piscine</span>
      </body>
    </html>
    """

    details = parse_listing_page_html(html)

    assert details.room_count == 11
    assert details.living_area_m2 == Decimal("296")
    assert details.land_area_m2 is None


def test_parse_listing_page_html_repairs_room_count_merged_with_surface() -> None:
    html = """
    <html>
      <head><meta property="og:title" content="SeLoger"></head>
      <body>
        Maison/villa 11 pièces COLLOBRIERES
        11 296 m²
      </body>
    </html>
    """

    details = parse_listing_page_html(html)

    assert details.title == "Maison/villa 11 pièces COLLOBRIERES"
    assert details.municipality == "Collobrieres"
    assert details.room_count == 11
    assert details.living_area_m2 == Decimal("296")


def test_parse_listing_page_html_keeps_regular_thousands_surface() -> None:
    html = """
    <html>
      <body>
        Maison 7 pièces Trans-en-Provence
        7 pièces 300 m² 5 489 m²
      </body>
    </html>
    """

    details = parse_listing_page_html(html)

    assert details.living_area_m2 == Decimal("300")
    assert details.land_area_m2 == Decimal("5489")
