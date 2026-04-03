# app/api/tag.py
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.schemas.common import ResponseModel
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.services.tag_service import TagService

router = APIRouter()


@router.get("/", response_model=ResponseModel[List[TagResponse]])
async def get_tags(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: AsyncSession = Depends(get_async_db)
):
    """获取所有标签"""
    service = TagService(db)
    tags = await service.get_tags(skip=skip, limit=limit)
    return ResponseModel.success(data=tags)


@router.get("/search", response_model=ResponseModel[List[TagResponse]])
async def search_tags(
        keyword: str = Query(..., min_length=1),
        db: AsyncSession = Depends(get_async_db)
):
    """搜索标签"""
    service = TagService(db)
    tags = await service.search_tags(keyword)
    return ResponseModel.success(data=tags)


@router.get("/{tag_id}", response_model=ResponseModel[TagResponse])
async def get_tag(
        tag_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """获取单个标签"""
    service = TagService(db)
    tag = await service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    return ResponseModel.success(data=tag)


@router.post("/", response_model=ResponseModel[TagResponse])
async def create_tag(
        data: TagCreate,
        db: AsyncSession = Depends(get_async_db)
):
    """创建新标签"""
    service = TagService(db)
    tag = await service.create_tag(data)
    return ResponseModel.success(data=tag)


@router.put("/{tag_id}", response_model=ResponseModel[TagResponse])
async def update_tag(
        tag_id: int,
        data: TagUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    """更新标签"""
    service = TagService(db)
    tag = await service.update_tag(tag_id, data)
    return ResponseModel.success(data=tag)


@router.delete("/{tag_id}", response_model=ResponseModel)
async def delete_tag(
        tag_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """删除标签"""
    service = TagService(db)
    await service.delete_tag(tag_id)
    return ResponseModel.success(msg="删除成功")
