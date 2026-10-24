import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
)
USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "false").lower()
SQLITE_FALLBACK_URL = f"sqlite:///{(BASE_DIR / 'taller_pro.db').as_posix()}"

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    ""
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

SPEERO_API_URL = os.getenv("SPEERO_API_URL", "https://speero.net/api/v1").rstrip("/")
SPEERO_API_KEY = os.getenv("SPEERO_API_KEY", "").strip()
