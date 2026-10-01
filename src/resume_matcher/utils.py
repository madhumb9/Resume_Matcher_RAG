from pathlib import Path
import hashlib


def create_resume_id(file_path: str | Path) -> str:
    """
    Create a unique ID from the PDF file content.
    """

    path = Path(file_path)

    file_bytes = path.read_bytes()

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


def get_filename(file_path: str | Path) -> str:
    """
    Return only the filename.
    """

    return Path(file_path).name