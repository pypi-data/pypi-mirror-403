from importlib.resources import files
from pathlib import Path
import json

# Base resources directory
BASE_RESOURCES = files("DjPractLelo") / "resources"


def get_resource(category: str, filename: str) -> Path:
    """
    Get any resource file from a category.
    category: 'data_science' or 'soft_computing'
    filename: exact filename
    """
    return BASE_RESOURCES / category / filename


def list_files(category: str, extension: str | None = None) -> list[Path]:
    """
    List files in a category.
    extension: '.csv', '.json', '.py', '.R', '.mp3', '.mp4', '.xml' etc. (None = all files)
    """
    directory = BASE_RESOURCES / category
    if extension:
        return [p for p in directory.iterdir() if p.suffix == extension]
    return [p for p in directory.iterdir() if p.is_file()]


def load_json(filename: str, category: str = "data_science") -> dict:
    """
    Load any JSON file from resources.
    """
    path = get_resource(category, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_manual(category: str) -> Path:
    """
    Get manual.docx from any category.
    """
    return get_resource(category, "manual.docx")
