import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

_raw_db_url = os.getenv("DATABASE_URL", "").strip()
if _raw_db_url.startswith("postgres://"):
    DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _raw_db_url.startswith("postgresql://"):
    DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    DATABASE_URL = _raw_db_url

USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "false").lower() in ("true", "1", "yes")
SQLITE_FALLBACK_URL = f"sqlite:///{(BASE_DIR / 'taller_pro.db').as_posix()}"

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "taller_pro_linear_secret_key_2026_x99a8b7c6d5e4f3"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

SPEERO_API_URL = os.getenv("SPEERO_API_URL", "https://speero.net/api/v1/search").rstrip("/")
if SPEERO_API_URL.endswith("/api/v1"):
    SPEERO_API_URL = f"{SPEERO_API_URL}/search"
SPEERO_API_KEY = os.getenv("SPEERO_API_KEY", "").strip()
