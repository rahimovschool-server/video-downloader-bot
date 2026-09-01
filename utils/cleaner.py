import os
import glob
import logging
from pathlib import Path

from config import DOWNLOAD_DIR

logger = logging.getLogger(__name__)


def clean_user_files(chat_id: int) -> int:
    """
    Foydalanuvchiga tegishli barcha vaqtinchalik fayllarni o'chirish.
    Returns: o'chirilgan fayllar soni
    """
    count = 0
    patterns = [
        os.path.join(DOWNLOAD_DIR, f"{chat_id}_*"),
        os.path.join(DOWNLOAD_DIR, f"{chat_id}_insta", "*"),
    ]

    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                p = Path(filepath)
                if p.is_file():
                    p.unlink()
                    count += 1
                elif p.is_dir():
                    import shutil
                    shutil.rmtree(filepath, ignore_errors=True)
                    count += 1
            except Exception as e:
                logger.warning(f"Faylni o'chirishda xato {filepath}: {e}")

    return count


def clean_all_old_files(max_age_hours: int = 1) -> int:
    """
    Eski fayllarni tozalash (1 soatdan eski).
    Returns: o'chirilgan fayllar soni
    """
    import time
    count = 0
    now = time.time()
    cutoff = now - max_age_hours * 3600

    try:
        for filepath in Path(DOWNLOAD_DIR).rglob("*"):
            if filepath.is_file():
                if filepath.stat().st_mtime < cutoff:
                    filepath.unlink()
                    count += 1
    except Exception as e:
        logger.warning(f"Eski fayllarni tozalashda xato: {e}")

    return count


def get_file_size_mb(filepath: str) -> float:
    """Fayl hajmini MB da qaytarish."""
    try:
        return Path(filepath).stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0
