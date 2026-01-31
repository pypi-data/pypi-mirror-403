"""
🧠 Cognitive Kernel - 통합 인지 엔진 (Complete Long-term Memory)

진짜 장기 기억 시스템:
- 자동 세션 관리 (with 문 지원)
- 자동 저장/로드
- 7개 엔진 통합 인터페이스
- Edge AI First 설계

사용 예시:
    # 기본 사용
    from cognitive_kernel import CognitiveKernel
    
    kernel = CognitiveKernel("my_brain")
    kernel.remember("meeting", {"topic": "project"}, importance=0.9)
    kernel.save()
    
    # 컨텍스트 매니저 (자동 저장)
    with CognitiveKernel("my_brain") as kernel:
        kernel.remember("idea", {"content": "great idea"})
        decision = kernel.decide(["rest", "work", "exercise"])
    # 자동 저장됨

Author: GNJz (Qquarts)
Version: 2.0.0
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# 엔진 임포트
from .engines.panorama import PanoramaMemoryEngine, PanoramaConfig
from .engines.memoryrank import MemoryRankEngine, MemoryRankConfig, MemoryNodeAttributes
from .engines.pfc import PFCEngine, PFCConfig, Action
from .engines.basal_ganglia import BasalGangliaEngine, BasalGangliaConfig


@dataclass
class CognitiveConfig:
    """Cognitive Kernel 설정"""
    
    # 저장 경로
    storage_dir: str = ".cognitive_kernel"
    
    # 자동 저장 설정
    auto_save: bool = True
    auto_save_interval: int = 100  # n개 이벤트마다 자동 저장
    
    # 엔진 설정
    working_memory_capacity: int = 7  # Miller's Law
    recency_half_life: float = 3600.0  # 1시간
    
    # PageRank 설정
    damping: float = 0.85
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "storage_dir": self.storage_dir,
            "auto_save": self.auto_save,
            "auto_save_interval": self.auto_save_interval,
            "working_memory_capacity": self.working_memory_capacity,
            "recency_half_life": self.recency_half_life,
            "damping": self.damping,
        }


class CognitiveKernel:
    """
    🧠 Cognitive Kernel - 통합 인지 엔진
    
    7개 모듈 통합:
    - Panorama: 시간축 기억 (필름)
    - MemoryRank: 중요도 랭킹 (조광기)
    - PFC: 의사결정 (감독)
    - BasalGanglia: 습관 학습 (스태프)
    
    진짜 장기 기억:
    - 자동 저장/로드
    - 세션 관리
    - 프로세스 종료 후에도 기억 유지
    """
    
    def __init__(
        self,
        session_name: str = "default",
        config: Optional[CognitiveConfig] = None,
        auto_load: bool = True,
    ):
        """
        Args:
            session_name: 세션 이름 (저장 파일 이름으로 사용)
            config: 설정 객체
            auto_load: True면 기존 세션 자동 로드
        """
        self.session_name = session_name
        self.config = config or CognitiveConfig()
        
        # 저장 경로 설정
        self.storage_path = Path(self.config.storage_dir) / session_name
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 엔진 초기화
        self._init_engines()
        
        # 상태
        self._event_count = 0
        self._is_dirty = False
        self._edges: List[Tuple[str, str, float]] = []
        
        # 자동 로드
        if auto_load and self._session_exists():
            self.load()
    
    def _init_engines(self):
        """엔진 초기화"""
        # Panorama (시간축 기억)
        self.panorama = PanoramaMemoryEngine(PanoramaConfig(
            recency_half_life=self.config.recency_half_life,
        ))
        
        # MemoryRank (중요도 랭킹)
        self.memoryrank = MemoryRankEngine(MemoryRankConfig(
            damping=self.config.damping,
        ))
        
        # PFC (의사결정)
        self.pfc = PFCEngine(PFCConfig(
            working_memory_capacity=self.config.working_memory_capacity,
        ))
        
        # BasalGanglia (습관 학습)
        self.basal_ganglia = BasalGangliaEngine(BasalGangliaConfig())
        
        # 클래스 참조 저장
        self._MemoryNodeAttributes = MemoryNodeAttributes
        self._Action = Action
    
    # ==================================================================
    # 핵심 인터페이스 - 간단하게 사용
    # ==================================================================
    
    def remember(
        self,
        event_type: str,
        content: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        emotion: float = 0.0,
        related_to: Optional[List[str]] = None,
    ) -> str:
        """
        기억 저장 (장기 기억)
        
        Args:
            event_type: 이벤트 종류 (예: "meeting", "idea", "conversation")
            content: 이벤트 내용
            importance: 중요도 (0~1)
            emotion: 감정 강도 (0~1)
            related_to: 연관된 기억 ID 리스트
            
        Returns:
            생성된 기억 ID
            
        Example:
            >>> kernel.remember("meeting", {"topic": "project"}, importance=0.9)
            >>> kernel.remember("idea", {"content": "new feature"}, related_to=["meeting_id"])
        """
        timestamp = time.time()
        
        # Panorama에 이벤트 저장
        event_id = self.panorama.append_event(
            timestamp=timestamp,
            event_type=event_type,
            payload=content or {},
            importance=importance,
        )
        
        # 연관 관계 저장 (MemoryRank 그래프용)
        if related_to:
            for related_id in related_to:
                self._edges.append((related_id, event_id, importance))
                self._edges.append((event_id, related_id, importance * 0.5))  # 양방향 (비대칭)
        
        # 메타데이터 저장
        self._event_count += 1
        self._is_dirty = True
        
        # 자동 저장 체크
        if self.config.auto_save and self._event_count % self.config.auto_save_interval == 0:
            self.save()
        
        return event_id
    
    def recall(self, k: int = 5) -> List[Dict[str, Any]]:
        """
        중요한 기억 회상 (Top-k)
        
        Args:
            k: 회상할 기억 수
            
        Returns:
            중요도 순으로 정렬된 기억 리스트
            
        Example:
            >>> memories = kernel.recall(k=5)
            >>> for m in memories:
            ...     print(f"{m['event_type']}: {m['importance']:.2f}")
        """
        # MemoryRank 그래프 구축
        self._rebuild_graph()
        
        # Top-k 조회
        top_memories = self.memoryrank.get_top_memories(k)
        
        # 이벤트 정보 추가
        results = []
        for event_id, score in top_memories:
            event = self.panorama.get_event(event_id)
            if event:
                results.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "content": event.payload,
                    "importance": score,
                    "timestamp": event.timestamp,
                })
        
        return results
    
    def decide(
        self,
        options: List[str],
        context: Optional[str] = None,
        use_habit: bool = True,
    ) -> Dict[str, Any]:
        """
        의사결정 (PFC + BasalGanglia)
        
        Args:
            options: 행동 후보 리스트
            context: 상황 컨텍스트
            use_habit: True면 습관 학습 결과도 반영
            
        Returns:
            결정 결과
            
        Example:
            >>> result = kernel.decide(["rest", "work", "exercise"])
            >>> print(f"Decision: {result['action']}")
        """
        # 기억 로드 → Working Memory
        memories = self.recall(k=self.config.working_memory_capacity)
        
        # MemoryRank 결과를 PFC Working Memory에 로드
        top_memories_tuples = [(m["id"], m["importance"]) for m in memories]
        self.pfc.load_from_memoryrank(top_memories_tuples)
        
        # Action 생성
        actions = []
        for i, opt in enumerate(options):
            # 기본 효용 (실제로는 더 정교한 계산 필요)
            actions.append(self._Action(
                id=f"action_{i}",
                name=opt,
                expected_reward=0.5,
                effort_cost=0.2,
                risk=0.1,
            ))
        
        # PFC 결정
        pfc_result = self.pfc.process(actions)
        
        # 습관 반영
        habit_action = None
        if use_habit and context:
            habit_action = self.basal_ganglia.select_action(context, options)
        
        return {
            "action": pfc_result.action.name if pfc_result.action else None,
            "utility": pfc_result.utility,
            "probability": pfc_result.selection_probability,
            "habit_suggestion": habit_action,
            "conflict": pfc_result.action.name != habit_action if (pfc_result.action and habit_action) else False,
        }
    
    def learn_from_reward(
        self,
        context: str,
        action: str,
        reward: float,
    ):
        """
        보상 학습 (습관 형성)
        
        Args:
            context: 상황
            action: 수행한 행동
            reward: 보상 값 (0~1)
            
        Example:
            >>> kernel.learn_from_reward("tired", "rest", reward=0.8)
        """
        self.basal_ganglia.update(context, action, reward)
        self._is_dirty = True
    
    def _rebuild_graph(self):
        """MemoryRank 그래프 재구축"""
        events = self.panorama.get_all_events()
        
        # 이벤트가 없으면 종료
        if not events:
            return
        
        # 엣지가 없으면 시간 순서로 연결
        if not self._edges:
            for i in range(len(events) - 1):
                self._edges.append((events[i].id, events[i+1].id, 0.5))
            # 이벤트가 1개뿐이면 자기 자신으로 연결
            if len(events) == 1:
                self._edges.append((events[0].id, events[0].id, 1.0))
        
        # 노드 속성 생성
        recency_scores = self.panorama.get_recency_scores()
        node_attrs = {}
        
        for event in events:
            node_attrs[event.id] = self._MemoryNodeAttributes(
                recency=recency_scores.get(event.id, 0.5),
                emotion=event.payload.get("emotion", 0.0) if event.payload else 0.0,
                frequency=1.0,
                base_importance=event.importance,
            )
        
        # 그래프 구축
        if self._edges and node_attrs:
            self.memoryrank.build_graph(self._edges, node_attrs)
            self.memoryrank.calculate_importance()
    
    # ==================================================================
    # 영속성 (장기 기억의 핵심)
    # ==================================================================
    
    def save(self) -> Dict[str, int]:
        """
        세션 저장 (장기 기억)
        
        Returns:
            저장 통계
        """
        stats = {}
        
        # Panorama 저장
        panorama_path = self.storage_path / "panorama.json"
        stats["events"] = self.panorama.save_to_json(str(panorama_path))
        
        # MemoryRank 저장
        if self.memoryrank._M is not None:
            memoryrank_path = self.storage_path / "memoryrank.json"
            result = self.memoryrank.save_to_json(str(memoryrank_path))
            stats["nodes"] = result["nodes"]
        
        # Edges 저장
        edges_path = self.storage_path / "edges.json"
        edges_path.write_text(json.dumps(self._edges, indent=2))
        stats["edges"] = len(self._edges)
        
        # BasalGanglia Q-values 저장
        q_path = self.storage_path / "q_values.json"
        q_data = {}
        if hasattr(self.basal_ganglia, '_q_table'):
            q_data = {k: dict(v) for k, v in self.basal_ganglia._q_table.items()}
        q_path.write_text(json.dumps(q_data, indent=2))
        
        # 메타데이터 저장
        meta_path = self.storage_path / "meta.json"
        meta_path.write_text(json.dumps({
            "session_name": self.session_name,
            "event_count": self._event_count,
            "last_saved": time.time(),
            "config": self.config.to_dict(),
        }, indent=2))
        
        self._is_dirty = False
        return stats
    
    def load(self) -> Dict[str, int]:
        """
        세션 로드 (장기 기억 복구)
        
        Returns:
            로드 통계
        """
        stats = {}
        
        # Panorama 로드
        panorama_path = self.storage_path / "panorama.json"
        if panorama_path.exists():
            stats["events"] = self.panorama.load_from_json(str(panorama_path))
        
        # MemoryRank 로드
        memoryrank_path = self.storage_path / "memoryrank.json"
        if memoryrank_path.exists():
            result = self.memoryrank.load_from_json(str(memoryrank_path))
            stats["nodes"] = result["nodes"]
        
        # Edges 로드
        edges_path = self.storage_path / "edges.json"
        if edges_path.exists():
            self._edges = json.loads(edges_path.read_text())
            stats["edges"] = len(self._edges)
        
        # BasalGanglia Q-values 로드
        q_path = self.storage_path / "q_values.json"
        if q_path.exists():
            q_data = json.loads(q_path.read_text())
            if hasattr(self.basal_ganglia, '_q_table'):
                from collections import defaultdict
                self.basal_ganglia._q_table = defaultdict(
                    lambda: defaultdict(float),
                    {k: defaultdict(float, v) for k, v in q_data.items()}
                )
        
        # 메타데이터 로드
        meta_path = self.storage_path / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            self._event_count = meta.get("event_count", 0)
        
        self._is_dirty = False
        return stats
    
    def _session_exists(self) -> bool:
        """세션 파일 존재 여부"""
        return (self.storage_path / "meta.json").exists()
    
    # ==================================================================
    # 컨텍스트 매니저 (자동 저장)
    # ==================================================================
    
    def __enter__(self) -> "CognitiveKernel":
        """with 문 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 문 종료 - 자동 저장"""
        if self._is_dirty:
            self.save()
        return False
    
    # ==================================================================
    # 유틸리티
    # ==================================================================
    
    def status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            "session_name": self.session_name,
            "storage_path": str(self.storage_path),
            "event_count": len(self.panorama),
            "edge_count": len(self._edges),
            "is_dirty": self._is_dirty,
            "auto_save": self.config.auto_save,
        }
    
    def clear(self):
        """모든 기억 삭제 (주의!)"""
        self.panorama.clear()
        self._edges.clear()
        self._event_count = 0
        self._is_dirty = True
    
    def __repr__(self) -> str:
        return f"CognitiveKernel(session='{self.session_name}', events={len(self.panorama)})"
    
    def __len__(self) -> int:
        return len(self.panorama)


# ==================================================================
# 편의 함수
# ==================================================================

def create_kernel(session_name: str = "default", **kwargs) -> CognitiveKernel:
    """CognitiveKernel 생성 편의 함수"""
    config = CognitiveConfig(**kwargs)
    return CognitiveKernel(session_name, config)

