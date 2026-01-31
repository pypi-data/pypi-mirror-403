# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Generic, TypeVar, Optional
from typing_extensions import override

from pydantic import Field as FieldInfo

from ._models import BaseModel
from ._base_client import BasePage, PageInfo, BaseSyncPage, BaseAsyncPage

__all__ = ["PageNumberPaginationMeta", "SyncPageNumberPagination", "AsyncPageNumberPagination"]

_T = TypeVar("_T")


class PageNumberPaginationMeta(BaseModel):
    request_id: Optional[str] = FieldInfo(alias="requestId", default=None)


class SyncPageNumberPagination(BaseSyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    page: Optional[int] = None
    per_page: Optional[int] = FieldInfo(alias="perPage", default=None)
    total: Optional[int] = None
    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    meta: Optional[PageNumberPaginationMeta] = None

    @override
    def _get_page_items(self) -> List[_T]:
        data = self.data
        if not data:
            return []
        return data

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        current_page = self.page
        if current_page is None:
            current_page = 1

        total_pages = self.total_pages
        if total_pages is not None and current_page >= total_pages:
            return None

        return PageInfo(params={"page": current_page + 1})


class AsyncPageNumberPagination(BaseAsyncPage[_T], BasePage[_T], Generic[_T]):
    data: List[_T]
    page: Optional[int] = None
    per_page: Optional[int] = FieldInfo(alias="perPage", default=None)
    total: Optional[int] = None
    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    meta: Optional[PageNumberPaginationMeta] = None

    @override
    def _get_page_items(self) -> List[_T]:
        data = self.data
        if not data:
            return []
        return data

    @override
    def next_page_info(self) -> Optional[PageInfo]:
        current_page = self.page
        if current_page is None:
            current_page = 1

        total_pages = self.total_pages
        if total_pages is not None and current_page >= total_pages:
            return None

        return PageInfo(params={"page": current_page + 1})
