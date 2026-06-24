"""전체 시뮬레이션 파라미터 — 모든 튜너블 상수는 여기서 관리."""

import random
from dataclasses import dataclass
from typing import ClassVar

# 설정 오버라이드 (실험 프레임워크 Phase 2.2)
_OVERRIDABLE_NAMES: set[str] = set()

def _overridable(name: str, default: object) -> object:
    _OVERRIDABLE_NAMES.add(name)
    return default

def apply_overrides(overrides: dict[str, object]) -> None:
    for key, value in overrides.items():
        if key in _OVERRIDABLE_NAMES:
            globals()[key] = value
        else:
            raise KeyError(f"Unknown or non-overridable config key: {key}")


def create_rng(seed: int, subsystem: str) -> random.Random:
    """서브시스템별 독립된 RNG 인스턴스 생성.
    
    각 서브시스템(engine, world, entity, brain, market, faction, events 등)은
    고유한 시드 공간을 가지도록 subsystem 문자열을 해시하여 결합.
    """
    import hashlib
    combined = f"{seed}:{subsystem}"
    derived_seed = int(hashlib.sha256(combined.encode()).hexdigest()[:8], 16)
    return random.Random(derived_seed)


# ──────────────────────────────────────────────
# 월드
# ──────────────────────────────────────────────
WORLD_WIDTH = _overridable("WORLD_WIDTH", 40)
WORLD_HEIGHT = _overridable("WORLD_HEIGHT", 30)
SEED = _overridable("SEED", 42)                  # 난수 시드 (재현성)

# 지형 비율 (합 1.0)
BIOME_WEIGHTS: dict[str, float] = {
    "plain": 0.30,
    "forest": 0.20,
    "mountain": 0.12,
    "water": 0.10,
    "desert": 0.10,
    "hill": 0.10,
    "swamp": 0.08,
}

# 자원 재생성: 매 틱마다 각 타일이 가진 최대량의 몇 % 회복하는지
RESOURCE_REGEN_RATE = 0.0004  # 0.04%/tick — 희소하지만 생존 가능한 수준

# 타일별 자원 편차 (개별 타일 생성 시 MAX * random(1-VAR, 1+VAR))
RESOURCE_TILE_VARIATION = 0.5  # ±50% 편차 — 부유한 타일과 빈약한 타일 차이 확보

# 타일 1칸당 최대 자원 보유량 (기준치, 실제는 VARATION 적용)
MAX_TILE_RESOURCES: dict[str, dict[str, float]] = {
    "plain":   {"food": 25, "wood": 4,  "stone": 2,  "iron": 0,  "gold": 0},
    "forest":  {"food": 15, "wood": 35, "stone": 4,  "iron": 0,  "gold": 0},
    "mountain": {"food": 3,  "wood": 2,  "stone": 35, "iron": 20, "gold": 8},
    "water":   {"food": 12, "wood": 0,  "stone": 0,  "iron": 0,  "gold": 0},
    "desert":  {"food": 3,  "wood": 1,  "stone": 15, "iron": 10, "gold": 3},
    "hill":    {"food": 10, "wood": 8,  "stone": 15, "iron": 8,  "gold": 2},
    "swamp":   {"food": 8,  "wood": 12, "stone": 4,  "iron": 2,  "gold": 0},
}


# ──────────────────────────────────────────────
# 개체 (Entity)
# ──────────────────────────────────────────────
INITIAL_ENTITY_COUNT = _overridable("INITIAL_ENTITY_COUNT", 40)

RESOURCE_MAX_STACK = 8               # 인벤토리 슬롯당 최대 적재량
BASE_GATHER_RATE = 2.0               # 기본 채집량
CONSUME_FOOD_AMOUNT = 2.0            # 한 번에 소비하는 식량량
TRADE_SURPLUS_THRESHOLD: dict[str, int] = {"food": 4, "default": 3}
TRADE_SELL_RATIO = 0.5               # 잉여 자원 중 판매 비율
KNOWLEDGE_INHERIT_RATIO = 0.3        # 번식 시 부모 지식 상속 비율
RESOURCE_BEQUEST_RATIO = 0.2         # 번식 시 부모 자원 상속 비율
MAX_EQUIPPED_SLOTS = 3               # 최대 장비 슬롯 수
AGING_ENERGY_COST = 5.0              # 노화 시 매 틱 에너지 감소량

BASE_MAX_ENERGY = 100.0
BASE_ENERGY = 80.0
BASE_SPEED = 1.0           # 한 틱에 이동 가능한 칸 수
BASE_INVENTORY_SLOTS = 10
BASE_ATTACK = 5.0
BASE_DEFENSE = 3.0

# 매 틱 소비 에너지 (행동별)
ENERGY_COST = {
    "idle": 1.5,
    "explore": 2.5,
    "gather": 3.0,
    "trade": 2.0,
    "craft": 4.0,
    "reproduce": 25.0,
    "combat": 7.0,
    "construct": 6.0,
}

# 배고픔 임계치 (energy/max_energy 비율)
HUNGER_THRESHOLD = 0.35    # 이 아래로 내려가면 먹이 찾기 우선
STARVATION_SPEED = 2.5     # 임계치 아래일 때 추가 에너지 소모 계수

# 소비: food 1단위 → energy 회복량
FOOD_ENERGY = 7.0

# 번식 조건
REPRODUCTION_ENERGY_RATIO = 0.65  # 최대 에너지의 65% 이상
REPRODUCTION_MIN_FOOD = 6.0       # 번식에 필요한 최소 식량
REPRODUCTION_COOLDOWN = 35         # 번식 후 쿨다운
MUTATION_RATE = 0.1                # 유전자 변이 확률
MUTATION_MAGNITUDE = 0.2           # 변이 시 최대 변화량 (±비율)
INITIAL_KNOWLEDGE_COUNT = 1        # 초기 보유 지식 수

# 수명
BASE_LIFESPAN = 500       # 평균 수명 (틱)
LIFESPAN_VARIANCE = 200    # 개체별 편차


# ──────────────────────────────────────────────
# 시장
# ──────────────────────────────────────────────
MARKET_TAX_RATE = 0.02   # 거래 수수료 2%
ORDER_EXPIRY = 20          # 주문이 자동 만료되는 틱 수
PRICE_HISTORY_LENGTH = 100  # 가격 지수 저장 길이
TRADE_HISTORY_MAXLEN = 5000  # 거래 내역 최대 보관 수 (메모리 보호)

PRICE_FLOOR: dict[str, float] = {
    "food": 0.5, "wood": 0.5, "stone": 0.5,
    "iron": 2.0, "gold": 5.0,
}
BASE_PRICES: dict[str, float] = {
    "food": 2.0, "wood": 3.0, "stone": 4.0,
    "iron": 8.0, "gold": 15.0,
}


# ──────────────────────────────────────────────
# 전투
# ──────────────────────────────────────────────
COMBAT_BASE_DAMAGE = 15.0
COMBAT_DAMAGE_VARIANCE = 0.25  # ±25% 무작위성
COMBAT_WINNER_LOOT_RATIO = 0.6  # 승자가 패자의 인벤토리 60% 획득
COMBAT_ENERGY_COST = 10.0
COMBAT_HOME_BONUS = 0.3        # 본거지 전투 시 30% 공/방 보정


# ──────────────────────────────────────────────
# 영토
# ──────────────────────────────────────────────
TERRITORY_CLAIM_TICKS = 15     # 이 타일에서 이틱 이상 머물면 클레임
TERRITORY_RADIUS = 3           # 본거지 기준 영토 반경 (맨해튼 거리)
TERRITORY_ABANDON_TICKS = 30   # 떠난 지 이틱 후 클레임 소멸
HOME_SITE_MEMORY = 20          # 최근 방문 타일 기억 개수


# ──────────────────────────────────────────────
# 크래프팅 (도구/무기)
# ──────────────────────────────────────────────
CRAFT_RECIPES: dict[str, list[tuple[str, float]]] = {
    "stone_axe":    [("wood", 3), ("stone", 5)],
    "iron_sword":   [("iron", 5), ("wood", 2)],
    "iron_armor":   [("iron", 8), ("stone", 3)],
    "fishing_rod":  [("wood", 4), ("stone", 1)],
    "gold_ornament": [("gold", 3), ("wood", 1)],
}

CRAFT_BONUS: dict[str, dict[str, float]] = {
    "stone_axe":    {"gather_wood": 2.0, "gather_stone": 1.5},
    "iron_sword":   {"attack": 10.0},
    "iron_armor":   {"defense": 8.0},
    "fishing_rod":  {"gather_food": 2.0},
    "gold_ornament": {"sociability": 0.2},  # 지식 전수/번식 확률 증가
}


# ──────────────────────────────────────────────
# 지식/기술
# ──────────────────────────────────────────────
@dataclass
class TechDef:
    name: str
    description: str
    prerequisites: list[str]      # 선행 기술
    discovery_cost: int           # 필요한 연구 포인트
    effect: dict                  # 적용 효과

# 연구 포인트 생성 계수
RESEARCH_POINT_BASE_RATE = 0.1        # innovation_rate * 이 값이 기본 생성량
RESEARCH_POINT_PER_KNOWLEDGE = 0.15   # 보유 지식 하나당 추가 계수
RESEARCH_FOCUS_THRESHOLD = 0.6        # 집중 연구 확률 (1.0=항상 집중, 0.0=항상 분산)

TECH_TREE: list[TechDef] = [
    # ── Tier 1 (선행 조건 없음, 비용 50) ──
    TechDef("basic_agriculture", "농업 기초 - 식량 채집 효율 1.5배, 식량 최대 보유량 +5",
            [], 50, {"gather_food": 1.5, "max_food_storage": 5.0}),
    TechDef("mining", "채광 기술 - 돌/철 채집 효율 1.5배, 인벤토리 +2칸",
            [], 50, {"gather_stone": 1.5, "gather_iron": 1.5, "max_inventory": 2}),
    TechDef("survival", "생존 기술 - 최대 에너지 +20, 에너지 소비 -10%",
            [], 40, {"max_energy": 20.0, "energy_efficiency": 0.1}),

    # ── Tier 2 (선행 1개 필요, 비용 70~80) ──
    TechDef("irrigation", "관개 농업 - 식량 채집 효율 2.5배, 식량 1당 에너지 회복량 +50%",
            ["basic_agriculture"], 80, {"gather_food": 2.5, "food_energy_mult": 1.5}),
    TechDef("currency", "화폐 도입 - 시장 거래 수수료 절반, 자원 매매 자동화",
            ["basic_agriculture"], 70, {"trade_efficiency": 0.4, "market_tax_discount": 0.5}),
    TechDef("sailing", "항해술 - 물 타일 통과 가능, 탐험 시 추가 이동 거리 +1",
            ["basic_agriculture"], 60, {"cross_water": True, "explore_range": 1}),
    TechDef("architecture", "건축술 - 방어력 +5, 영토 전투 보정 +20%",
            ["mining"], 70, {"defense": 5.0, "home_bonus_extra": 0.2}),
    TechDef("weapon_smithing", "무기 제작 - 공격력 +5, 돌도끼/철검 성능 2배",
            ["mining"], 60, {"attack": 5.0, "craft_weapon_boost": True}),

    # ── Tier 3 (선행 2개 필요, 비용 100~130) ──
    TechDef("metallurgy", "야금술 - 철제 장비 제작 가능, 돌/철 채집 효율 2배",
            ["mining", "weapon_smithing"], 100, {"craft_iron": True, "gather_stone": 2.0, "gather_iron": 2.0}),
    TechDef("bureaucracy", "관료제 - 파벌 결속력 +0.2, 파벌 최대 인원 +10, 전쟁 시 사기 보정",
            ["currency"], 100, {"faction_cohesion": 0.2, "faction_max_members": 10, "faction_morale": 0.15}),

    # ── Tier 4 (선행 2+개, 비용 140) ──
    TechDef("alchemy", "연금술 - 금 가치 3배, 금 거래 보너스, 금 장식 효과 2배",
            ["metallurgy", "currency"], 140, {"gold_value_mult": 3.0, "trade_gold_bonus": 0.3, "gold_ornament_boost": True}),
]

# 기술 효과 Lookup 캐시 (O(1) 조회 — get_combined_effects() 최적화)
TECH_EFFECTS_MAP: dict[str, dict] = {t.name: t.effect for t in TECH_TREE}


# ──────────────────────────────────────────────
# 지니계수 / 통계
# ──────────────────────────────────────────────
METRICS_SNAPSHOT_INTERVAL = 10   # n틱마다 스냅샷 저장
METRICS_SNAPSHOT_MAXLEN = 2000   # 스냅샷 최대 보관 개수 (메모리 보호)
WORLD_LOG_INTERVAL = 50          # n틱마다 월드 상태 로그


# ──────────────────────────────────────────────
# 파벌 (Faction)
# ──────────────────────────────────────────────
FACTION_ENABLED = _overridable("FACTION_ENABLED", True)
FACTION_FORMATION_SOCIABILITY = 0.1  # 파벌 결성에 필요한 최소 사회성
FACTION_FORMATION_RADIUS = 5          # 같은 파벌로 결성될 최대 거리 (맨해튼)
FACTION_FORMATION_MIN_MEMBERS = 3     # 파벌 결성에 필요한 최소 인원
FACTION_FORMATION_TICKS = 20          # 이 틱 이상 함께 있어야 결성
FACTION_MAX_MEMBERS = 15              # 파벌 최대 인원
FACTION_ALLY_SUPPORT_RADIUS = 3       # 전투 시 동맹 지원 반경
FACTION_ALLY_COMBAT_BONUS = 0.15      # 동맹 지원 시 공/방 15% 보정
FACTION_TERRITORY_RADIUS = 5          # 파벌 영토 반경 (지도자 기준)
FACTION_COHESION_BREAKUP = 0.3        # 결속력이 이 아래면 파벌 해체 위험
FACTION_WAR_DURATION = 50             # 선언 후 자동 종료까지 틱


# ──────────────────────────────────────────────
# 이데올로기 시스템 (Phase 3.1)
# ──────────────────────────────────────────────
IDEOLOGIES: dict[str, dict] = {
    "materialism": {
        "traits": {"industry": 0.15, "sociability": 0.1},
        "action_bias": {"trade": 1.3, "gather": 1.2, "craft": 1.2},
    },
    "militarism": {
        "traits": {"aggression": 0.2, "loyalty": 0.15},
        "action_bias": {"combat": 1.5, "explore": 1.1},
    },
    "spiritualism": {
        "traits": {"curiosity": 0.1, "sociability": 0.15},
        "action_bias": {"explore": 1.2, "reproduce": 1.2},
    },
    "egalitarianism": {
        "traits": {"sociability": 0.2, "loyalty": 0.1},
        "action_bias": {"trade": 1.4},
    },
}
IDEOLOGY_FORMATION_TICKS = 30
IDEOLOGY_TRANSFER_RADIUS = 2
IDEOLOGY_CONVERSION_CHANCE = 0.05
IDEOLOGY_SAME_BONUS = 0.15
IDEOLOGY_DIFFERENT_PENALTY = 0.1


# ──────────────────────────────────────────────
# 전투 강화
# ──────────────────────────────────────────────
EQUIPMENT_BREAK_CHANCE = 0.08         # 전투 후 장비 파괴 확률 8%
COMBAT_ALLY_CONTRIBUTION = 0.4        # 동맹 지원 시 공격력 기여 비율
COMBAT_KNOWLEDGE_LOOT_CHANCE = 0.3    # 전사한 적 지식 약탈 확률
COMBAT_EQUIPMENT_LOOT_CHANCE = 0.2    # 전사한 적 장비 약탈 확률
COMBAT_PURSUIT_RADIUS = 5             # 승리 후 추격 반경
COMBAT_RETREAT_THRESHOLD = 0.25       # 에너지 비율 이하면 후퇴


# ──────────────────────────────────────────────
# SmartBrain — 듀얼 브레인 시스템
# ──────────────────────────────────────────────
SMART_BRAIN_RATIO = _overridable("SMART_BRAIN_RATIO", 0.25)          # 전체 개체 중 SmartBrain 비율 (0.25 = 25%)
SMART_MEMORY_SIZE = 50            # 각 SmartBrain이 기억하는 최근 경험 수
SMART_SIMILARITY_THRESHOLD = 0.7  # 경험 참조를 위한 상태 유사도 임계값
SMART_PLANNING_RATE = 0.3         # 멀티스텝 계획 시도 확률 (매 결정마다)
SMART_PLANNING_DISCOUNT = 0.6     # 미래 액션 점수 할인율 (0~1, 높을수록 미래 중시)
SMART_LEARNING_RATE = 0.1         # 경험 보정의 학습률 (너무 높으면 불안정)
SMART_TRADE_THRESHOLD = 3          # SmartBrain 거래 제안 수락 임계값
SMART_SURPLUS_THRESHOLDS: dict[str, int] = {"food": 5, "default": 3}


# ──────────────────────────────────────────────
# 계절 시스템
# ──────────────────────────────────────────────
SEASON_LENGTH = 25  # 한 계절의 틱 수
SEASON_NAMES = ["spring", "summer", "autumn", "winter"]

# 계절별 효과 배율 [봄, 여름, 가을, 겨울] (기준=1.0)
SEASON_RESOURCE_REGEN = [1.2, 1.1, 1.0, 0.7]      # 자원 재생률
SEASON_ENERGY_COST = [1.0, 1.15, 1.0, 1.2]         # 에너지 소비
SEASON_GATHER_BONUS = [1.0, 1.0, 1.1, 0.9]         # 채집 효율
SEASON_SPEED_MOD = [1.0, 1.0, 1.0, 0.8]            # 이동 속도


# ──────────────────────────────────────────────
# 연구/기술
# ──────────────────────────────────────────────
RESEARCH_BASIC_BIAS = 0.4          # 기초 기술 선택 편향 확률
TECH_PIONEER_CHANCE = 0.1          # 기술 발견 시 선구자 즉시 학습 확률


# ──────────────────────────────────────────────
# 파벌
# ──────────────────────────────────────────────
FACTION_FORM_CHANCE = 0.3          # 매 틱 파벌 결성 시도 확률


# ──────────────────────────────────────────────
# 랜덤 이벤트 시스템
# ──────────────────────────────────────────────
EVENT_BASE_PROBABILITY = 0.02        # 매 틱 이벤트 발생 확률 (2%)
EVENT_MAX_ACTIVE = 3                  # 동시에 활성화될 수 있는 최대 이벤트 수
EVENT_MIN_INTERVAL = 10              # 이벤트 간 최소 틱 간격
EVENT_RADIUS_MIN = 3                  # 이벤트 최소 반경
EVENT_RADIUS_MAX = 8                  # 이벤트 최대 반경
EVENT_DURATION_MIN = 10              # 이벤트 최소 지속 틱
EVENT_DURATION_MAX = 25              # 이벤트 최대 지속 틱
EVENT_SEVERITY_MIN = 0.3             # 이벤트 최소 심각도
EVENT_SEVERITY_MAX = 1.0             # 이벤트 최대 심각도


# ──────────────────────────────────────────────
# 건설 시스템
# ──────────────────────────────────────────────
from dataclasses import dataclass, field


@dataclass
class BuildingDef:
    name: str
    description: str
    cost: dict[str, float]
    effects: dict
    max_per_entity: int = 1
    tech_required: str = ""


BUILDING_DEFS: list[BuildingDef] = [
    BuildingDef("storehouse", "저장고 — 인벤토리 +5칸, 식량 저장 한도 +10",
                {"wood": 5, "stone": 3},
                {"max_inventory": 5, "max_food_storage": 10.0}),
    BuildingDef("watchtower", "감시탑 — 탐험 범위 +2, 주변 개체 탐지 반경 +1",
                {"wood": 5, "stone": 5},
                {"explore_range": 2, "detection_radius": 1}),
    BuildingDef("wall", "벽 — 영토 전투 시 방어력 +30%",
                {"stone": 8, "wood": 3},
                {"defense_bonus": 0.3}),
    BuildingDef("forge", "대장간 — 제작 효율 +50%, 철 레시피 비용 -1",
                {"stone": 5, "iron": 3},
                {"craft_efficiency": 0.5, "iron_cost_discount": 1.0}),
    BuildingDef("shrine", "제단 — 사회성 +0.2, 지식 전수율 +20%",
                {"wood": 3, "stone": 2, "gold": 1},
                {"sociability_bonus": 0.2, "knowledge_transfer_boost": 0.2}),
]

BUILDING_DESTROY_CHANCE = 0.05  # 전투/재해 시 건물 파괴 확률


# ──────────────────────────────────────────────
# 외교 시스템 (Phase 2.1)
# ──────────────────────────────────────────────
DIPLOMACY_ENABLED = True
ALLIANCE_BREAK_COHESION = 0.2        # 동맹 파기 시 결속력 감소량
TRADE_PACT_TAX_DISCOUNT = 0.5        # 무역 협정 시 거래 수수료 할인율
VASSAL_TRIBUTE_RATIO = 0.1           # 종속 파벌의 자원 상납 비율
ALLIANCE_COMBAT_BONUS = 0.05         # 동맹 전투 보너스 추가
DIPLOMACY_RELATION_DECAY = 100       # 우호 관계 자동 악화 틱 간격
NON_AGGRESSION_COMBAT_SCORE = 0.0    # 불가침 조약 시 전투 점수 강제


# ──────────────────────────────────────────────
# 시각화
# ──────────────────────────────────────────────
TICK_INTERVAL_MS = 100  # 메인 루프 지연 (ms), 0이면 최대 속도
VISUALIZER_REFRESH_TICKS = 5  # n틱마다 화면 갱신


# ──────────────────────────────────────────────
# RNG 팩토리 — 시드 기반 난수 생성기
# ──────────────────────────────────────────────
def create_rng(seed: int | None = None, subsystem: str = "") -> random.Random:
    """시드 기반 RNG 인스턴스 생성.
    
    Args:
        seed: 기본 시드 (None이면 config.SEED 사용)
        subsystem: 서브시스템 식별자 (동일 시드여도 서브시스템마다 다른 RNG 보장)
    """
    base = seed if seed is not None else SEED
    if subsystem:
        # 동일 메인 시드여도 서브시스템별로 다른 RNG 생성
        sub_seed = hash((base, subsystem)) % (2**31 - 1)
        return random.Random(sub_seed)
    return random.Random(base)
