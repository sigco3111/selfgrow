"""전체 시뮬레이션 파라미터 — 모든 튜너블 상수는 여기서 관리."""

from dataclasses import dataclass
from typing import ClassVar


# ──────────────────────────────────────────────
# 월드
# ──────────────────────────────────────────────
WORLD_WIDTH = 40
WORLD_HEIGHT = 30
SEED = 42                  # 난수 시드 (재현성)

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
INITIAL_ENTITY_COUNT = 40

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

TECH_TREE: list[TechDef] = [
    TechDef("basic_agriculture", "농업 기초 - 식량 생산 +1/tick",
            [], 20, {"gather_food": 1.5}),
    TechDef("mining", "채광 기술 - 돌/철 생산 +1/tick",
            [], 20, {"gather_stone": 1.5, "gather_iron": 1.5}),
    TechDef("metallurgy", "야금술 - 철 도구 제작 가능",
            ["mining"], 40, {"craft_iron_sword": True}),
    TechDef("currency", "화폐 도입 - 시장 효율 +20%",
            ["basic_agriculture"], 30, {"trade_efficiency": 0.2}),
    TechDef("irrigation", "관개 - 모든 농업 생산 +50%",
            ["basic_agriculture"], 35, {"gather_food": 2.0}),
    TechDef("architecture", "건축 - 방어력 +3",
            ["mining"], 30, {"defense": 3.0}),
    TechDef("alchemy", "연금술 - 금 가치 2배",
            ["metallurgy"], 50, {"gold_value_mult": 2.0}),
    TechDef("sailing", "항해 - 물 타일 통과 가능",
            ["basic_agriculture"], 25, {"cross_water": True}),
    TechDef("bureaucracy", "관료제 - 조직 결성 가능",
            ["currency"], 40, {"organization": True}),
]


# ──────────────────────────────────────────────
# 지니계수 / 통계
# ──────────────────────────────────────────────
METRICS_SNAPSHOT_INTERVAL = 10   # n틱마다 스냅샷 저장
WORLD_LOG_INTERVAL = 50          # n틱마다 월드 상태 로그


# ──────────────────────────────────────────────
# 시각화
# ──────────────────────────────────────────────
TICK_INTERVAL_MS = 100  # 메인 루프 지연 (ms), 0이면 최대 속도
VISUALIZER_REFRESH_TICKS = 5  # n틱마다 화면 갱신
