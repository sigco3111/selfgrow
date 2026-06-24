"""이벤트 로그 패널 — 필터링, 타입별 분류, 향상된 표시."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .event_types import EVENT_NAMES_KR, get_event_icon, get_event_color
from .event_filters import FILTER_CATEGORIES, get_filtered_events

if TYPE_CHECKING:
    from .entity import Entity


def format_event(ev: dict, show_tick: bool = True) -> Text:
    """이벤트를 Rich Text로 포맷.
    
    Args:
        ev: 이벤트 딕셔너리
        show_tick: 틱 번호 표시 여부
    
    Returns:
        포맷된 Rich Text
    """
    tick = ev.get("tick", "?")
    etype = ev.get("type", "?")
    name = ev.get("entity_name", "?")
    data = ev.get("data", {})
    
    icon = get_event_icon(etype)
    color = get_event_color(etype)
    
    parts: list[tuple[str, str]] = []
    
    if show_tick:
        parts.append((f"[{tick}] ", "cp.dim"))
    
    parts.append((f"{icon} ", color))
    
    # 이벤트 타입별 포맷
    if etype == "reproduce":
        child = data.get("child", "?")
        partner = data.get("partner")
        if partner:
            parts.append((f"{name} × {partner}", "cp.text"))
            parts.append((f" → {child}", "cp.green"))
        else:
            parts.append((f"{name}", "cp.text"))
            parts.append((f" → {child} (단성생식)", "cp.green"))
    
    elif etype == "combat":
        target = data.get("target", "?")
        dmg = data.get("damage_dealt", 0)
        taken = data.get("damage_taken", 0)
        target_alive = data.get("target_alive", True)
        status = "" if target_alive else " 처치"
        parts.append((f"{name} → {target}", "cp.text"))
        parts.append((f" ({dmg:.0f}/{taken:.0f}{status})", color))
    
    elif etype == "loot":
        loot = data.get("loot", {})
        loot_str = ", ".join(f"{k}:{v:.0f}" for k, v in loot.items())
        parts.append((f"{name} 약탈", "cp.text"))
        parts.append((f" [{loot_str}]", "cp.amber"))
    
    elif etype == "craft":
        item = data.get("item", "?")
        parts.append((f"{name} 제작", "cp.text"))
        parts.append((f" → {item}", "cp.cyan"))
    
    elif etype == "construct":
        building = data.get("building", "?")
        parts.append((f"{name} 건설", "cp.text"))
        parts.append((f" → {building}", "cp.amber"))

    elif etype == "consume":
        food = data.get("food", 0)
        gained = data.get("energy_gained", 0)
        parts.append((f"{name} 섭취", "cp.text"))
        parts.append((f" (식량 {food:.0f} → 에너지 +{gained:.0f})", "cp.green"))

    elif etype == "gather":
        resource = data.get("resource", "?")
        amount = data.get("amount", 0)
        parts.append((f"{name} 채집", "cp.text"))
        parts.append((f" {resource} +{amount:.1f}", "cp.green"))

    elif etype == "move":
        to_pos = data.get("to", "?")
        parts.append((f"{name} 이동", "cp.text"))
        parts.append((f" → {to_pos}", "cp.dim"))

    elif etype == "ally_attack":
        ally = data.get("ally", "?")
        dmg = data.get("damage_contrib", 0)
        parts.append((f"{ally} → {name} 지원", "cp.text"))
        parts.append((f" (데미지 +{dmg:.1f})", "cp.blue"))

    elif etype == "trade_offer":
        sell = data.get("sell", "?")
        qty = data.get("qty", 0)
        price = data.get("unit_price", 0)
        parts.append((f"{name} 매도", "cp.text"))
        parts.append((f" {sell} ×{qty:.0f} @{price:.1f}", "cp.purple"))

    elif etype == "trade_bid":
        buy = data.get("buy", "?")
        qty = data.get("qty", 0)
        price = data.get("unit_price", 0)
        parts.append((f"{name} 매수", "cp.text"))
        parts.append((f" {buy} ×{qty:.0f} @{price:.1f}", "cp.purple"))

    elif etype == "tech_discovery":
        tech = data.get("tech", "?")
        parts.append((f"{tech} 발견!", "cp.cyan"))
    
    elif etype == "faction_formed":
        f_name = data.get("faction", "?")
        n = data.get("members", 0)
        leader = data.get("leader", "?")
        parts.append((f"{f_name} 결성", "cp.red"))
        parts.append((f" (인원 {n}, 지도자: {leader})", "cp.text"))
    
    elif etype == "faction_disbanded":
        f_name = data.get("faction", "?")
        reason = data.get("reason", "?")
        parts.append((f"{f_name} 해체", "cp.red"))
        parts.append((f" ({reason})", "cp.dim"))
    
    elif etype == "event_started":
        ev_name = data.get("event", "?")
        parts.append((f"⚠ {ev_name} 발생!", "cp.red"))

    elif etype == "event_ended":
        ev_name = data.get("event", "?")
        parts.append((f"{ev_name} 종료", "cp.green"))

    elif etype == "event_death":
        cause = data.get("cause", "?")
        parts.append((f"{name} 사망", "cp.red"))
        parts.append((f" ({cause})", "cp.dim"))

    elif etype == "starvation":
        parts.append((f"{name} 기아사", "cp.red"))

    elif etype == "death":
        parts.append((f"{name} 사망", "cp.red"))

    elif etype == "knowledge_transfer":
        from_name = data.get("from", "?")
        to_name = data.get("to", "?")
        tech = data.get("tech", "?")
        parts.append((f"{from_name} → {to_name}", "cp.text"))
        parts.append((f" {tech} 전수", "cp.cyan"))

    elif etype == "knowledge_loot":
        tech = data.get("tech", "?")
        from_name = data.get("from", "?")
        parts.append((f"{name} 지식 약탈", "cp.text"))
        parts.append((f" {tech} ← {from_name}", "cp.cyan"))

    elif etype == "equipment_loot":
        item = data.get("item", "?")
        from_name = data.get("from", "?")
        parts.append((f"{name} 장비 탈취", "cp.text"))
        parts.append((f" {item} ← {from_name}", "cp.amber"))

    elif etype == "equipment_broken":
        item = data.get("item", "?")
        parts.append((f"{name} 장비 파괴", "cp.red"))
        parts.append((f" {item}", "cp.dim"))

    elif etype == "building_destroyed":
        building = data.get("building", "?")
        target_name = data.get("target")
        if target_name:
            parts.append((f"{target_name} 건물 파괴", "cp.red"))
        else:
            parts.append((f"{name} 건물 파괴", "cp.red"))
        parts.append((f" {building}", "cp.dim"))

    elif etype == "diplomacy":
        msg = data.get("message", "?")
        parts.append((f"외교", "cp.text"))
        parts.append((f" {msg}", "cp.purple"))

    elif etype == "ideology_formed":
        ideo = data.get("ideology", "?")
        parts.append((f"{name} 이데올로기", "cp.text"))
        parts.append((f" {ideo} 형성", "cp.amber"))

    elif etype == "ideology_conversion":
        old = data.get("from", "?")
        new = data.get("to", "?")
        parts.append((f"{name} 이데올로기", "cp.text"))
        parts.append((f" {old} → {new}", "cp.amber"))

    elif etype == "trade":
        msg = data.get("message", "?")
        parts.append((f"{name} 거래", "cp.text"))
        parts.append((f" {msg}", "cp.purple"))

    elif etype == "message":
        msg = data.get("message", "?")
        parts.append((f"{name} 메시지", "cp.text"))
        parts.append((f" {msg}", "cp.blue"))
    
    else:
        kr_name = EVENT_NAMES_KR.get(etype, etype)
        parts.append((f"{name} {kr_name}", "cp.text"))
    
    # Rich Text 조합
    text = Text()
    for content, style in parts:
        text.append(content, style=style)
    
    return text


def render_event_log_panel(
    events: deque[dict],
    filter_category: str | None = None,
    max_display: int = 8,
    show_ticks: bool = True,
) -> Panel:
    """이벤트 로그 패널 렌더링.
    
    Args:
        events: 이벤트 딕셔너리 덱
        filter_category: 필터 카테고리 ("전투", "경제", "인구", "기술", "이벤트", "메시지", None)
        max_display: 최대 표시 이벤트 수
        show_ticks: 틱 번호 표시 여부
    
    Returns:
        Rich Panel 객체
    """
    if not events:
        return Panel(
            Text("(이벤트 없음)", style="cp.dim"),
            title="[cp.amber]📜 이벤트 로그[/]",
            border_style="cp.amber",
            padding=(0, 1),
        )
    
    filtered = get_filtered_events(events, filter_category)
    
    # 최근 N개만 표시
    recent = filtered[:max_display]
    
    # 이벤트 라인 생성
    lines: list[Text] = []
    for ev in recent:
        line = format_event(ev, show_tick=show_ticks)
        lines.append(line)
    
    content = Text("\n").join(lines) if lines else Text("(필터 결과 없음)", style="cp.dim")
    
    # 제목에 필터 정보 추가
    title = "[cp.amber]📜 이벤트 로그[/]"
    if filter_category:
        title = f"[cp.amber]📜 이벤트 로그 ({filter_category})[/]"
    
    return Panel(
        content,
        title=title,
        border_style="cp.amber",
        padding=(0, 1),
    )


def render_event_stats(events: deque[dict]) -> Table:
    """이벤트 통계 테이블 렌더링 (최근 100틱 기준).
    
    Returns:
        Rich Table 객체
    """
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cp.dim", width=14)
    table.add_column(style="cp.text")
    
    if not events:
        table.add_row("이벤트 없음", "")
        return table
    
    # 이벤트 타입별 카운트
    type_counts: dict[str, int] = {}
    for ev in events:
        etype = ev.get("type", "unknown")
        type_counts[etype] = type_counts.get(etype, 0) + 1
    
    # 상위 5개 표시
    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])[:5]
    for etype, count in sorted_types:
        icon = get_event_icon(etype)
        color = get_event_color(etype)
        kr_name = EVENT_NAMES_KR.get(etype, etype)
        table.add_row(
            f"[{color}]{icon} {kr_name}[/]",
            f"{count}",
        )
    
    return table
