"""QuadTree 공간 인덱싱 테스트."""

from __future__ import annotations

from sim.spatial import QuadTree, Point


def test_quadtree_creation():
    """QuadTree 생성 테스트."""
    qt = QuadTree(40, 30)
    assert qt.width == 40
    assert qt.height == 30
    assert qt.points == []
    assert qt.children == []
    assert qt.divided is False


def test_quadtree_insert_single():
    """단일 점 삽입 테스트."""
    qt = QuadTree(40, 30)
    point = Point(10.0, 15.0, entity_id=1)
    
    result = qt.insert(point)
    
    assert result is True
    assert len(qt.points) == 1
    assert qt.points[0].entity_id == 1


def test_quadtree_insert_multiple():
    """여러 점 삽입 테스트 (분할 없이)."""
    qt = QuadTree(40, 30)
    
    for i in range(5):
        qt.insert(Point(float(i * 5), float(i * 3), entity_id=i))
    
    assert len(qt.points) == 5
    assert qt.divided is False


def test_quadtree_insert_divides():
    """점 수 초과 시 분할 테스트."""
    qt = QuadTree(40, 30)
    
    # 8개 이상 삽입하면 분할 발생
    for i in range(10):
        qt.insert(Point(float(i), float(i), entity_id=i))
    
    assert qt.divided is True
    assert len(qt.points) == 0  # 리프에는 점 없음


def test_quadtree_query_range():
    """범위 검색 테스트."""
    qt = QuadTree(40, 30)
    
    # 점 삽입
    qt.insert(Point(5.0, 5.0, entity_id=1))
    qt.insert(Point(15.0, 15.0, entity_id=2))
    qt.insert(Point(25.0, 25.0, entity_id=3))
    qt.insert(Point(35.0, 35.0, entity_id=4))
    
    # 범위 검색 (10x10 영역)
    result = qt.query_range(0.0, 0.0, 10.0, 10.0)
    
    assert len(result) == 1
    assert result[0].entity_id == 1


def test_quadtree_query_radius():
    """반경 검색 테스트 (맨해튼 거리)."""
    qt = QuadTree(40, 30)
    
    # 점 삽입
    qt.insert(Point(10.0, 10.0, entity_id=1))
    qt.insert(Point(12.0, 10.0, entity_id=2))  # 맨해튼 거리 2
    qt.insert(Point(15.0, 10.0, entity_id=3))  # 맨해튼 거리 5
    qt.insert(Point(20.0, 20.0, entity_id=4))  # 맨해튼 거리 20
    
    # 반경 5로 검색
    result = qt.query_radius(10.0, 10.0, 5.0)
    
    assert len(result) == 3  # entity_id 1, 2, 3


def test_quadtree_out_of_bounds():
    """영역 밖 점 삽입 무시 테스트."""
    qt = QuadTree(40, 30)
    
    result = qt.insert(Point(50.0, 50.0, entity_id=1))
    
    assert result is False
    assert len(qt.points) == 0


def test_quadtree_clear():
    """QuadTree 초기화 테스트."""
    qt = QuadTree(40, 30)
    
    # 점 삽입
    for i in range(10):
        qt.insert(Point(float(i), float(i), entity_id=i))
    
    assert qt.divided is True
    
    # 초기화
    qt.clear()
    
    assert qt.points == []
    assert qt.children == []
    assert qt.divided is False


def test_quadtree_query_empty():
    """빈 QuadTree 검색 테스트."""
    qt = QuadTree(40, 30)
    
    result = qt.query_range(0.0, 0.0, 10.0, 10.0)
    
    assert len(result) == 0
