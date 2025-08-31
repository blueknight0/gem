"""
인증 API 라우터: 회원가입, 로그인(JWT), 내 정보 조회
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from backend.core.database import get_db
import os
from backend.models.models import User, SystemConfig
from backend.models.schemas import UserCreate, User as UserSchema, Token
from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    DEFAULT_JWT_SECRET,
    DEFAULT_JWT_ALGORITHM,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_jwt_settings(db: Session) -> tuple[str, str, int]:
    """ENV > SystemConfig > 기본값 순으로 JWT 설정을 반환"""
    try:
        # 1) ENV 우선
        env_secret = os.getenv("JWT_SECRET")
        env_alg = os.getenv("JWT_ALGORITHM")
        env_exp = os.getenv("JWT_EXPIRE_MINUTES")
        if env_secret or env_alg or env_exp:
            secret_val = env_secret or DEFAULT_JWT_SECRET
            alg_val = env_alg or DEFAULT_JWT_ALGORITHM
            try:
                exp_val = (
                    int(env_exp) if env_exp else DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
                )
            except Exception:
                exp_val = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
            return secret_val, alg_val, exp_val

        # 2) DB 설정
        secret = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == "jwt_secret")
            .first()
        )
        alg = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == "jwt_algorithm")
            .first()
        )
        exp = (
            db.query(SystemConfig)
            .filter(SystemConfig.config_key == "jwt_expire_minutes")
            .first()
        )
        secret_val = (
            secret.config_value
            if secret and secret.config_value
            else DEFAULT_JWT_SECRET
        )
        alg_val = (
            alg.config_value if alg and alg.config_value else DEFAULT_JWT_ALGORITHM
        )
        try:
            exp_val = (
                int(exp.config_value)
                if exp and exp.config_value
                else DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        except Exception:
            exp_val = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        return secret_val, alg_val, exp_val
    except Exception:
        return (
            DEFAULT_JWT_SECRET,
            DEFAULT_JWT_ALGORITHM,
            DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    secret, algorithm, _ = get_jwt_settings(db)
    payload = decode_token(token, secret_key=secret, algorithms=[algorithm])
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 유효하지 않거나 만료되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰"
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )
    return user


@router.post("/register", response_model=UserSchema)
def register_disabled(_: UserCreate, db: Session = Depends(get_db)):
    """회원가입 비활성화: 비공개 시스템 정책"""
    raise HTTPException(status_code=403, detail="회원가입이 비활성화되었습니다.")


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400, detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    secret, algorithm, expires = get_jwt_settings(db)
    access_token = create_access_token(
        data={"sub": user.email},
        secret_key=secret,
        algorithm=algorithm,
        expires_minutes=expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/protected")
def protected_example(current_user: User = Depends(get_current_user)):
    return {"message": "접근 허용", "email": current_user.email}
