"""자원 히트맵 — 자원 분포를 색상으로 시각화."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from ..world import World


HEAT_LEVELS = " ░▒▓█"
RESOURCE_COLORS: dict[str, str] = {
    "food": "cp.green",
    "wood": "cp.amber",
    "stone": "cp.dim",
    "iron": "cp.blue",
    "gold": "cp.magenta",
}


def _heat_char(density: float) -> str:
    idx = min(int(density * (len(HEAT_LEVELS) - 1)), len(HEAT_LEVELS) - 1)
    return HEAT_LEVELS[idx]


def render_resource_heatmap(
    world: World,
    resource_type: str = "food",
    scale: int = 2,
) -> Panel:
    color = RESOURCE_COLORS.get(resource_type, "cp.text")
    heatmap = Text()

    max_res = 0.0
    for y in range(0, world.height, scale):
        for x in range(0, world.width, scale):
            tile = world.tile_at(x, y)
            if tile:
                val = tile.resources.get(resource_type, 0)
                if val > max_res:
                    max_res = val

    if max_res == 0:
        max_res = 1.0

    for y in range(0, world.height, scale):
        for x in range(0, world.width, scale):
            tile = world.tile_at(x, y)
            if not tile:
                heatmap.append(" ", "cp.dim")
                continue

            val = tile.resources.get(resource_type, 0)
            density = val / max_res
            ch = _heat_char(density)

            if density > 0.7:
                s = f"bold {color}"
            elif density > 0.3:
                s = color
            else:
                s = "cp.dim"
            heatmap.append(ch, style=s)

        heatmap.append("\n")

    legend = Table.grid(padding=(0, 1))
    legend.add_column(style="cp.dim", width=4)
    legend.add_column(style="cp.text")
    for i, ch in enumerate(HEAT_LEVELS):
        pct = int(i / (len(HEAT_LEVELS) - 1) * 100)
        legend.add_row(f"[{color}]{ch}[/]", f"{pct}%+")

    return Panel(
        heatmap,
        title=f"[{color}]🗺️ {resource_type} 히트맵[/]",
        border_style=color,
        padding=(0, 1),
    )
