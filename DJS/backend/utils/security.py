"""
보안 유틸리티: 비밀번호 해싱/검증, JWT 생성/검증
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext


# 비밀번호 해싱 컨텍스트 (bcrypt)
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


# JWT 설정 (기본값, 추후 DB 설정에서 불러오거나 환경 변수에서 주입 가능)
DEFAULT_JWT_SECRET = "CHANGE_ME_DEV_SECRET"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간


def create_access_token(
    data: Dict[str, Any],
    secret_key: str = DEFAULT_JWT_SECRET,
    algorithm: str = DEFAULT_JWT_ALGORITHM,
    expires_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_token(
    token: str,
    secret_key: str = DEFAULT_JWT_SECRET,
    algorithms: list[str] | None = None,
) -> Optional[Dict[str, Any]]:
    if algorithms is None:
        algorithms = [DEFAULT_JWT_ALGORITHM]
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except JWTError:
        return None
