#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emotion Curve Validator

감정 곡선 검증 엔진: 50초 세일즈 스크립트의 감정 흐름을 검증
세일즈맨처럼 처음부터 끝까지 감정을 끌고가는 설계 검증

Design Philosophy:
- Hook (0-3s): 불안/긴급성 → 시선 강탈
- Pain Point (3-8s): 공감 → 문제 인식
- Solution (8-15s): 호기심 → 해결책 제시
- Value Proof (15-30s): 열망 → 가치 증명
- Affinity (30-40s): 확신 → 감정 피크
- CTA (40-50s): 행동 유발 → 전환

References:
- Learning_Data/심리적4단계_구조.md (감정 강도 곡선)
- engines/comprehensive_script_generator.py (EMOTION_SCORES)
"""

import re
import threading
from typing import Dict, List, Tuple
from collections import defaultdict

# Thread-safe cache
_emotion_cache = {}
_cache_lock = threading.Lock()


# 구간별 감정 목표 범위 (50초 구조)
EMOTION_TARGETS = {
    "hook": (0.25, 0.35),           # 0-3초: 불안/긴급성
    "pain_point": (0.45, 0.60),     # 3-8초: 공감
    "solution": (0.65, 0.75),       # 8-15초: 호기심
    "value_proof_1": (0.80, 0.90),  # 15-25초: 열망
    "value_proof_2": (0.85, 0.95),  # 25-30초: 열망 지속
    "affinity": (0.90, 1.00),       # 30-40초: 확신 (피크)
    "emotional_peak": (0.90, 1.00), # 감정 피크
    "cta": (0.85, 0.95),            # 40-50초: 행동 유발
    "narrowing": (0.75, 0.85),      # CTA 전 선택지 좁히기
    "offer": (0.80, 0.90),          # 제안
}


# 감정 키워드 가중치 (긍정=높음, 부정=낮음)
EMOTION_KEYWORDS = {
    # 불안/긴급성 (0.25-0.35)
    "불안": [
        ("모르면", 0.30), ("못 먹은", 0.28), ("놓칩니다", 0.32),
        ("걱정", 0.30), ("실수", 0.28), ("후회", 0.32),
    ],
    # 공감 (0.45-0.60)
    "공감": [
        ("그랬습니다", 0.55), ("이해합니다", 0.58), ("느껴집니다", 0.52),
        ("마음", 0.50), ("같은", 0.48), ("저도", 0.55),
    ],
    # 호기심 (0.65-0.75)
    "호기심": [
        ("비밀", 0.72), ("숨겨진", 0.70), ("놀라운", 0.68),
        ("특별한", 0.70), ("유일한", 0.72), ("처음", 0.68),
    ],
    # 열망 (0.80-0.95)
    "열망": [
        ("꿈", 0.88), ("버킷리스트", 0.92), ("인생", 0.85),
        ("최고", 0.82), ("완벽", 0.86), ("감동", 0.90),
    ],
    # 확신 (0.90-1.00)
    "확신": [
        ("보장", 0.95), ("믿을", 0.92), ("안전", 0.94),
        ("검증", 0.93), ("신뢰", 0.95), ("확실", 0.96),
    ],
    # 행동 (0.85-0.95)
    "행동": [
        ("지금", 0.90), ("바로", 0.88), ("오늘", 0.86),
        ("확인", 0.85), ("상담", 0.87), ("예약", 0.90),
    ],
}


# 금지 감정 키워드 (감점 요소)
NEGATIVE_KEYWORDS = {
    "약한_표현": [("같아요", -0.15), ("것 같아요", -0.20)],
    "불안_과잉": [("무서워", -0.25), ("두려워", -0.20)],
}


def calculate_segment_emotion(segment_type: str, text: str, trust_count: int = 0) -> float:
    """
    세그먼트 감정 점수 계산

    Args:
        segment_type: 세그먼트 타입 (hook, pain_point, solution 등)
        text: 세그먼트 텍스트
        trust_count: Trust 요소 개수 (가점)

    Returns:
        감정 점수 0.0-1.0
    """
    cache_key = f"{segment_type}:{text[:50]}:{trust_count}"

    with _cache_lock:
        if cache_key in _emotion_cache:
            return _emotion_cache[cache_key]

    # 기본 점수 (타입별)
    base_score = {
        "hook": 0.30,
        "pain_point": 0.50,
        "solution": 0.70,
        "value_proof_1": 0.85,
        "value_proof_2": 0.88,
        "affinity": 0.95,
        "emotional_peak": 0.98,
        "cta": 0.90,
    }.get(segment_type, 0.50)

    # 키워드 가중치 적용
    score = base_score
    for emotion_type, keywords in EMOTION_KEYWORDS.items():
        for keyword, weight in keywords:
            if keyword in text:
                score = (score + weight) / 2  # 평균으로 조정

    # 금지 키워드 감점
    for neg_type, keywords in NEGATIVE_KEYWORDS.items():
        for keyword, penalty in keywords:
            if keyword in text:
                score += penalty

    # Trust 요소 가점 (신뢰 → 확신 상승)
    if trust_count >= 2:
        score += 0.05

    # 범위 제한
    score = max(0.0, min(1.0, score))

    with _cache_lock:
        _emotion_cache[cache_key] = score

    return score


def validate_emotion_curve(segments: List[Dict]) -> Tuple[float, Dict]:
    """
    감정 곡선 검증

    Args:
        segments: 스크립트 세그먼트 리스트

    Returns:
        (점수 0-100, 상세 리포트)
    """
    if not segments:
        return 0.0, {"error": "No segments provided"}

    scores = []
    violations = []
    segment_scores = {}

    trust_count = sum(1 for seg in segments if seg.get("trust_element"))

    for i, segment in enumerate(segments):
        seg_type = segment.get("type", "unknown")
        text = segment.get("text", "")

        # 감정 점수 계산
        emotion_score = calculate_segment_emotion(seg_type, text, trust_count)
        scores.append(emotion_score)
        segment_scores[f"{i}_{seg_type}"] = emotion_score

        # 목표 범위 체크
        target_range = EMOTION_TARGETS.get(seg_type)
        if target_range:
            min_score, max_score = target_range
            if not (min_score <= emotion_score <= max_score):
                violations.append({
                    "segment": i,
                    "type": seg_type,
                    "score": emotion_score,
                    "expected": f"{min_score}-{max_score}",
                    "text_preview": text[:30] + "..."
                })

    # 감정 흐름 일관성 체크
    drops = []
    for i in range(1, len(scores)):
        drop = scores[i-1] - scores[i]
        if drop > 0.15:  # 급격한 하락 방지
            drops.append({
                "from_segment": i-1,
                "to_segment": i,
                "drop": round(drop, 2)
            })

    # 변동성 체크 (단조로움 방지)
    if len(scores) >= 3:
        variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
        if variance < 0.01:
            violations.append({
                "type": "low_variance",
                "variance": round(variance, 4),
                "message": "감정 곡선이 너무 평탄함 (단조로움)"
            })

    # 피크 타이밍 체크 (30-40초 구간)
    peak_score = max(scores)
    peak_index = scores.index(peak_score)
    peak_segment_type = segments[peak_index].get("type", "")

    ideal_peak_types = ["affinity", "emotional_peak", "value_proof_2"]
    if peak_segment_type not in ideal_peak_types:
        violations.append({
            "type": "peak_timing",
            "peak_segment": peak_index,
            "peak_type": peak_segment_type,
            "message": f"감정 피크가 {ideal_peak_types}에 없음"
        })

    # 점수 계산 (0-100점)
    base_score = 100.0

    # 목표 범위 위반 (-5점/건)
    base_score -= len([v for v in violations if "expected" in v]) * 5

    # 급격한 하락 (-8점/건)
    base_score -= len(drops) * 8

    # 피크 타이밍 오류 (-10점)
    if any(v.get("type") == "peak_timing" for v in violations):
        base_score -= 10

    # 단조로움 (-15점)
    if any(v.get("type") == "low_variance" for v in violations):
        base_score -= 15

    final_score = max(0.0, min(100.0, base_score))

    report = {
        "emotion_curve_score": round(final_score, 1),
        "segment_scores": segment_scores,
        "emotion_flow": [round(s, 2) for s in scores],
        "violations": violations,
        "sudden_drops": drops,
        "peak_info": {
            "score": round(peak_score, 2),
            "segment_index": peak_index,
            "segment_type": peak_segment_type,
            "is_optimal": peak_segment_type in ideal_peak_types
        },
        "grade": "S" if final_score >= 90 else "A" if final_score >= 80 else "B"
    }

    return final_score, report
