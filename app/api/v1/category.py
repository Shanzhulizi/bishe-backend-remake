# app/api/category.py
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import ResponseModel
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/", response_model=ResponseModel[List[CategoryResponse]])
async def get_categories(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
        db: AsyncSession = Depends(get_async_db)
):
    """获取所有类别"""
    service = CategoryService(db)
    categories =await service.get_categories(skip=skip, limit=limit)
    return ResponseModel.success(data=categories)
    # return categories


@router.get("/{category_id}", response_model=ResponseModel[CategoryResponse])
async def get_category(
        category_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """获取单个类别"""
    service = CategoryService(db)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="类别不存在")

    return ResponseModel.success(data=category)
    # return category


@router.post("/", response_model=ResponseModel[CategoryResponse], status_code=201)
async def create_category(
        data: CategoryCreate,
        db: AsyncSession = Depends(get_async_db)
):
    """创建新类别"""
    service = CategoryService(db)
    category = await service.create_category(data)
    return ResponseModel.success(data=category)


@router.put("/{category_id}", response_model=ResponseModel[CategoryResponse])
async def update_category(
        category_id: int,
        data: CategoryUpdate,
        db: AsyncSession = Depends(get_async_db)
):
    """更新类别"""
    service = CategoryService(db)
    updated_category = await service.update_category(category_id, data)
    return ResponseModel.success(data=updated_category)


@router.delete("/{category_id}", response_model=ResponseModel)
async def delete_category(
        category_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """删除类别"""
    service = CategoryService(db)
    await service.delete_category(category_id)
    return ResponseModel.success(msg="删除成功")
