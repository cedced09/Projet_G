from pathlib import Path
from tkinter import TclError, Tk, filedialog


class LocalFileDialogError(RuntimeError):
    pass


def select_html_file(import_directories: str) -> Path | None:
    initial_directory = _first_existing_directory(import_directories)
    try:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            parent=root,
            initialdir=str(initial_directory) if initial_directory is not None else None,
            title="Sélectionner le fichier HTML de l'annonce",
            filetypes=(
                ("Fichiers HTML", "*.html *.htm"),
                ("Tous les fichiers", "*.*"),
            ),
        )
        root.destroy()
    except TclError as exc:
        raise LocalFileDialogError(
            "La boîte de sélection de fichier n'est pas disponible sur cette machine."
        ) from exc
    if selected == "":
        return None
    return Path(selected)


def _first_existing_directory(import_directories: str) -> Path | None:
    for item in import_directories.split(","):
        clean_value = item.strip().strip('"')
        if clean_value == "":
            continue
        path = Path(clean_value).expanduser()
        if path.is_dir():
            return path
    return None
