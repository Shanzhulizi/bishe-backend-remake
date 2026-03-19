# schemas/pagination.py
from typing import Generic, TypeVar, List

from pydantic import BaseModel
from pydantic.generics import GenericModel

# 泛型类型变量
T = TypeVar('T')


class PageParams(BaseModel):
    """分页请求参数"""
    page: int = 1  # 当前页码，默认第1页
    page_size: int = 20  # 每页条数，默认20条

    @property
    def offset(self) -> int:
        """计算SQL偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取每页限制数"""
        return self.page_size


class Pagination(BaseModel):
    """分页信息"""
    page: int  # 当前页码
    page_size: int  # 每页条数
    total: int  # 总记录数
    pages: int  # 总页数

    @classmethod
    def create(cls, page: int, page_size: int, total: int):
        """创建分页信息"""
        pages = (total + page_size - 1) // page_size
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            pages=pages
        )


class PageResponse(GenericModel, Generic[T]):
    """通用分页响应模板"""
    code: int = 200
    message: str = "success"
    data: List[T]  # 数据列表
    pagination: Pagination  # 分页信息

    class Config:
        arbitrary_types_allowed = True