"""이벤트 필터링 로직 — 카테고리별 분류 및 인덱스."""

from __future__ import annotations

from collections import deque


FILTER_CATEGORIES: dict[str, list[str]] = {
    "전투": ["combat", "loot", "equipment_loot", "equipment_broken", "faction_formed", "faction_disbanded"],
    "경제": ["trade", "craft", "construct", "building_destroyed"],
    "인구": ["reproduce", "death", "starvation", "event_death"],
    "기술": ["tech_discovery", "knowledge_loot"],
    "이벤트": ["event_started", "event_ended"],
    "메시지": ["message"],
}


class EventIndex:
    def __init__(self) -> None:
        self._type_to_indices: dict[str, list[int]] = {}
        self._all_events: deque[dict] | None = None
        self._last_id: int = -1

    def update(self, events: deque[dict]) -> None:
        if events is self._all_events and len(events) == self._last_id + 1:
            new_start = self._last_id + 1
        else:
            self._type_to_indices.clear()
            new_start = 0
            self._all_events = events

        for i in range(new_start, len(events)):
            ev = events[i]
            etype = ev.get("type", "unknown")
            self._type_to_indices.setdefault(etype, []).append(i)
        self._last_id = len(events) - 1

    def get_by_type(self, events: deque[dict], etype: str) -> list[dict]:
        self.update(events)
        indices = self._type_to_indices.get(etype, [])
        return [events[i] for i in indices if i < len(events)]

    def get_by_category(self, events: deque[dict], category: str) -> list[dict]:
        allowed = FILTER_CATEGORIES.get(category, [])
        self.update(events)
        result = []
        for t in allowed:
            for i in self._type_to_indices.get(t, []):
                if i < len(events):
                    result.append(events[i])
        return result


_event_index = EventIndex()


def get_filtered_events(events: deque[dict], filter_category: str | None = None) -> list[dict]:
    if filter_category and filter_category in FILTER_CATEGORIES:
        filtered = _event_index.get_by_category(events, filter_category)
        return list(reversed(filtered))
    return list(reversed(events))
