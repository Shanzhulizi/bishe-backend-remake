# app/api/deps.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password_async, \
    verify_password_async
from app.exceptions import BizException
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = get_logger(__name__)

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_user(self, user_in) -> User:
        # 1. 检查用户名是否已存在


        result =await self.user_repo.get_by_username(user_in.username)

        if result.scalar_one_or_none():
            logger.warning(f"用户{user_in.username}已存在")
            raise ValueError("Username already exists")

        # 2. 查重（email）
        if user_in.email:
            result =await self.db.execute(
                select(User).where(User.email == user_in.email)
            )
            if result.scalar_one_or_none():
                logger.warning(f"邮箱{user_in.email}已注册")
                raise ValueError("邮箱已存在")

        logger.info(f"准备创建用户: {user_in.username}")
        # 2. 构造用户对象
        user = User(
            username=user_in.username,
            email=user_in.email,
            # password_hash=get_hash_password(user_in.password)
            password_hash=await hash_password_async(user_in.password)
        )

        self.db.add(user)
        # 3. 添加到数据库
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception:
            await self.db.rollback()
            raise

        logger.info(f"用户注册完成")
        return user


    async def user_login(self, username: str, password: str) -> str:
        user =await self.user_repo.get_by_username( username)
        logger.info(f"用户登录服务 {user.username}")
        if not user:
            logger.warning(f"用户{username}不存在")
            raise BizException(ResponseCode.USER_NOT_FOUND)
        # if not verify_password(password, user.password_hash):
        if not await verify_password_async(password, user.password_hash):
            logger.warning(f"用户{username}密码错误")
            raise BizException(ResponseCode.PASSWORD_ERROR)
        if not user.is_active:
            logger.warning(f"用户{username}已停用")
            raise BizException(ResponseCode.USER_DISABLED)

        return create_access_token(str(user.id))
