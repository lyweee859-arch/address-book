import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "xp-address-book-secret-key-2026")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(DATA_DIR, "address_book.db")
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size for Excel import
