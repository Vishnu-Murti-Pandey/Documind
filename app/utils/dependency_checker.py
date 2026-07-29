"""
Validate external tools required by the application.
"""

from pathlib import Path
import shutil
import os


def check_tesseract() -> str:
    """
    Locate the Tesseract executable.

    Priority:
    1. TESSERACT_PATH in .env
    2. System PATH

    Returns:
        Absolute path to tesseract.exe

    Raises:
        FileNotFoundError if Tesseract cannot be located.
    """

    # Try .env first
    env_path = os.getenv("TESSERACT_PATH")

    if env_path:
        path = Path(env_path)

        if path.exists():
            return str(path)

    # Try system PATH
    system_path = shutil.which("tesseract")

    if system_path:
        return system_path

    raise FileNotFoundError(
        "Tesseract not found.\n"
        "Either add it to PATH or set TESSERACT_PATH in .env"
    )