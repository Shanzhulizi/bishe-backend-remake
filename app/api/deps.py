from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.repositories.user_repo import UserRepository


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


"""
它不是登录逻辑，也不会真的去调用 /api/auth/login。

它的真实作用只有两个：
    从请求头里“规范地”取出 Authorization: Bearer <token>
    告诉 FastAPI / OpenAPI：你的接口使用的是 OAuth2 Bearer Token 认证
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = await UserRepository.get_by_id(db, int(user_id))
    if not user:
        raise credentials_exception
    return user
