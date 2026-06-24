"""공간 인덱싱 — QuadTree 기반 효율적인 이웃 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Point:
    """2D 점 — 개체의 위치를 나타냄."""
    x: float
    y: float
    entity_id: int = -1  # 개체 ID (선택적)


class QuadTree:
    """QuadTree 공간 인덱싱 — O(n log n) 이웃 검색.
    
    40×30 월드에 최적화된 그리드 기반 인덱싱.
    매 틱마다 모든 개체를 순회하는 O(n²) 문제를 해결합니다.
    """
    
    MAX_POINTS = 8  # 리프 노드 최대 점 수
    MAX_DEPTH = 8   # 최대 깊이
    
    def __init__(self, width: float, height: float, 
                 x: float = 0.0, y: float = 0.0,
                 depth: int = 0):
        """QuadTree 초기화.
        
        Args:
            width: 영역 너비
            height: 영역 높이
            x: 영역 시작 x 좌표
            y: 영역 시작 y 좌표
            depth: 현재 깊이
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.depth = depth
        self.points: list[Point] = []
        self.children: list[QuadTree] = []
        self.divided = False
    
    def _contains(self, point: Point) -> bool:
        """점이 이 노드 영역에 포함되는지 확인."""
        return (self.x <= point.x < self.x + self.width and
                self.y <= point.y < self.y + self.height)
    
    def _intersects(self, x: float, y: float, w: float, h: float) -> bool:
        """주어진 영역이 이 노드와 교차하는지 확인."""
        return not (x + w <= self.x or x >= self.x + self.width or
                    y + h <= self.y or y >= self.y + self.height)
    
    def _divide(self) -> None:
        """4개 자식 노드로 분할."""
        if self.divided:
            return
        
        half_w = self.width / 2
        half_h = self.height / 2
        
        self.children = [
            QuadTree(half_w, half_h, self.x, self.y, self.depth + 1),           # NW
            QuadTree(half_w, half_h, self.x + half_w, self.y, self.depth + 1),  # NE
            QuadTree(half_w, half_h, self.x, self.y + half_h, self.depth + 1),  # SW
            QuadTree(half_w, half_h, self.x + half_w, self.y + half_h, self.depth + 1),  # SE
        ]
        self.divided = True
    
    def insert(self, point: Point) -> bool:
        """점 삽입.
        
        Args:
            point: 삽입할 점
            
        Returns:
            삽입 성공 여부
        """
        # 영역 밖이면 무시
        if not self._contains(point):
            return False
        
        # 리프 노드이고 점 수가 제한 미만이면 직접 저장
        if not self.divided and len(self.points) < self.MAX_POINTS:
            self.points.append(point)
            return True
        
        # 분할이 필요하면 분할
        if not self.divided:
            if self.depth >= self.MAX_DEPTH:
                # 최대 깊이 도달 시 그냥 추가
                self.points.append(point)
                return True
            self._divide()
            # 기존 점들을 자식으로 이동
            for p in self.points:
                for child in self.children:
                    if child.insert(p):
                        break
            self.points = []
        
        # 자식에게 삽입 시도
        for child in self.children:
            if child.insert(point):
                return True
        
        return False
    
    def query_range(self, x: float, y: float, w: float, h: float) -> list[Point]:
        """범위 내 점 검색.
        
        Args:
            x: 검색 영역 시작 x
            y: 검색 영역 시작 y
            w: 검색 영역 너비
            h: 검색 영역 높이
            
        Returns:
            범위 내 점들의 리스트
        """
        result: list[Point] = []
        
        # 영역이 교차하지 않으면 반환
        if not self._intersects(x, y, w, h):
            return result
        
        # 리프 노드: 점들을 확인
        if not self.divided:
            for point in self.points:
                if x <= point.x < x + w and y <= point.y < y + h:
                    result.append(point)
            return result
        
        # 자식 노드에서 재귀 검색
        for child in self.children:
            result.extend(child.query_range(x, y, w, h))
        
        return result
    
    def query_radius(self, cx: float, cy: float, radius: float) -> list[Point]:
        """반경 내 점 검색 (맨해튼 거리).
        
        Args:
            cx: 중심 x 좌표
            cy: 중심 y 좌표
            radius: 검색 반경
            
        Returns:
            반경 내 점들의 리스트
        """
        # 반경을 포함하는 사각형으로 범위 검색 후 필터링
        # 경계선 점을 포함하도록 약간의 여유 추가
        margin = 0.001
        points = self.query_range(
            cx - radius - margin, cy - radius - margin,
            radius * 2 + margin * 2, radius * 2 + margin * 2
        )
        
        # 맨해튼 거리로 필터링
        return [p for p in points 
                if abs(p.x - cx) + abs(p.y - cy) <= radius]
    
    def clear(self) -> None:
        """QuadTree 초기화."""
        self.points = []
        self.children = []
        self.divided = False
