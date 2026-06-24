"""개체 궤적 시각화 — 개체의 이동 경로를 점선으로 표시."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from ..entity import Entity
    from ..world import World

from .map_overlay import TILE_CHARS, TILE_STYLES, SPEC_STYLES


def render_map_with_trail(
    world: World,
    entity: Entity,
    trail_length: int = 20,
) -> Panel:
    visited = list(entity.visited_tiles)
    trail = visited[-trail_length:] if len(visited) > trail_length else visited
    trail_set = set(trail)

    map_text = Text()

    entity_positions: dict[tuple[int, int], list[Entity]] = {}
    for e in world.entities.values():
        if e.alive:
            entity_positions.setdefault((e.x, e.y), []).append(e)

    for y in range(world.height):
        for x in range(world.width):
            tile = world.tile_at(x, y)
            if not tile:
                map_text.append(" ", "cp.dim")
                continue

            pos = (x, y)
            entities_at = entity_positions.get(pos, [])

            if pos == (entity.x, entity.y):
                map_text.append("@", style="bold white on blue")
            elif entities_at:
                first = entities_at[0]
                style = SPEC_STYLES.get(first.genome.specialization, "cp.text")
                count = len(entities_at)
                ch = "#" if count >= 3 else "%" if count == 2 else "o"
                map_text.append(ch, style=style)
            elif pos in trail_set:
                idx = trail.index(pos) if pos in trail else 0
                density = idx / max(1, len(trail) - 1)
                if density > 0.6:
                    map_text.append("·", style="cp.cyan")
                elif density > 0.3:
                    map_text.append("∘", style="cp.blue")
                else:
                    map_text.append("─", style="cp.dim")
            else:
                biome = tile.biome.value
                t_style = TILE_STYLES.get(biome, "cp.dim")
                t_char = TILE_CHARS.get(biome, "?")
                map_text.append(t_char, style=t_style)

        map_text.append("\n")

    return Panel(
        map_text,
        title=f"[cp.cyan]🛤️ {entity.name} 궤적 (최근 {len(trail)}칸)[/]",
        border_style="cp.cyan",
        padding=(0, 1),
    )
