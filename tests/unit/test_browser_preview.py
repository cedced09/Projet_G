from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.infrastructure.storage import browser_preview
from app.infrastructure.storage.browser_preview import open_html_preview


def test_open_html_preview_writes_file_and_opens_browser(monkeypatch) -> None:
    base_path = Path("tests/_tmp_manual") / uuid4().hex
    opened_urls: list[str] = []
    monkeypatch.setattr(
        browser_preview.webbrowser,
        "open",
        lambda url, new=0: opened_urls.append(url) or True,
    )

    try:
        preview_path = open_html_preview(
            "<html><body>Annonce sauvegardée</body></html>",
            "ANN-0001",
            preview_dir=base_path,
        )
        preview_content = preview_path.read_text(encoding="utf-8")
    finally:
        rmtree(base_path, ignore_errors=True)

    assert preview_path.name == "ANN-0001.html"
    assert preview_content == "<html><body>Annonce sauvegardée</body></html>"
    assert opened_urls == [preview_path.resolve().as_uri()]
