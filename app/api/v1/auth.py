from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_async_db
from app.core.constants import ResponseCode
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.user import *
from app.services.user_service import UserService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=ResponseModel[UserOut])
async def register(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_async_db),
):
    logger.info(f"注册用户: {user_in.username}")
    user_service = UserService(db)
    try:
        user = await user_service.create_user( user_in)
        logger.info(f"用户注册成功,用户id: {user.id}")
        return ResponseModel.success(
            msg="注册成功",
            data=user,
        )
    except ValueError as e:

        return ResponseModel.error(
            code=ResponseCode.USER_ALREADY_EXISTS,
            msg="注册失败，" + str(e) + ""
        )


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(
        user_in: LoginRequest,
        db: AsyncSession = Depends(get_async_db),
):
    logger.info(f"用户登录: {user_in.username}")
    user_service = UserService(db)
    try:
        token =await user_service.user_login( user_in.username, user_in.password)
        logger.info(f"登录成功: {token}")
        return ResponseModel.success(
            msg="登录成功",
            data=LoginResponse(
                access_token=token
            )
        )
    except Exception as e:
        logger.info(f"登录失败" + str(e))
        return ResponseModel.error(
            code=ResponseCode.USER_NOT_FOUND,
            msg="登录失败，" + str(e) + ""
        )


@router.get("/me", response_model=ResponseModel[UserDetail])
async def me(
        current_user: User = Depends(get_current_user)
):
    return ResponseModel.success(
        msg="查询成功",
        data=current_user
    )
