import re
import webbrowser
from pathlib import Path


class BrowserPreviewError(RuntimeError):
    pass


def open_html_preview(html: str, public_id: str, *, preview_dir: Path) -> Path:
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{_safe_filename(public_id)}.html"
    preview_path.write_text(html, encoding="utf-8")
    opened = webbrowser.open(preview_path.resolve().as_uri(), new=2)
    if not opened:
        raise BrowserPreviewError("Le navigateur n'a pas pu être ouvert automatiquement.")
    return preview_path


def _safe_filename(value: str) -> str:
    safe_value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return safe_value or "annonce"
