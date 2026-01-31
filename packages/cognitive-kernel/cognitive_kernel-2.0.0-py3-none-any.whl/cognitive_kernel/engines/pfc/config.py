from dataclasses import dataclass


@dataclass
class PFCConfig:
    """PFC Engine v1.0 설정값.

    - working_memory_capacity: 작업 기억 용량 (Miller's Law: 7±2)
    - decay_rate: 작업 기억 감쇠율 (λ)
    - risk_aversion: 위험 회피 계수 (κ)
    - inhibition_threshold: 억제 임계값
    - decision_temperature: Softmax 온도 (β), 높을수록 최적 선택 확률 증가
    """

    working_memory_capacity: int = 7
    decay_rate: float = 0.1
    risk_aversion: float = 0.5
    inhibition_threshold: float = 0.7
    decision_temperature: float = 1.0
