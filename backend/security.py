from datetime import datetime, timedelta, timezone
from typing import List
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from backend.database import get_db
from backend.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: int, alias: str, rol_nombre: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "alias": alias,
        "rol": rol_nombre,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación no proporcionado.",
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Inicia sesión nuevamente.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )

    if user.token and user.token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ya no es activo. Inicia sesión nuevamente.",
        )

    if user.estado and user.estado.nombre.lower() != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario se encuentra inactiva.",
        )

    return user


def require_roles(*allowed_roles: str):
    normalized_allowed = {r.lower() for r in allowed_roles}

    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        user_role = (current_user.rol.nombre if current_user.rol else "").lower()
        if user_role == "administrador" or user_role in normalized_allowed:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso restringido. Tu rol ({current_user.rol.nombre}) no tiene permisos para este módulo.",
        )

    return role_checker
