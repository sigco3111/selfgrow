"""맵 오버레이 — 파벌 영토 하이라이트, 선택 영역 표시."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World
    from .faction import Faction


# 지형 문자 (visualizer.py와 동일)
TILE_CHARS: dict[str, str] = {
    "plain": ".",
    "forest": "T",
    "mountain": "^",
    "water": "~",
    "desert": ",",
    "hill": "n",
    "swamp": "=",
}

# 지형 색상
TILE_STYLES: dict[str, str] = {
    "plain": "cp.green",
    "forest": "#8bd5ca",
    "mountain": "cp.white",
    "water": "cp.blue",
    "desert": "cp.amber",
    "hill": "#eed49f",
    "swamp": "cp.dim",
}

# 개체 심볼
SYM = {
    "HD": "#",
    "DB": "%",
    "SG": "o",
    "HR": "+",
    "SK": "x",
    "ST": "*",
    "SW": "@",
    "HM": "&",
    "HT": "H",
    "AR": "->",
}

# 직업별 색상
SPEC_STYLES: dict[str, str] = {
    "farmer": "cp.green",
    "miner": "cp.amber",
    "merchant": "cp.purple",
    "warrior": "cp.red",
    "crafter": "cp.blue",
    "explorer": "cp.cyan",
    "general": "cp.text",
}


def render_map_with_overlay(
    world: World,
    highlight_faction_id: int | None = None,
    highlight_entity: Entity | None = None,
    show_all_factions: bool = True,
    viewport_x: int = 0,
    viewport_y: int = 0,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
) -> Panel:
    """오버레이가 적용된 월드맵 렌더링.

    Args:
        world: 월드 객체
        highlight_faction_id: 강조할 파벌 ID (None이면 모든 파벌 표시)
        highlight_entity: 강조할 개체 (None이면 개체 강조 없음)
        show_all_factions: 모든 파벌 영토 표시 여부
        viewport_x: 뷰포트 시작 X (대형 월드 지원)
        viewport_y: 뷰포트 시작 Y (대형 월드 지원)
        viewport_width: 뷰포트 너비 (None이면 전체 월드)
        viewport_height: 뷰포트 높이 (None이면 전체 월드)

    Returns:
        Rich Panel 객체
    """
    map_text = Text()

    end_x = viewport_x + viewport_width if viewport_width else world.width
    end_y = viewport_y + viewport_height if viewport_height else world.height
    end_x = min(end_x, world.width)
    end_y = min(end_y, world.height)

    entity_positions: dict[tuple[int, int], list[Entity]] = {}
    for entity in world.entities.values():
        if entity.alive:
            entity_positions.setdefault((entity.x, entity.y), []).append(entity)

    for y in range(viewport_y, end_y):
        for x in range(viewport_x, end_x):
            tile = world.tile_at(x, y)
            if not tile:
                map_text.append(" ", "cp.dim")
                continue
            
            is_claimed = (x, y) in world.tile_claims
            entities_at = entity_positions.get((x, y), [])
            
            # 파벌 영토 색상 오버레이
            faction_territory_color = None
            faction_reg = world.faction_registry
            for fid, faction in faction_reg.items():
                if (x, y) in faction.territory:
                    if show_all_factions or fid == highlight_faction_id:
                        faction_territory_color = faction.color
                    break
            
            # 선택된 개체 강조
            is_highlighted = False
            if highlight_entity and entities_at:
                for e in entities_at:
                    if e.eid == highlight_entity.eid:
                        is_highlighted = True
                        break
            
            if entities_at:
                count = len(entities_at)
                first = entities_at[0]
                on_home = (
                    hasattr(first, "home_x")
                    and first.home_x == x
                    and first.home_y == y
                )
                
                if count >= 3:
                    ch = SYM["HD"]
                elif count == 2:
                    ch = SYM["DB"]
                elif on_home:
                    ch = SYM["HT"]
                else:
                    ch = SYM["SG"]
                
                # 선택된 개체는 별도 표시
                if is_highlighted:
                    style = "bold white on blue"
                elif first.faction_id >= 0 and faction_territory_color:
                    style = faction_territory_color
                else:
                    style = SPEC_STYLES.get(first.genome.specialization, "cp.text")
                
                map_text.append(ch, style=style)
            
            elif is_claimed:
                if faction_territory_color:
                    map_text.append(".", style=Style(dim=True, color="#6c7086"))
                else:
                    base = Style(dim=True, color="#585b70")
                    map_text.append(".", style=base)
            
            else:
                biome = tile.biome.value
                t_style = TILE_STYLES.get(biome, "cp.dim")
                t_char = TILE_CHARS.get(biome, "?")
                map_text.append(t_char, style=t_style)
        
        map_text.append("\n")
    
    # 제목 생성
    title = "[cp.cyan]🌍 월드 맵[/]"
    if highlight_faction_id is not None:
        faction = faction_reg.get(highlight_faction_id)
        if faction:
            title = f"[{faction.color}]{faction.name} 영토[/]"
    elif highlight_entity:
        title = f"[cp.cyan]🔍 {highlight_entity.name} 위치[/]"
    
    return Panel(
        map_text,
        title=title,
        border_style="cp.green",
        padding=(0, 1),
    )


def render_faction_legend(faction_reg: dict[int, Faction]) -> Panel:
    """파벌 범례 패널 렌더링.
    
    Args:
        faction_reg: 파벌 레지스트리
    
    Returns:
        Rich Panel 객체
    """
    if not faction_reg:
        return Panel(
            Text("(파벌 없음)", style="cp.dim"),
            title="[cp.red]🔥 파벌 범례[/]",
            border_style="cp.dim",
        )
    
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cp.text", width=12)
    table.add_column(style="cp.dim", width=6)
    table.add_column(style="cp.text")
    
    for fid, faction in sorted(faction_reg.items()):
        color = faction.color
        table.add_row(
            f"[{color}]■[/] [{color}]{faction.name}[/]",
            f"n={faction.member_count}",
            f"k={faction.total_kills}",
        )
    
    return Panel(
        table,
        title="[cp.red]🔥 파벌 범례[/]",
        border_style="cp.red",
        padding=(0, 1),
    )


def render_minimap(
    world: World,
    viewport_x: int = 0,
    viewport_y: int = 0,
    viewport_width: int = 40,
    viewport_height: int = 30,
) -> Panel:
    """미니맵 렌더링 (전체 월드 축소).
    
    Args:
        world: 월드 객체
        viewport_x: 뷰포트 시작 X
        viewport_y: 뷰포트 시작 Y
        viewport_width: 뷰포트 너비
        viewport_height: 뷰포트 높이
    
    Returns:
        Rich Panel 객체
    """
    minimap = Text()
    
    # 축소 비율 계산 (최대 20x15)
    scale_x = max(1, world.width // 20)
    scale_y = max(1, world.height // 15)
    
    for y in range(0, world.height, scale_y):
        for x in range(0, world.width, scale_x):
            tile = world.tile_at(x, y)
            if not tile:
                minimap.append(" ", "cp.dim")
                continue
            
            # 뷰포트 범위 확인
            in_viewport = (
                viewport_x <= x < viewport_x + viewport_width
                and viewport_y <= y < viewport_y + viewport_height
            )
            
            # 개체 존재 확인
            has_entity = False
            for e in world.entities.values():
                if e.alive and e.x == x and e.y == y:
                    has_entity = True
                    break
            
            if has_entity:
                minimap.append("●", style="cp.green" if in_viewport else "cp.dim")
            elif in_viewport:
                minimap.append("□", style="cp.cyan")
            else:
                biome = tile.biome.value
                char = TILE_CHARS.get(biome, "?")
                minimap.append(char, style="cp.dim")
        
        minimap.append("\n")
    
    return Panel(
        minimap,
        title="[cp.dim]🗺️ 미니맵[/]",
        border_style="cp.dim",
        padding=(0, 1),
    )
