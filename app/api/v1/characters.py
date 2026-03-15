import os
import shutil
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import get_logger
from app.schemas.character import CharacterCreate, CharacterDetailResponse

from app.schemas.common import ResponseModel
from app.services.character_service import CharacterService

# router = APIRouter()
# service = CharacterService(CharacterRepository())

logger = get_logger(__name__)

from app.core.config import settings
# 确保头像目录存在
AVATAR_DIR = settings. AVATAR_IMAGES_DIR
AVATAR_DIR.mkdir(parents=True, exist_ok=True)




# @router.post("/create", response_model=CharacterDetailResponse)
# def create_character(
#         name: str = Form(...),
#         description: str = Form(None),
#         worldview: str = Form(None),
#         tags: str = Form(""),
#         avatar: UploadFile = File(None),
#         db: Session = Depends(get_db),
#
#         voice_code: str = Form(None),  # 新增
#         voice_id: str = Form(None)
# ):
#
#     logger.info(f"创建角色请求: name={name}, description={description}, worldview={worldview}, tags={tags}, avatar_filename={avatar.filename if avatar else 'None'}, voice_code={voice_code}, voice_id={voice_id}")
#
#     avatar_url = None
#     logger.info("test")
#     if avatar:
#         ext = avatar.filename.split(".")[-1]
#         filename = f"{uuid.uuid4()}.{ext}"
#         file_path = AVATAR_DIR / filename
#
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(avatar.file, buffer)
#
#         avatar_url = f"http://localhost:8000/static/avatars/{filename}"
#
#     logger.info("test")
#     tag_list = tags.split(",") if tags else []
#
#     data = CharacterCreate(
#         name=name,
#         avatar=avatar_url,
#         description=description,
#         worldview=worldview,
#         tags=tag_list,
#         voice_code=voice_code,
#         voice_id= voice_id
#     )
#
#     char = service.create_character(db, data)
#
#     return {
#         "id": char.id,
#         "name": char.name,
#         "avatar": char.avatar,
#         "description": char.description,
#         "worldview": char.worldview,
#         "is_active": True,
#         "persona": char.config.persona if char.config else {},
#         "voice_id":char.voice_id
#     }
#
#
# @router.get("/list")
# def list_characters(db: Session = Depends(get_db)):
#     """
#     获取所有角色的基本信息
#     """
#     chars = service.get_all_characters_basic(db)
#     logger.info(f"获取所有角色基本信息成功，数量：{len(chars)}")
#     # 返回统一格式
#     return ResponseModel.success(
#         data=[dict(id=c.id, name=c.name, avatar=c.avatar, description=c.description, like_count=c.like_count) for c in
#               chars])
#
#
# """
# /api/characters/list 被 误匹配到了 /api/characters/{id} 这个接口上
# 所以，id这个接口放到了最后
# """
#
#
# @router.get("/{character_id}", response_model=CharacterResponse)
# def get_character_by_id(character_id: int, db: Session = Depends(get_db)):
#     logger.info(f"获取角色基本信息{character_id}")
#     char = service.get_character_by_id(db, character_id)
#     logger.info(f"获取角色基本信息成功：{char.id} - {char.name}")
#     if not char:
#         return None
#     return {
#         "id": char.id,
#         "name": char.name,
#         "avatar": char.avatar,
#         "description": char.description,
#         "voice_id": char.voice_id,
#     }


# app/api/character.py
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.services.character_service import CharacterService
from app.schemas.character import (
    CharacterCreate, CharacterUpdate,
    CharacterDetailResponse, CharacterListItem
)

router = APIRouter()


@router.get("/", response_model=ResponseModel[List[CharacterListItem]])
def get_characters(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        category_id: Optional[int] = Query(None),
        tag_id: Optional[int] = Query(None),
        keyword: Optional[str] = Query(None),
        is_official: Optional[bool] = Query(None),
        db: Session = Depends(get_db)
):
    """获取角色列表（支持筛选和搜索）"""
    service = CharacterService(db)
    characters, total = service.get_characters(
        skip=skip,
        limit=limit,
        category_id=category_id,
        tag_id=tag_id,
        keyword=keyword,
        is_official=is_official
    )

    # 添加总数字段到响应头
    from fastapi.responses import JSONResponse
    response = JSONResponse(content=[c.__dict__ for c in characters])
    response.headers["X-Total-Count"] = str(total)
    return ResponseModel.success(data=characters)


@router.get("/{character_id}", response_model=ResponseModel[CharacterDetailResponse])
def get_character(
        character_id: int,
        db: Session = Depends(get_db)
):
    """获取角色详情"""
    service = CharacterService(db)
    character = service.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ResponseModel.success(data= character)


@router.post("/", response_model=ResponseModel[CharacterDetailResponse])
async def create_character(
        name: str = Form(..., min_length=1, max_length=50),
        description: Optional[str] = Form(None),
        worldview: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None),
        voice_id: Optional[str] = Form(None),
        greeting: Optional[str] = Form(None),
        category_ids: str = Form("[]"),  # JSON string
        tag_ids: str = Form("[]"),  # JSON string
        is_official: bool = Form(False),
        db: Session = Depends(get_db)
):
    """创建新角色"""
    # 处理头像上传
    avatar_url = None
    # if avatar:
    #     # 保存头像文件
    #     file_ext = os.path.splitext(avatar.filename)[1]
    #     file_name = f"{uuid.uuid4().hex}{file_ext}"
    #     upload_dir = Path("static/avatars")
    #     upload_dir.mkdir(parents=True, exist_ok=True)
    #
    #     file_path = upload_dir / file_name
    #     with open(file_path, "wb") as buffer:
    #         shutil.copyfileobj(avatar.file, buffer)
    #
    #     avatar_url = f"/static/avatars/{file_name}"

    if avatar:
        ext = avatar.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = AVATAR_DIR / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)

        avatar_url = f"http://localhost:8000/static/avatars/{filename}"
    #

    # 解析JSON数组
    try:
        cat_ids = json.loads(category_ids)
        tag_ids_list = json.loads(tag_ids)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="category_ids 或 tag_ids 格式错误")

    data = CharacterCreate(
        name=name,
        description=description,
        worldview=worldview,
        avatar=avatar_url,
        voice_id=voice_id,
        greeting=greeting,
        category_ids=cat_ids,
        tag_ids=tag_ids_list,
        is_official=is_official
    )

    service = CharacterService(db)
    char= service.create_character(data)
    return ResponseModel.success(data = char)

import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, File, Form, HTTPException
from typing import Optional


@router.put("/{character_id}", response_model=ResponseModel[CharacterDetailResponse])
async def update_character(
        character_id: int,
        name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        worldview: Optional[str] = Form(None),
        avatar: Optional[str] = Form(None),
        voice_id: Optional[str] = Form(None),
        greeting: Optional[str] = Form(None),
        category_ids: Optional[str] = Form(None),
        tag_ids: Optional[str] = Form(None),
        is_official: Optional[bool] = Form(None),
        is_active: Optional[bool] = Form(None),
        db: Session = Depends(get_db)
):
    """更新角色"""

    data_dict = {}
    if name is not None:
        data_dict["name"] = name
    if description is not None:
        data_dict["description"] = description
    if worldview is not None:
        data_dict["worldview"] = worldview
    if avatar is not None:
        data_dict["avatar"] = avatar
    if voice_id is not None:
        data_dict["voice_id"] = voice_id
    if greeting is not None:
        data_dict["greeting"] = greeting
    if is_official is not None:
        data_dict["is_official"] = is_official
    if is_active is not None:
        data_dict["is_active"] = is_active

    # 解析JSON数组
    if category_ids is not None:
        try:
            data_dict["category_ids"] = json.loads(category_ids)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="category_ids 格式错误")

    if tag_ids is not None:
        try:
            data_dict["tag_ids"] = json.loads(tag_ids)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="tag_ids 格式错误")

    data = CharacterUpdate(**data_dict)

    service = CharacterService(db)
    char = service.update_character(character_id, data)
    return ResponseModel.success(data=char)

@router.delete("/{character_id}")
def delete_character(
        character_id: int,
        db: Session = Depends(get_db)
):
    """删除角色（软删除）"""
    service = CharacterService(db)
    service.delete_character(character_id)
    return ResponseModel.success(msg="角色已删除")


# @router.post("/{character_id}/popularity")
# def update_popularity(
#         character_id: int,
#         db: Session = Depends(get_db)
# ):
#     """更新角色热度分数"""
#     service = CharacterService(db)
#     service.update_popularity_score(character_id)
#     return {"message": "热度更新成功"}