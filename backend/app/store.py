"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any

from app.seed import SEED_ROWS

# 下钻视图「负责班组」维度的取值字段；没有对应字段的模块不下班组分布。
OWNER_FIELDS: dict[str, str] = {
    "station": "运维班组",
    "cleaning": "作业班组",
    "sparepart": "所属班组",
    "inspection": "巡检人员",
    "defect": "发现人",
    "repair": "处理人员",
    "alarm": "确认人员",
    "permit": "工作负责人",
    "contractor": "联系人",
    "training": "培训对象",
    "settlement": "结算对象",
}

# 下钻视图「近七天趋势」的取数日期字段；没有日期字段的模块不统计趋势。
DATE_FIELDS: dict[str, str] = {
    "station": "投运日期",
    "inverter": "投运日期",
    "stringmon": "采集时间",
    "irradiance": "采集时间",
    "cleaning": "计划日期",
    "inspection": "开始时间",
    "defect": "发现时间",
    "repair": "完成时间",
    "sparepart": "领用日期",
    "generation": "统计日期",
    "curtail": "限电开始时间",
    "alarm": "触发时间",
    "permit": "许可时间",
    "training": "培训日期",
}

UNASSIGNED = "未分配"
UNKNOWN_STATUS = "未知状态"
TREND_DAYS = 7


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self) -> dict[str, object]:
        modules: list[dict[str, object]] = []
        for name in self.module_names():
            rows = self.rows(name)
            modules.append({
                "name": name,
                "created": len(rows),
                "pending": sum(1 for row in rows if row.get("pending")),
                "abnormal": sum(1 for row in rows if row.get("abnormal")),
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}

    def module_drilldown(self, module: str) -> dict[str, object] | None:
        """某个模块待处理条目的下钻视图：按状态、按负责班组分布，外加近七天趋势。

        与模块列表页读同一份数据、用同一个 pending 口径，保证看板数字和模块页面对得上。
        """
        if module not in self._tables:
            return None
        rows = self.rows(module)
        pending_rows = [row for row in rows if row.get("pending")]
        owner_field = OWNER_FIELDS.get(module)
        date_field = DATE_FIELDS.get(module)
        return {
            "module": module,
            "total": len(rows),
            "pending": len(pending_rows),
            "owner_field": owner_field,
            "date_field": date_field,
            "by_status": _count_by(pending_rows, "status", UNKNOWN_STATUS),
            "by_team": _count_by(pending_rows, owner_field, UNASSIGNED) if owner_field else [],
            "trend": _pending_trend(pending_rows, date_field),
        }


def _count_by(rows: list[dict[str, Any]], field: str, fallback: str) -> list[dict[str, object]]:
    """按某个字段聚合计数，空值归入 fallback；结果按数量降序、名称升序排列。"""
    counter: Counter[str] = Counter()
    for row in rows:
        name = str(row.get(field) or "").strip() or fallback
        counter[name] += 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _pending_trend(pending_rows: list[dict[str, Any]], date_field: str | None) -> list[dict[str, object]]:
    """近七天每日待处理条目数：按模块的日期字段落桶，没有日期字段时计 0。"""
    today = date.today()
    window = [today - timedelta(days=offset) for offset in range(TREND_DAYS - 1, -1, -1)]
    counts = {day: 0 for day in window}
    if date_field:
        for row in pending_rows:
            day = _parse_date(row.get(date_field))
            if day in counts:
                counts[day] += 1
    return [{"date": day.isoformat(), "count": counts[day]} for day in window]


def _parse_date(value: Any) -> date | None:
    """从字段值里解析日期，兼容「2026-09-01」和「2026-09-01 08:30」两种写法。"""
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


store = Store()
