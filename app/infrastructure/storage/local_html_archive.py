from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path

from app.infrastructure.db.repositories.listing_html_archives import HtmlAssetInput


class LocalHtmlArchiveError(ValueError):
    pass


@dataclass(frozen=True)
class LocalHtmlArchive:
    html: str
    original_filename: str
    assets: tuple[HtmlAssetInput, ...]
    asset_directory: Path | None


def load_local_html_archive(html_path: Path) -> LocalHtmlArchive:
    resolved_path = html_path.expanduser().resolve()
    if not resolved_path.exists():
        raise LocalHtmlArchiveError("Le fichier HTML est introuvable.")
    if not resolved_path.is_file():
        raise LocalHtmlArchiveError("Le chemin indiqué ne pointe pas vers un fichier.")
    if resolved_path.suffix.lower() not in {".html", ".htm"}:
        raise LocalHtmlArchiveError("Le fichier principal doit être un HTML.")

    html = resolved_path.read_bytes().decode("utf-8", errors="replace")
    asset_directory = _find_browser_asset_directory(resolved_path)
    assets = _load_assets(asset_directory, resolved_path.parent) if asset_directory else ()
    return LocalHtmlArchive(
        html=html,
        original_filename=resolved_path.name,
        assets=assets,
        asset_directory=asset_directory,
    )


def _find_browser_asset_directory(html_path: Path) -> Path | None:
    candidates = (
        html_path.with_name(f"{html_path.stem}_files"),
        html_path.with_name(f"{html_path.stem}_fichiers"),
        html_path.with_name(f"{html_path.stem}.files"),
        html_path.with_name(html_path.stem),
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _load_assets(asset_directory: Path, base_directory: Path) -> tuple[HtmlAssetInput, ...]:
    assets: list[HtmlAssetInput] = []
    for path in sorted(asset_directory.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(base_directory).as_posix()
        assets.append(
            HtmlAssetInput(
                relative_path=relative_path,
                content_bytes=path.read_bytes(),
                content_type=guess_type(path.name)[0] or "application/octet-stream",
            )
        )
    return tuple(assets)
