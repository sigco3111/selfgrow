"""개체 상세 뷰 패널 — 선택 개체의 상세 정보 표시."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


# 직업별 아이콘/색상
SPEC_INFO: dict[str, tuple[str, str]] = {
    "farmer": ("🌾", "cp.green"),
    "miner": ("⛏️", "cp.amber"),
    "merchant": ("💰", "cp.purple"),
    "warrior": ("⚔️", "cp.red"),
    "crafter": ("🔨", "cp.blue"),
    "explorer": ("🧭", "cp.cyan"),
    "general": ("👤", "cp.text"),
}

# 뇌 타입 표시
BRAIN_INFO: dict[str, tuple[str, str]] = {
    "SmartBrain": ("🧠", "cp.cyan"),
    "RuleBasedBrain": ("⚙️", "cp.text"),
}


def get_spec_icon(spec: str) -> str:
    """직업 아이콘 반환."""
    icon, _ = SPEC_INFO.get(spec, ("👤", "cp.text"))
    return icon


def get_spec_color(spec: str) -> str:
    """직업 색상 반환."""
    _, color = SPEC_INFO.get(spec, ("👤", "cp.text"))
    return color


def format_brain_type(brain) -> str:
    """뇌 타입 문자열 반환."""
    brain_class = brain.__class__.__name__
    return brain_class


def render_entity_detail_panel(entity: Entity | None) -> Panel:
    """개체 상세 정보 패널 렌더링.
    
    Args:
        entity: 표시할 개체 (None이면 "선택 없음" 표시)
    
    Returns:
        Rich Panel 객체
    """
    if entity is None:
        return Panel(
            Text("개체를 선택하세요", style="cp.dim"),
            title="[cp.cyan]🧬 개체 상세[/]",
            border_style="cp.dim",
            padding=(0, 1),
        )
    
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cp.dim", width=14)
    table.add_column(style="cp.text")
    
    # 기본 정보
    spec = entity.genome.specialization
    spec_icon = get_spec_icon(spec)
    spec_color = get_spec_color(spec)
    brain_type = format_brain_type(entity.brain)
    brain_icon, brain_color = BRAIN_INFO.get(brain_type, ("❓", "cp.dim"))
    
    table.add_row(
        f"[{spec_color}]{spec_icon} 직업[/]",
        f"[{spec_color}]{spec}[/]",
    )
    table.add_row(
        f"[{brain_color}]{brain_icon} 뇌[/]",
        f"[{brain_color}]{brain_type}[/]",
    )
    
    # 구분선
    table.add_row("[cp.dim]─" * 14 + "[/]", "")
    
    # 상태 정보
    age_ratio = entity.age / entity.max_age if entity.max_age > 0 else 0
    energy_ratio = entity.energy / entity.max_energy if entity.max_energy > 0 else 0
    
    age_style = "cp.green" if age_ratio < 0.5 else "cp.amber" if age_ratio < 0.8 else "cp.red"
    energy_style = "cp.green" if energy_ratio > 0.5 else "cp.amber" if energy_ratio > 0.2 else "cp.red"
    
    table.add_row("나이", f"[{age_style}]{entity.age}/{entity.max_age}[/]")
    table.add_row("에너지", f"[{energy_style}]{entity.energy:.0f}/{entity.max_energy:.0f}[/]")
    table.add_row("위치", f"({entity.x}, {entity.y})")
    
    # 구분선
    table.add_row("[cp.dim]─" * 14 + "[/]", "")
    
    # 형질 정보
    traits = [
        ("공격성", entity.genome.aggression, "cp.red"),
        ("사회성", entity.genome.sociability, "cp.pink"),
        ("호기심", entity.genome.curiosity, "cp.cyan"),
        ("생산성", entity.genome.industry, "cp.green"),
        ("혁신성", entity.genome.innovation_rate, "cp.purple"),
    ]
    
    for trait_name, value, color in traits:
        # 바 차트 시각화
        bar_len = int(value * 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        table.add_row(
            f"[{color}]{trait_name}[/]",
            f"[{color}]{bar}[/] {value:.2f}",
        )
    
    # 구분선
    table.add_row("[cp.dim]─" * 14 + "[/]", "")
    
    # 인벤토리
    if entity.inventory:
        inv_items = []
        for rtype, amount in sorted(entity.inventory.items()):
            if amount > 0:
                inv_items.append(f"{rtype}:{amount:.0f}")
        table.add_row("인벤토리", " ".join(inv_items) if inv_items else "비어있음")
    
    # 장착 장비
    if entity.equipped:
        table.add_row("장착", ", ".join(entity.equipped))
    
    # 지식
    if hasattr(entity, "knowledge") and entity.knowledge:
        techs = list(entity.knowledge.known)[:5]
        if techs:
            table.add_row("기술", ", ".join(techs))
    
    # 전투 정보
    if entity.kill_count > 0:
        table.add_row("[cp.red]킬[/]", f"[cp.red]{entity.kill_count}[/]")
    
    # 파벌
    if entity.faction_id >= 0:
        table.add_row("[cp.red]파벌 ID[/]", f"[cp.red]{entity.faction_id}[/]")
    
    # 부(wealth)
    total_wealth = entity.total_wealth() if hasattr(entity, "total_wealth") else 0
    table.add_row("[cp.purple]부[/]", f"[cp.purple]{total_wealth:.1f}[/]")
    
    return Panel(
        table,
        title=f"[cp.cyan]🧬 {entity.name}[/]",
        border_style="cp.cyan",
        padding=(0, 1),
    )


def render_entity_list(entities: list[Entity], max_display: int = 10) -> Panel:
    """개체 목록 패널 렌더링.
    
    Args:
        entities: 개체 리스트
        max_display: 최대 표시 개수
    
    Returns:
        Rich Panel 객체
    """
    table = Table.grid(padding=(0, 1))
    table.add_column(style="cp.dim", width=8)
    table.add_column(style="cp.text", width=10)
    table.add_column(style="cp.dim", width=8)
    table.add_column(style="cp.text")
    
    # 헤더
    table.add_row(
        "[cp.dim]ID[/]",
        "[cp.dim]직업[/]",
        "[cp.dim]위치[/]",
        "[cp.dim]에너지[/]",
    )
    
    # 개체 목록 (에너지 순으로 정렬)
    sorted_entities = sorted(entities, key=lambda e: -e.energy)[:max_display]
    
    for entity in sorted_entities:
        spec = entity.genome.specialization
        spec_color = get_spec_color(spec)
        energy_ratio = entity.energy / entity.max_energy if entity.max_energy > 0 else 0
        energy_style = "cp.green" if energy_ratio > 0.5 else "cp.amber" if energy_ratio > 0.2 else "cp.red"
        
        table.add_row(
            f"{entity.eid:4d}",
            f"[{spec_color}]{spec[:6]}[/]",
            f"({entity.x},{entity.y})",
            f"[{energy_style}]{entity.energy:.0f}[/]",
        )
    
    return Panel(
        table,
        title=f"[cp.cyan]📋 개체 목록 ({len(entities)}개)[/]",
        border_style="cp.dim",
        padding=(0, 1),
    )
