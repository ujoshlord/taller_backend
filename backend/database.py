import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATABASE_URL, USE_SQLITE_FALLBACK, SQLITE_FALLBACK_URL

logger = logging.getLogger("taller_pro.db")

Base = declarative_base()

IS_POSTGRES = False
ACTIVE_DATABASE_URL = DATABASE_URL


def _build_engine():
    global IS_POSTGRES, ACTIVE_DATABASE_URL
    try:
        pg_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 10} if "postgresql" in DATABASE_URL else {},
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        IS_POSTGRES = "postgresql" in DATABASE_URL
        ACTIVE_DATABASE_URL = DATABASE_URL
        logger.info("Conectado exitosamente a PostgreSQL: %s", DATABASE_URL)
        return pg_engine
    except Exception as exc:
        if USE_SQLITE_FALLBACK:
            logger.warning(
                "PostgreSQL no disponible (%s). Usando base de datos local SQLite de respaldo: %s",
                exc,
                SQLITE_FALLBACK_URL,
            )
            IS_POSTGRES = False
            ACTIVE_DATABASE_URL = SQLITE_FALLBACK_URL
            return create_engine(
                SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
            )
        raise


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
