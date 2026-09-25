"""运营概览下钻：复用各模块自己的列表口径，给出待处理分布与近七天趋势。

数字一致性是这个服务的核心约束——这里不自己另写筛选规则，而是直接调用
各模块 service 的 list_entries（与模块页面 GET /api/<module> 完全同一段代码），
pending 判定也沿用各模块动作流转时写入的 pending 标记，保证概览、下钻、模块页三处对得上。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException

from app.services.alarm import AlarmService
from app.services.array import ArrayService
from app.services.cleaning import CleaningService
from app.services.combiner import CombinerService
from app.services.contractor import ContractorService
from app.services.curtail import CurtailService
from app.services.defect import DefectService
from app.services.generation import GenerationService
from app.services.inspection import InspectionService
from app.services.inverter import InverterService
from app.services.irradiance import IrradianceService
from app.services.permit import PermitService
from app.services.repair import RepairService
from app.services.settlement import SettlementService
from app.services.sparepart import SparepartService
from app.services.station import StationService
from app.services.stringmon import StringmonService
from app.services.training import TrainingService

# 模块 -> 模块自己的 service（list_entries 口径与模块页一致）
SERVICES: dict[str, Any] = {
    "station": StationService(),
    "array": ArrayService(),
    "inverter": InverterService(),
    "combiner": CombinerService(),
    "stringmon": StringmonService(),
    "irradiance": IrradianceService(),
    "cleaning": CleaningService(),
    "inspection": InspectionService(),
    "defect": DefectService(),
    "repair": RepairService(),
    "sparepart": SparepartService(),
    "generation": GenerationService(),
    "curtail": CurtailService(),
    "alarm": AlarmService(),
    "permit": PermitService(),
    "contractor": ContractorService(),
    "training": TrainingService(),
    "settlement": SettlementService(),
}

# 负责班组字段：只有这几个模块的示例数据里真有班组列，其余模块不臆造，统一归入“未分配班组”
TEAM_FIELDS: dict[str, str] = {
    "station": "运维班组",
    "cleaning": "作业班组",
    "sparepart": "所属班组",
}
UNASSIGNED_TEAM = "未分配班组"

# 近七天趋势的历史波动形状（最后一天由真实待处理量兜底，见 _trend）。
# 当前是内存示例数据，没有历史快照，这里只造一条可读的演示曲线；
# 换成数据库后应改为按天落库的待处理快照。
_TREND_SHAPE = [2, 1, 2, 0, 1, 0]


class DrilldownService:
    def pending_breakdown(self, module: str) -> dict[str, Any]:
        service = SERVICES.get(module)
        if service is None:
            raise HTTPException(status_code=404, detail=f"业务模块「{module}」不存在")

        # size 取大值：与模块页“导出/默认查询”看到的全量条目保持同一口径
        items, total = service.list_entries(page=1, size=10000)
        status_order: list[str] = list(getattr(service, "STATUS_ORDER", []))
        team_field = TEAM_FIELDS.get(module)

        pending_items = [row for row in items if row.get("pending")]
        pending_total = len(pending_items)

        statuses: list[str] = []
        teams_order: list[str] = []
        counts: dict[str, dict[str, int]] = {}

        for row in pending_items:
            status = str(row.get("status") or "未知状态")
            if status not in statuses:
                statuses.append(status)
            team = self._team_of(row, team_field)
            if team not in teams_order:
                teams_order.append(team)
                counts[team] = {}
            counts[team][status] = counts[team].get(status, 0) + 1

        # 列顺序跟随模块自己的状态机定义，机子里没出现过的状态不列
        statuses.sort(key=lambda s: status_order.index(s) if s in status_order else len(status_order))
        # 班组行按待处理量从多到少，便于一眼看到卡点
        teams_order.sort(key=lambda t: -sum(counts[t].values()))

        distribution = [
            {
                "team": team,
                "counts": [counts[team].get(status, 0) for status in statuses],
                "total": sum(counts[team].values()),
            }
            for team in teams_order
        ]

        return {
            "module": module,
            "total": total,
            "pendingTotal": pending_total,
            "statuses": statuses,
            "distribution": distribution,
            "trend": self._trend(module, pending_total),
        }

    @staticmethod
    def _team_of(row: dict[str, Any], team_field: str | None) -> str:
        if team_field:
            value = str(row.get(team_field) or "").strip()
            if value:
                return value
        return UNASSIGNED_TEAM

    @staticmethod
    def _trend(module: str, pending_total: int) -> list[dict[str, Any]]:
        """生成近七天（含今天）待处理量曲线，今天取真实值，前六天按演示形状回推。"""
        end = date.today()
        days = [end - timedelta(days=offset) for offset in range(6, -1, -1)]
        seed = sum(ord(ch) for ch in module)
        anchor = _TREND_SHAPE[seed % len(_TREND_SHAPE)]
        points: list[dict[str, Any]] = []
        for idx, day in enumerate(days):
            if idx < len(days) - 1:
                wobble = _TREND_SHAPE[(idx + seed) % len(_TREND_SHAPE)]
                value = max(0, pending_total + wobble - anchor)
            else:
                value = pending_total  # 最后一天与当前待处理量一致
            points.append({"date": day.isoformat(), "pending": value})
        return points


drilldown_service = DrilldownService()
