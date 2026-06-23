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


# ──────────────────────────────────────────────
# 지니계수 / 통계
# ──────────────────────────────────────────────
METRICS_SNAPSHOT_INTERVAL = 10   # n틱마다 스냅샷 저장
WORLD_LOG_INTERVAL = 50          # n틱마다 월드 상태 로그


# ──────────────────────────────────────────────
# 파벌 (Faction)
# ──────────────────────────────────────────────
FACTION_ENABLED = True
FACTION_FORMATION_SOCIABILITY = 0.55  # 파벌 결성에 필요한 최소 사회성
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
SMART_BRAIN_RATIO = 0.25          # 전체 개체 중 SmartBrain 비율 (0.25 = 25%)
SMART_MEMORY_SIZE = 50            # 각 SmartBrain이 기억하는 최근 경험 수
SMART_SIMILARITY_THRESHOLD = 0.7  # 경험 참조를 위한 상태 유사도 임계값
SMART_PLANNING_RATE = 0.3         # 멀티스텝 계획 시도 확률 (매 결정마다)
SMART_PLANNING_DISCOUNT = 0.6     # 미래 액션 점수 할인율 (0~1, 높을수록 미래 중시)
SMART_LEARNING_RATE = 0.1         # 경험 보정의 학습률 (너무 높으면 불안정)


# ──────────────────────────────────────────────
# 시각화
# ──────────────────────────────────────────────
TICK_INTERVAL_MS = 100  # 메인 루프 지연 (ms), 0이면 최대 속도
VISUALIZER_REFRESH_TICKS = 5  # n틱마다 화면 갱신
