"""이벤트 타입 정의 — 아이콘, 색상, 한글 이름."""

from __future__ import annotations

EVENT_STYLES: dict[str, tuple[str, str]] = {
    "reproduce": ("💕", "cp.pink"),
    "death": ("💀", "cp.red"),
    "starvation": ("🥀", "cp.red"),
    "tech_discovery": ("💡", "cp.cyan"),
    "combat": ("⚔️", "cp.red"),
    "craft": ("🔨", "cp.blue"),
    "construct": ("🏗️", "cp.amber"),
    "loot": ("💰", "cp.amber"),
    "faction_formed": ("⚡", "cp.red"),
    "faction_disbanded": ("☠️", "cp.red"),
    "knowledge_loot": ("📚", "cp.cyan"),
    "equipment_loot": ("🗡️", "cp.amber"),
    "equipment_broken": ("💥", "cp.red"),
    "event_started": ("🌟", "cp.red"),
    "event_ended": ("✅", "cp.green"),
    "event_death": ("☠️", "cp.red"),
    "building_destroyed": ("🏚️", "cp.red"),
    "trade": ("🤝", "cp.purple"),
    "trade_offer": ("📤", "cp.purple"),
    "trade_bid": ("📥", "cp.purple"),
    "message": ("💬", "cp.blue"),
    "consume": ("🍽️", "cp.green"),
    "gather": ("⛏️", "cp.green"),
    "move": ("👣", "cp.dim"),
    "ally_attack": ("🛡️", "cp.blue"),
    "knowledge_transfer": ("📖", "cp.cyan"),
    "diplomacy": ("🤝", "cp.purple"),
    "ideology_formed": ("🧠", "cp.amber"),
    "ideology_conversion": ("🔄", "cp.amber"),
}

EVENT_NAMES_KR: dict[str, str] = {
    "reproduce": "번식",
    "death": "사망",
    "starvation": "기아사",
    "tech_discovery": "기술 발견",
    "combat": "전투",
    "craft": "제작",
    "construct": "건설",
    "loot": "약탈",
    "faction_formed": "파벌 결성",
    "faction_disbanded": "파벌 해체",
    "knowledge_loot": "지식 약탈",
    "equipment_loot": "장비 약탈",
    "equipment_broken": "장비 파괴",
    "event_started": "자연재해 발생",
    "event_ended": "자연재해 종료",
    "event_death": "자연재해 사망",
    "building_destroyed": "건물 파괴",
    "trade": "거래",
    "trade_offer": "매도 등록",
    "trade_bid": "매수 신청",
    "message": "메시지",
    "consume": "섭취",
    "gather": "채집",
    "move": "이동",
    "ally_attack": "동맹 지원",
    "knowledge_transfer": "지식 전수",
    "diplomacy": "외교",
    "ideology_formed": "이데올로기 형성",
    "ideology_conversion": "이데올로기 전파",
}


def get_event_icon(etype: str) -> str:
    icon, _ = EVENT_STYLES.get(etype, ("❓", "cp.dim"))
    return icon


def get_event_color(etype: str) -> str:
    _, color = EVENT_STYLES.get(etype, ("❓", "cp.dim"))
    return color
