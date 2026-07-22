import json
from html import escape
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy.orm import Session

from app.application.map_service import MapService
from app.domain.map import ListingMapMarker


def render_var_map_page(session: Session) -> None:
    st.subheader("Carte du Var")
    listing_map = MapService(session).list_var_listing_markers()
    if not listing_map.markers:
        st.info("Aucune annonce localisable pour le moment.")
    else:
        components.html(_render_map_html(listing_map.markers), height=720, scrolling=False)

    if listing_map.unmapped:
        st.caption("Annonces non localisées")
        st.dataframe(
            [
                {
                    "ID": item.public_id,
                    "Titre": item.title,
                    "Commune": item.municipality,
                    "Raison": item.reason,
                }
                for item in listing_map.unmapped
            ],
            use_container_width=True,
            hide_index=True,
        )


def _render_map_html(markers: list[ListingMapMarker]) -> str:
    payload = json.dumps([_marker_payload(marker) for marker in markers])
    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIINfQFtoZ4hOKItLqrbFHT1v6b8E0iNgxk="
          crossorigin=""
        />
        <script
          src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
          integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
          crossorigin="">
        </script>
        <style>
          .leaflet-pane,
          .leaflet-tile,
          .leaflet-marker-icon,
          .leaflet-marker-shadow,
          .leaflet-tile-container,
          .leaflet-pane > svg,
          .leaflet-pane > canvas,
          .leaflet-zoom-box,
          .leaflet-image-layer,
          .leaflet-layer {{
            position: absolute;
            left: 0;
            top: 0;
          }}
          .leaflet-container {{
            overflow: hidden;
            outline-offset: 1px;
          }}
          .leaflet-tile,
          .leaflet-marker-icon,
          .leaflet-marker-shadow {{
            user-select: none;
            -webkit-user-drag: none;
          }}
          .leaflet-tile {{
            filter: inherit;
            visibility: hidden;
          }}
          .leaflet-tile-loaded {{
            visibility: inherit;
          }}
          .leaflet-zoom-animated {{
            transform-origin: 0 0;
          }}
          .leaflet-pane {{
            z-index: 400;
          }}
          .leaflet-tile-pane {{
            z-index: 200;
          }}
          .leaflet-overlay-pane {{
            z-index: 400;
          }}
          .leaflet-shadow-pane {{
            z-index: 500;
          }}
          .leaflet-marker-pane {{
            z-index: 600;
          }}
          .leaflet-tooltip-pane {{
            z-index: 650;
          }}
          .leaflet-popup-pane {{
            z-index: 700;
          }}
          .leaflet-control {{
            position: relative;
            z-index: 800;
            pointer-events: auto;
          }}
          .leaflet-top,
          .leaflet-bottom {{
            position: absolute;
            z-index: 1000;
            pointer-events: none;
          }}
          .leaflet-top {{
            top: 0;
          }}
          .leaflet-right {{
            right: 0;
          }}
          .leaflet-bottom {{
            bottom: 0;
          }}
          .leaflet-left {{
            left: 0;
          }}
          .leaflet-control-container .leaflet-top,
          .leaflet-control-container .leaflet-bottom {{
            pointer-events: none;
          }}
          .leaflet-control-container .leaflet-control {{
            pointer-events: auto;
          }}
          .leaflet-control-zoom a {{
            background: #ffffff;
            border-bottom: 1px solid #ccc;
            color: #111827;
            display: block;
            font: bold 18px Arial, Helvetica, sans-serif;
            height: 26px;
            line-height: 26px;
            text-align: center;
            text-decoration: none;
            width: 26px;
          }}
          .leaflet-control-attribution {{
            background: rgba(255, 255, 255, 0.82);
            font-size: 11px;
            padding: 0 5px;
          }}
          html, body, #map {{
            height: 700px;
            margin: 0;
            width: 100%;
          }}
          body {{
            font-family: Inter, Segoe UI, Arial, sans-serif;
          }}
          #map {{
            border: 1px solid #d0d7de;
            border-radius: 8px;
          }}
          .ann-label {{
            background: #ffffff;
            border: 1px solid #9fb0c3;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.18);
            color: #123047;
            font-size: 14px;
            font-weight: 750;
            line-height: 1;
            padding: 6px 8px;
            white-space: nowrap;
          }}
          .ann-label a {{
            color: #123047;
            text-decoration: underline;
          }}
          .popup-title {{
            color: #102a43;
            font-weight: 750;
            margin-bottom: 4px;
          }}
          .popup-city {{
            color: #52616b;
            margin-bottom: 8px;
          }}
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          const markers = {payload};
          const map = L.map("map", {{
            scrollWheelZoom: true,
          }}).setView([43.35, 6.25], 9);

          L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
            maxZoom: 19,
            attribution:
              '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          }}).addTo(map);

          const bounds = [];
          markers.forEach((marker) => {{
            const position = [marker.latitude, marker.longitude];
            bounds.push(position);

            const icon = L.divIcon({{
              className: "",
              html: `<div class="ann-label"><a href="${{marker.sourceUrl}}"
                       target="_blank" rel="noopener noreferrer">${{marker.publicId}}</a></div>`,
              iconAnchor: [10, 10],
            }});

            L.marker(position, {{ icon }})
              .addTo(map)
              .bindPopup(`
                <div class="popup-title">${{marker.title}}</div>
                <div class="popup-city">${{marker.municipality}}</div>
                <a href="${{marker.sourceUrl}}" target="_blank" rel="noopener noreferrer">
                  Ouvrir ${{marker.publicId}}
                </a>
              `);
          }});

          if (bounds.length === 1) {{
            map.setView(bounds[0], 12);
          }} else if (bounds.length > 1) {{
            map.fitBounds(bounds, {{ padding: [40, 40], maxZoom: 12 }});
          }}
          window.setTimeout(() => map.invalidateSize(), 100);
          window.setTimeout(() => map.invalidateSize(), 500);
        </script>
      </body>
    </html>
    """


def _marker_payload(marker: ListingMapMarker) -> dict[str, Any]:
    return {
        "publicId": escape(marker.public_id),
        "title": escape(marker.title),
        "sourceUrl": escape(marker.source_url, quote=True),
        "municipality": escape(marker.municipality),
        "latitude": marker.latitude,
        "longitude": marker.longitude,
    }
