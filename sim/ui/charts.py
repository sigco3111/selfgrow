"""시계열 차트 패널 — 문자 스파크라인으로 메트릭 추이 시각화.

캐싱: 동일 스냅샷 키일 때 이전 렌더링 결과를 재사용하여 렌더링 속도 향상.
커스터마이징: visible_metrics로 표시할 지표를 선택 가능.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from .metrics import MetricsCollector


# 스파크라인 문자 (8단계)
SPARK_CHARS = "▁▂▃▄▅▆▇█"

# 사용 가능한 모든 지표 키
ALL_METRIC_KEYS = ["population", "gini", "wealth", "energy", "top_prices"]

# 차트 캐시 (스냅샷 키 -> Panel)
_cache: dict[str, object] = {"key": -1, "panel": None}


def sparkline(values: list[float], width: int = 20) -> str:
    """값 리스트를 문자 스파크라인으로 변환.
    
    Args:
        values: 시계열 값 리스트
        width: 스파크라인 표시 너비 (최근 N개 값 사용)
    
    Returns:
        스파크라인 문자열
    """
    if not values:
        return ""
    
    # 최근 width개 값만 사용
    recent = values[-width:] if len(values) > width else values
    
    min_val = min(recent)
    max_val = max(recent)
    val_range = max_val - min_val
    
    if val_range == 0:
        return SPARK_CHARS[4] * len(recent)  # 중간 값으로 채우기
    
    result = []
    for v in recent:
        normalized = (v - min_val) / val_range
        idx = int(normalized * (len(SPARK_CHARS) - 1))
        result.append(SPARK_CHARS[idx])
    
    return "".join(result)


def delta_indicator(current: float, previous: float) -> Text:
    """값 변화를 화살표 + 색상으로 표시.
    
    Returns:
        Rich Text 객체 (상승=초록, 하락=빨강, 변동없음=회색)
    """
    diff = current - previous
    if abs(diff) < 0.01:
        return Text("→ 0.0", style="cp.dim")
    
    arrow = "↑" if diff > 0 else "↓"
    color = "cp.green" if diff > 0 else "cp.red"
    return Text(f"{arrow} {diff:+.1f}", style=color)


def render_timeseries_panel(
    metrics: MetricsCollector,
    width: int = 20,
    visible_metrics: list[str] | None = None,
) -> Panel:
    """시계열 차트 패널 렌더링.

    Args:
        metrics: 메트릭 수집기 인스턴스
        width: 차트 너비 (표시할 이전 값 개수)
        visible_metrics: 표시할 지표 키 리스트 (None이면 전부 표시).
            키: "population", "gini", "wealth", "energy", "top_prices"

    Returns:
        Rich Panel 객체 (캐싱 적용)
    """
    snapshots = list(metrics.snapshots)

    if len(snapshots) < 2:
        empty_table = Table.grid(padding=(0, 2))
        empty_table.add_column(style="cp.dim", width=14)
        empty_table.add_column(style="cp.text")
        empty_table.add_row("데이터 부족", f"(스냅샷 {len(snapshots)}개)")
        return Panel(
            empty_table,
            title="[cp.cyan]📈 시계열[/]",
            border_style="cp.dim",
        )

    # 캐시 키 = 마지막 스냅샷의 tick + population + avg_wealth
    latest = snapshots[-1]
    cache_key = hash((latest.tick, latest.population, latest.avg_wealth,
                       tuple(visible_metrics) if visible_metrics else None))
    if cache_key == _cache["key"] and _cache["panel"] is not None:
        return _cache["panel"]  # type: ignore[return-value]

    show = visible_metrics or ALL_METRIC_KEYS

    table = Table.grid(padding=(0, 2))
    table.add_column(style="cp.dim", width=14)
    table.add_column(width=width + 2)
    table.add_column(style="cp.text", width=12)

    if "population" in show:
        data = [s.population for s in snapshots]
        spark = sparkline(data, width)
        table.add_row("[cp.green]인구[/]", f"[cp.green]{spark}[/]",
                       f"[cp.green]{data[-1]:.0f}[/]")

    if "gini" in show:
        data = [s.gini_coefficient for s in snapshots]
        spark = sparkline(data, width)
        table.add_row("[cp.amber]지니계수[/]", f"[cp.amber]{spark}[/]",
                       f"[cp.amber]{data[-1]:.3f}[/]")

    if "wealth" in show:
        data = [s.avg_wealth for s in snapshots]
        spark = sparkline(data, width)
        table.add_row("[cp.purple]평균 부[/]", f"[cp.purple]{spark}[/]",
                       f"[cp.purple]{data[-1]:.1f}[/]")

    if "energy" in show:
        data = [s.avg_energy for s in snapshots]
        spark = sparkline(data, width)
        table.add_row("[cp.cyan]에너지[/]", f"[cp.cyan]{spark}[/]",
                       f"[cp.cyan]{data[-1]:.1f}[/]")

    if "top_prices" in show:
        table.add_row("[cp.dim]─" * 14 + "[/]", "", "")
        latest_prices = latest.prices
        price_data: dict[str, list[float]] = {r: [] for r in latest_prices}
        for s in snapshots:
            for rtype in price_data:
                price_data[rtype].append(s.prices.get(rtype, 0.0))
        sorted_prices = sorted(latest_prices.items(), key=lambda x: -x[1])[:3]
        for rtype, price in sorted_prices:
            data = price_data.get(rtype, [])
            spark = sparkline(data, width)
            table.add_row(f"[cp.blue]{rtype}[/]", f"[cp.blue]{spark}[/]",
                           f"[cp.blue]{price:.1f}[/]")

    panel = Panel(table, title="[cp.cyan]📈 시계열[/]",
                   border_style="cp.cyan", padding=(0, 1))
    _cache["key"] = cache_key
    _cache["panel"] = panel
    return panel
