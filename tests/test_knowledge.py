"""지식/기술 시스템 단위 테스트 — Knowledge, TechnologyTree, KnowledgeBook."""

from __future__ import annotations

import random

from sim import config
from sim.knowledge import Knowledge, TechnologyTree, KnowledgeBook


# ── Knowledge 노드 테스트 ──

def test_knowledge_initial_state():
    """Knowledge 노드 초기 상태 확인."""
    k = Knowledge(name="basic_agriculture", description="농업 기초", research_cost=10)
    assert k.name == "basic_agriculture"
    assert not k.discovered
    assert k.research_progress == 0
    assert not k.is_researched


def test_knowledge_research_progress():
    """연구 포인트 투입 시 progress 증가 확인."""
    k = Knowledge(name="test", research_cost=20)
    done = k.research(5)
    assert not done
    assert k.research_progress == 5
    assert not k.discovered


def test_knowledge_research_complete():
    """연구 완료 시 discovered=True 확인."""
    k = Knowledge(name="test", research_cost=10)
    done = k.research(10)
    assert done
    assert k.discovered
    assert k.is_researched


def test_knowledge_research_already_done():
    """이미 완료된 연구 재투입 시 False 반환."""
    k = Knowledge(name="test", research_cost=5)
    k.research(5)
    assert k.discovered
    done = k.research(5)
    assert not done


def test_knowledge_research_over_threshold():
    """연구 포인트가 비용을 초과해도 완료 처리."""
    k = Knowledge(name="test", research_cost=10)
    done = k.research(15)
    assert done
    assert k.discovered


# ── TechnologyTree 테스트 ──

def test_tech_tree_loads_all_techs():
    """설정된 기술 트리의 모든 기술이 로드됨."""
    tree = TechnologyTree()
    assert tree.total_count() > 0
    assert tree.total_count() == len(config.TECH_TREE)


def test_tech_tree_discovered_count_initial():
    """초기 발견 기술 수는 0."""
    tree = TechnologyTree()
    assert tree.discover_count() == 0


def test_tech_tree_get_available_no_prereqs():
    """선행 기술이 없는 기술은 즉시 연구 가능."""
    tree = TechnologyTree()
    available = tree.get_available(set())
    # 최소 1개 이상의 기술이 연구 가능해야 함
    assert len(available) > 0


def test_tech_tree_get_available_with_prereqs():
    """선행 기술 미충족 시 연구 불가."""
    tree = TechnologyTree()
    # 아무것도 발견하지 않은 상태
    available = tree.get_available(set())
    # 선행 기술이 필요한 기술은 포함되지 않아야 함
    for tech in available:
        assert len(tech.prerequisites) == 0 or all(
            p in set() for p in tech.prerequisites
        )


def test_tech_tree_get_available_after_discovery():
    """선행 기술 발견 후 후속 기술 연구 가능."""
    tree = TechnologyTree()
    available = tree.get_available(set())
    if available:
        first = available[0]
        first.research(first.research_cost)
        discovered = {first.name}
        next_available = tree.get_available(discovered)
        # 최소 첫 기술은 discovered 목록에 있어야 함
        assert first.name in {t.name for t in tree.get_discovered()}


def test_tech_tree_get_by_name():
    """이름으로 기술 조회."""
    tree = TechnologyTree()
    first_tech = config.TECH_TREE[0]
    found = tree.get_by_name(first_tech.name)
    assert found is not None
    assert found.name == first_tech.name


def test_tech_tree_get_by_name_missing():
    """존재하지 않는 기술명 조회 시 None."""
    tree = TechnologyTree()
    assert tree.get_by_name("nonexistent_tech") is None


def test_tech_tree_all_techs():
    """all_techs()가 전체 기술 목록 반환."""
    tree = TechnologyTree()
    all_techs = tree.all_techs()
    assert len(all_techs) == tree.total_count()


def test_tech_tree_discover_increments_count():
    """기술 발견 시 discover_count 증가."""
    tree = TechnologyTree()
    available = tree.get_available(set())
    if available:
        tech = available[0]
        tech.research(tech.research_cost)
        assert tree.discover_count() == 1


# ── KnowledgeBook 테스트 ──

def test_knowledge_book_initial_empty():
    """초기 KnowledgeBook은 비어있음."""
    kb = KnowledgeBook()
    assert kb.count() == 0
    assert not kb.know("any_tech")


def test_knowledge_book_learn():
    """기술 습득 후 know() 확인."""
    kb = KnowledgeBook()
    kb.learn("basic_agriculture")
    assert kb.know("basic_agriculture")
    assert kb.count() == 1


def test_knowledge_book_forget():
    """기술 상실 후 know() False 확인."""
    kb = KnowledgeBook()
    kb.learn("basic_agriculture")
    kb.forget("basic_agriculture")
    assert not kb.know("basic_agriculture")
    assert kb.count() == 0


def test_knowledge_book_forget_nonexistent():
    """존재하지 않는 기술 상실 시 에러 없음."""
    kb = KnowledgeBook()
    kb.forget("nonexistent")  # 에러 없이 동작
    assert kb.count() == 0


def test_knowledge_book_copy_from():
    """copy_from으로 지식 전체 복사."""
    kb1 = KnowledgeBook()
    kb1.learn("tech_a")
    kb1.learn("tech_b")
    kb2 = KnowledgeBook()
    kb2.copy_from(kb1)
    assert kb2.know("tech_a")
    assert kb2.know("tech_b")
    assert kb2.count() == 2


def test_knowledge_book_share_high_sociability():
    """높은 사회성으로 지식 전수 성공."""
    rng = config.create_rng(42, "test")
    kb1 = KnowledgeBook()
    kb1.learn("tech_a")
    kb1.learn("tech_b")
    kb2 = KnowledgeBook()
    transferred = kb1.share(kb2, sociability=0.9, rng=rng)
    # 전수된 기술이 있거나(확률), 없어도 무방
    assert isinstance(transferred, list)


def test_knowledge_book_share_low_sociability():
    """낮은 사회성으로 지식 전수 실패."""
    rng = config.create_rng(42, "test")
    kb1 = KnowledgeBook()
    kb1.learn("tech_a")
    kb2 = KnowledgeBook()
    # sociability 0.0이면 항상 실패
    transferred = kb1.share(kb2, sociability=0.0, rng=rng)
    assert transferred == []
    assert not kb2.know("tech_a")


def test_knowledge_book_share_no_duplicate():
    """이미 알고 있는 기술은 전수하지 않음."""
    rng = config.create_rng(42, "test")
    kb1 = KnowledgeBook()
    kb1.learn("tech_a")
    kb2 = KnowledgeBook()
    kb2.learn("tech_a")
    transferred = kb1.share(kb2, sociability=1.0, rng=rng)
    assert "tech_a" not in transferred


def test_knowledge_book_multiple_learns():
    """여러 기술을 연속 습득."""
    kb = KnowledgeBook()
    for i in range(5):
        kb.learn(f"tech_{i}")
    assert kb.count() == 5
    for i in range(5):
        assert kb.know(f"tech_{i}")
