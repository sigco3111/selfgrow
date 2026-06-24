"""대화형 지도 — 개체 추적, 계절 시각화, 무역 경로 표시."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World
    from .season import Season


# 계절별 지형 색상 보정
SEASON_COLOR_MODIFIERS: dict[str, dict[str, str]] = {
    "spring": {
        "plain": "#a6e3a1",
        "forest": "#94e2d5",
        "water": "#89b4fa",
    },
    "summer": {
        "plain": "#f9e2af",
        "forest": "#a6e3a1",
        "water": "#74c7ec",
    },
    "autumn": {
        "plain": "#fab387",
        "forest": "#f38ba8",
        "water": "#89b4fa",
    },
    "winter": {
        "plain": "#cdd6f4",
        "forest": "#bac2de",
        "water": "#a6adc8",
    },
}

# 지형 문자
TILE_CHARS: dict[str, str] = {
    "plain": ".",
    "forest": "T",
    "mountain": "^",
    "water": "~",
    "desert": ",",
    "hill": "n",
    "swamp": "=",
}

# 기본 지형 색상
TILE_STYLES: dict[str, str] = {
    "plain": "cp.green",
    "forest": "#8bd5ca",
    "mountain": "cp.white",
    "water": "cp.blue",
    "desert": "cp.amber",
    "hill": "#eed49f",
    "swamp": "cp.dim",
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


def render_interactive_map(
    world: World,
    current_season: Season | None = None,
    tracked_entity: Entity | None = None,
    show_trade_routes: bool = False,
    show_cultural_regions: bool = False,
) -> Panel:
    """대화형 지도 렌더링.
    
    Args:
        world: 월드 객체
        current_season: 현재 계절
        tracked_entity: 추적 중인 개체
        show_trade_routes: 무역 경로 표시 여부
        show_cultural_regions: 문화권 표시 여부
        
    Returns:
        Rich Panel 객체
    """
    map_text = Text()
    
    season_name = current_season.value if current_season else "spring"
    season_colors = SEASON_COLOR_MODIFIERS.get(season_name, {})
    
    entity_positions: dict[tuple[int, int], list[Entity]] = {}
    for entity in world.entities.values():
        if entity.alive:
            entity_positions.setdefault((entity.x, entity.y), []).append(entity)
    
    for y in range(world.height):
        for x in range(world.width):
            tile = world.tile_at(x, y)
            if not tile:
                map_text.append(" ", "cp.dim")
                continue
            
            entities_at = entity_positions.get((x, y), [])
            
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
                
                is_tracked = tracked_entity and first.eid == tracked_entity.eid
                if is_tracked:
                    style = "bold white on blue"
                elif first.faction_id >= 0:
                    from .faction import FACTION_COLORS
                    style = FACTION_COLORS[first.faction_id % len(FACTION_COLORS)]
                else:
                    style = SPEC_STYLES.get(first.genome.specialization, "cp.text")
                
                map_text.append(ch, style=style)
            
            else:
                biome = tile.biome.value
                t_style = season_colors.get(biome, TILE_STYLES.get(biome, "cp.dim"))
                t_char = TILE_CHARS.get(biome, "?")
                map_text.append(t_char, style=t_style)
        
        map_text.append("\n")
    
    title = "[cp.cyan]🌍 대화형 지도[/]"
    if tracked_entity:
        title = f"[cp.cyan]🔍 {tracked_entity.name} 추적[/]"
    
    return Panel(
        map_text,
        title=title,
        border_style="cp.green",
        padding=(0, 1),
    )


def render_entity_info_panel(entity: Entity) -> Panel:
    """개체 상세 정보 패널.
    
    Args:
        entity: 정보를 표시할 개체
        
    Returns:
        Rich Panel 객체
    """
    info = Text()
    
    info.append(f"이름: {entity.name}\n", style="cp.cyan")
    info.append(f"위치: ({entity.x}, {entity.y})\n", style="cp.text")
    info.append(f"나이: {entity.age}\n", style="cp.text")
    info.append(f"에너지: {entity.energy:.1f}/{entity.max_energy:.1f}\n", style="cp.text")
    info.append(f"직업: {entity.genome.specialization}\n", style="cp.text")
    
    if hasattr(entity, "culture"):
        info.append(f"언어: {entity.culture.language}\n", style="cp.text")
        if entity.culture.customs:
            customs = ", ".join(entity.culture.customs)
            info.append(f"관습: {customs}\n", style="cp.text")
    
    if entity.faction_id >= 0:
        info.append(f"파벌: {entity.faction_id}\n", style="cp.text")
    
    return Panel(
        info,
        title=f"[cp.cyan]📋 {entity.name} 정보[/]",
        border_style="cp.cyan",
        padding=(0, 1),
    )


def render_season_indicator(current_season: Season, tick: int) -> Panel:
    """계절 상태 표시 패널.
    
    Args:
        current_season: 현재 계절
        tick: 현재 틱
        
    Returns:
        Rich Panel 객체
    """
    season_names = {
        "spring": "봄",
        "summer": "여름",
        "autumn": "가을",
        "winter": "겨울",
    }
    
    season_colors = {
        "spring": "cp.green",
        "summer": "cp.amber",
        "autumn": "cp.red",
        "winter": "cp.blue",
    }
    
    name = season_names.get(current_season.value, current_season.value)
    color = season_colors.get(current_season.value, "cp.text")
    
    info = Text()
    info.append(f"계절: {name}\n", style=color)
    info.append(f"틱: {tick}", style="cp.text")
    
    return Panel(
        info,
        title=f"[{color}]🍃 계절[/]",
        border_style=color,
        padding=(0, 1),
    )
