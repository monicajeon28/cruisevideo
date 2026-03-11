#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Re-Hook Keyword Injector - S등급 필수 조건 (FR-3)

Target Timings: 9s, 27s (Valley of Boredom 방지)
Impact: +5.0 S-grade points (PASONA scenarios: 0/10 → 10/10)

Author: Code Writer Agent (2026-03-08)
Based on: output/05_PRD_DOCUMENT.md FR-3
"""

import logging
import random
from typing import Dict, List

from engines.sgrade_constants import REHOOK_TARGET_TIMINGS
from engines.timing_utils import TimingHelper

logger = logging.getLogger(__name__)


class ReHookInjector:
    """
    Re-Hook 키워드 자동 주입 시스템

    S등급 조건:
    - Re-Hook 개수: 최소 2개 이상
    - Re-Hook 타이밍: 9초 ±2초, 27초 ±2초
    - 목적: Valley of Boredom (10-25초) 이탈 방지 + 클라이맥스 예고

    Usage:
        injector = ReHookInjector()
        corrected_script = injector.inject_rehooks(script)
    """

    # Re-Hook 타이밍 - SSOT from sgrade_constants
    REHOOK_1ST_TIMING = REHOOK_TARGET_TIMINGS[0]  # 9.0초
    REHOOK_2ND_TIMING = REHOOK_TARGET_TIMINGS[1]  # 27.0초
    TIMING_WINDOW = 2.0  # ±2초 범위에서 세그먼트 탐색

    # WO v11.0 B-4: Micro-Hook 타이밍 (10초 이상 감정 자극 없는 구간 방지)
    MICRO_HOOK_TIMING = 18.0  # 12~27초 사이 호기심갭 주입
    MICRO_HOOK_KEYWORDS = [
        "잠깐만요",
        "여기서 궁금한 점은",
        "아직 끝이 아닙니다",
        "더 놀라운 건",
        "핵심 포인트는",
    ]

    # 1차 Re-Hook 키워드 (9초, 손실 회피 프레임)
    REHOOK_1ST_KEYWORDS = [
        "잠깐",
        "하지만",
        "놓치면 안 되는",
        "중요한",
        "여기서 끝이 아닙니다",
        "더 중요한 게",
        "손해 보지 마세요",
        "이걸 모르면"
    ]

    # 2차 Re-Hook 키워드 (27초, 사회적 증거 프레임)
    REHOOK_2ND_KEYWORDS = [
        "핵심은",
        "진짜 혜택",
        "그런데",
        "마지막으로",
        "가장 중요한",
        "결정적인",
        "재구매율 82%",
        "당신만 놓치시겠어요"
    ]

    # 카테고리별 Re-Hook 템플릿
    REHOOK_TEMPLATES_BY_CATEGORY = {
        "기항지정보": {
            "13s": [
                "잠깐, {port_name}에서 꼭 가봐야 할 곳이 있어요",
                "하지만 {port_name}의 진짜 매력은 따로 있어요",
                "놓치면 안 되는 {port_name} 숨은 명소가 있습니다"
            ],
            "32s": [
                "그런데 {port_name} 투어, 크루즈 승객만 무료예요",
                "핵심은 {port_name}에서 시간 배분입니다",
                "재구매율 82%, {port_name}에서 감동한 분들의 후기입니다"
            ]
        },
        "선내시설": {
            "13s": [
                "하지만 {ship_name}만의 특별함이 있어요",
                "잠깐, {ship_name} 숨은 시설을 보여드릴게요",
                "놓치면 안 되는 {ship_name} 꿀팁이 있습니다"
            ],
            "32s": [
                "진짜 놀라운 건 지금부터예요",
                "핵심은 {ship_name}의 이 서비스입니다",
                "지금 예약하면 60만원 지원 받으세요"
            ]
        },
        "불안해소": {
            "13s": [
                "놓치면 안 되는 사실이 있어요",
                "하지만 걱정 마세요, 해결책이 있습니다",
                "중요한 건 2억 보험이 기본이라는 거예요"
            ],
            "32s": [
                "핵심은 24시간 한국어 케어입니다",
                "그런데 11년간 무사고 기록입니다",
                "재구매율 82%, 안심하고 다녀온 분들의 후기예요"
            ]
        },
        "가격비교": {
            "13s": [
                "잠깐, 가격만 비교하면 안 됩니다",
                "하지만 숨은 비용이 있어요",
                "놓치면 60만원 손해입니다"
            ],
            "32s": [
                "핵심은 올인클루시브 가격입니다",
                "그런데 오늘 신청하면 60만원 지원",
                "이번 달 출발 상품 확인해보세요"
            ]
        },
        "버킷리스트": {
            "13s": [
                "잠깐, 내년엔 못 올 수도 있어요",
                "하지만 지금이 골든타임입니다",
                "놓치면 평생 후회할 수 있어요"
            ],
            "32s": [
                "핵심은 지금 결정하는 겁니다",
                "그런데 68세 선배들은 벌써 신청했어요",
                "재구매율 82%, 다녀온 분들이 증명합니다"
            ]
        }
    }

    # 기본 Re-Hook 템플릿 (카테고리 없을 때)
    DEFAULT_REHOOK_TEMPLATES = {
        "13s": [
            "잠깐, 여기서 가장 중요한 걸 말씀드릴게요",
            "하지만 더 중요한 사실이 있어요",
            "놓치면 안 되는 정보가 있습니다"
        ],
        "32s": [
            "핵심은 바로 이겁니다",
            "그래서 결론은요",
            "제일 중요한 건 바로 이거예요"
        ],
        # WO v11.0 B-4: Micro-Hook 템플릿 (18초, 호기심갭)
        "micro": [
            "그런데 아직 제일 중요한 걸 말씀 안 드렸어요",
            "여기서부터가 진짜 핵심입니다",
            "더 놀라운 건 이제부터예요",
        ]
    }

    def __init__(self):
        logger.info(f"ReHookInjector 초기화 완료 ({REHOOK_TARGET_TIMINGS[0]}초, {REHOOK_TARGET_TIMINGS[1]}초 Re-Hook 자동 주입)")

    def inject_rehooks(self, script: Dict) -> Dict:
        """
        Re-Hook 자동 주입 (9초, 27초)

        Args:
            script: 스크립트 딕셔너리

        Returns:
            Re-Hook이 주입된 스크립트

        Raises:
            ValueError: script가 None이거나 segments가 없을 경우
        """
        if not script or "segments" not in script:
            raise ValueError("Invalid script: 'segments' field required")

        # 1. 현재 Re-Hook 개수 확인
        existing_rehooks = self._count_rehooks(script)
        logger.info(f"[Re-Hook Injector] 현재 Re-Hook 개수: {existing_rehooks}개 (목표: 2개 이상)")

        # 2. 9초 Re-Hook 체크 및 주입
        has_13s = self._has_rehook_in_window(
            script,
            self.REHOOK_1ST_TIMING,
            self.REHOOK_1ST_KEYWORDS
        )

        if not has_13s:
            logger.info("[Re-Hook Injector] 9초 Re-Hook 없음 → 주입")
            script = self._inject_rehook_at_timing(
                script,
                timing=self.REHOOK_1ST_TIMING,
                stage="13s"
            )

        # 3. 27초 Re-Hook 체크 및 주입
        has_32s = self._has_rehook_in_window(
            script,
            self.REHOOK_2ND_TIMING,
            self.REHOOK_2ND_KEYWORDS
        )

        if not has_32s:
            logger.info("[Re-Hook Injector] 27초 Re-Hook 없음 → 주입")
            script = self._inject_rehook_at_timing(
                script,
                timing=self.REHOOK_2ND_TIMING,
                stage="32s"
            )

        # 4. WO v11.0 B-4: Micro-Hook 주입 (18초, 호기심갭)
        has_micro = self._has_rehook_in_window(
            script,
            self.MICRO_HOOK_TIMING,
            self.MICRO_HOOK_KEYWORDS
        )

        if not has_micro:
            logger.info("[Re-Hook Injector] 18초 Micro-Hook 없음 → 주입")
            script = self._inject_rehook_at_timing(
                script,
                timing=self.MICRO_HOOK_TIMING,
                stage="micro"
            )

        # 5. 최종 Re-Hook 개수 확인
        final_rehooks = self._count_rehooks(script)
        logger.info(
            f"[Re-Hook Injector] Re-Hook 주입 완료: "
            f"{existing_rehooks}개 → {final_rehooks}개"
        )

        return script

    def _count_rehooks(self, script: Dict) -> int:
        """
        스크립트 내 Re-Hook 개수 카운트

        Returns:
            Re-Hook 개수
        """
        count = 0
        cumulative_time = 0.0

        for segment in script.get("segments", []):
            # is_rehook 플래그 체크
            if segment.get("is_rehook"):
                count += 1

            # 9초/27초 근처 Re-Hook 키워드 체크
            text = segment.get("text", "") + " " + segment.get("subtitle", "")
            text_lower = text.lower()

            # Re-Hook 1 범위 (SSOT 타이밍 ±2초)
            if REHOOK_TARGET_TIMINGS[0] - 2.0 <= cumulative_time <= REHOOK_TARGET_TIMINGS[0] + 2.0:
                if any(kw in text_lower for kw in self.REHOOK_1ST_KEYWORDS):
                    count += 1

            # Re-Hook 2 범위 (SSOT 타이밍 ±2초)
            if REHOOK_TARGET_TIMINGS[1] - 2.0 <= cumulative_time <= REHOOK_TARGET_TIMINGS[1] + 2.0:
                if any(kw in text_lower for kw in self.REHOOK_2ND_KEYWORDS):
                    count += 1

            cumulative_time += TimingHelper.get_segment_duration(segment)

        # 중복 제거 (is_rehook + 키워드 중복)
        return min(count, 4)  # 최대 4개까지만 인정

    def _has_rehook_in_window(
        self,
        script: Dict,
        target_timing: float,
        keywords: List[str]
    ) -> bool:
        """
        target_timing ±2초 범위에 Re-Hook 키워드가 있는지 체크

        Returns:
            True: Re-Hook 존재, False: 없음
        """
        cumulative_time = 0.0

        for segment in script.get("segments", []):
            # 타이밍 범위 체크
            if abs(cumulative_time - target_timing) <= self.TIMING_WINDOW:
                text = segment.get("text", "") + " " + segment.get("subtitle", "")
                text_lower = text.lower()

                # 키워드 존재 체크
                if any(kw in text_lower for kw in keywords):
                    logger.debug(
                        f"[Re-Hook] {target_timing:.0f}초 Re-Hook 발견: "
                        f"{cumulative_time:.1f}s ('{text[:30]}...')"
                    )
                    return True

                # is_rehook 플래그 체크
                if segment.get("is_rehook"):
                    return True

            cumulative_time += TimingHelper.get_segment_duration(segment)

        return False

    def _inject_rehook_at_timing(
        self,
        script: Dict,
        timing: float,
        stage: str
    ) -> Dict:
        """
        target_timing에 가장 가까운 세그먼트에 Re-Hook 주입

        Args:
            timing: 목표 타이밍 (9.0, 18.0, or 27.0)
            stage: "13s", "micro", or "32s"

        Returns:
            Re-Hook이 주입된 스크립트
        """
        segments = script.get("segments", [])

        # target_timing에 가장 가까운 세그먼트 찾기
        cumulative_time = 0.0
        closest_idx = None
        min_deviation = float('inf')

        for idx, segment in enumerate(segments):
            deviation = abs(cumulative_time - timing)
            if deviation < min_deviation:
                min_deviation = deviation
                closest_idx = idx

            cumulative_time += TimingHelper.get_segment_duration(segment)

        if closest_idx is None:
            logger.warning(f"[Re-Hook Inject] {timing:.0f}초 주입 실패 (세그먼트 없음)")
            return script

        # Re-Hook 템플릿 선택
        category = script.get("context", {}).get("category", "")
        rehook_text = self._select_rehook_template(
            category=category,
            stage=stage,
            context=script.get("context", {})
        )

        # 세그먼트 텍스트 앞에 Re-Hook 추가
        original_text = segments[closest_idx].get("text", "")
        segments[closest_idx]["text"] = f"{rehook_text} {original_text}"
        segments[closest_idx]["is_rehook"] = True
        segments[closest_idx]["rehook_timing"] = timing

        logger.info(
            f"[Re-Hook Inject] {timing:.0f}초 Re-Hook 주입 완료: "
            f"segment {closest_idx} ('{rehook_text}')"
        )

        script["segments"] = segments
        return script

    def _select_rehook_template(
        self,
        category: str,
        stage: str,
        context: Dict
    ) -> str:
        """
        카테고리 + Context 기반 Re-Hook 템플릿 선택

        Args:
            category: 카테고리명
            stage: "13s" or "32s"
            context: 스크립트 context (port_name, ship_name 등)

        Returns:
            Re-Hook 텍스트
        """
        # 카테고리별 템플릿 우선
        if category in self.REHOOK_TEMPLATES_BY_CATEGORY and stage in self.REHOOK_TEMPLATES_BY_CATEGORY[category]:
            templates = self.REHOOK_TEMPLATES_BY_CATEGORY[category][stage]
        else:
            templates = self.DEFAULT_REHOOK_TEMPLATES[stage]

        # 랜덤 선택
        template = random.choice(templates)

        # Context 변수 치환
        port_name = context.get("port_name", "이곳")
        ship_name = context.get("ship_name", "이 크루즈")

        rehook_text = template.format(port_name=port_name, ship_name=ship_name)

        return rehook_text


# ============================================================================
# Convenience Function
# ============================================================================

def inject_rehooks(script: Dict) -> Dict:
    """
    Re-Hook 주입 편의 함수

    Usage:
        corrected_script = inject_rehooks(script)
    """
    injector = ReHookInjector()
    return injector.inject_rehooks(script)


# ============================================================================
# Unit Tests
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 샘플 테스트
    test_script = {
        "context": {
            "category": "기항지정보",
            "port_name": "산토리니",
            "ship_name": "MSC 벨리시마"
        },
        "segments": [
            {"text": "Hook 시작", "duration": 5.0},
            {"text": "Body 1", "duration": 6.0},
            {"text": "Body 2", "duration": 10.0},  # 11초 근처 (9초 Re-Hook 주입 대상)
            {"text": "Body 3", "duration": 10.0},
            {"text": "Body 4", "duration": 10.0},  # 31초 근처 (27초 Re-Hook 주입 대상)
            {"text": "CTA", "duration": 10.0},
        ]
    }

    injector = ReHookInjector()
    result = injector.inject_rehooks(test_script)

    print("\n=== Re-Hook Injection Result ===")
    print(f"Re-Hook count: {injector._count_rehooks(result)}")

    for idx, seg in enumerate(result["segments"]):
        if seg.get("is_rehook"):
            print(f"Segment {idx}: [{seg['rehook_timing']:.0f}s] {seg['text'][:50]}...")
