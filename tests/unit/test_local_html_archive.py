from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from app.infrastructure.storage.local_html_archive import load_local_html_archive


def test_load_local_html_archive_imports_chrome_associated_directory() -> None:
    base_path = Path("tests/_tmp_manual") / uuid4().hex
    try:
        base_path.mkdir(parents=True)
        html_path = base_path / "annonce.html"
        asset_dir = base_path / "annonce_fichiers"
        image_dir = asset_dir / "images"
        image_dir.mkdir(parents=True)
        html_path.write_text(
            '<html><body><img src="annonce_fichiers/images/photo.jpg"></body></html>',
            encoding="utf-8",
        )
        (image_dir / "photo.jpg").write_bytes(b"photo")

        archive = load_local_html_archive(html_path)
    finally:
        rmtree(base_path, ignore_errors=True)

    assert archive.original_filename == "annonce.html"
    assert archive.asset_directory == asset_dir.resolve()
    assert archive.html.startswith("<html>")
    assert len(archive.assets) == 1
    assert archive.assets[0].relative_path == "annonce_fichiers/images/photo.jpg"
    assert archive.assets[0].content_bytes == b"photo"
    assert archive.assets[0].content_type == "image/jpeg"
