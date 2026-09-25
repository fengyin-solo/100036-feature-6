"""运营概览下钻接口：给出单个模块的待处理分布与近七天趋势。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.drilldown import drilldown_service

router = APIRouter(prefix="/api/overview", tags=["运营概览"])


@router.get("/modules/{module}/pending-breakdown")
def pending_breakdown(module: str) -> dict[str, Any]:
    """待处理条目分布（状态 × 负责班组）与近七天趋势。

    条目口径直接复用模块页列表的 list_entries，保证下钻数字与模块页面一致；
    模块没有待处理数据时返回空分布，由前端展示空态说明。
    """
    return drilldown_service.pending_breakdown(module)
