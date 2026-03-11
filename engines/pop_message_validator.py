#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pop Message Timing Enforcer - S등급 필수 조건 (FR-1)

Target Timings: 15.0s, 32.5s, 42.0s (정확히 3개, ±0.5s tolerance)
Impact: +3.0 S-grade points (7/10 → 10/10)

Author: Code Writer Agent (2026-03-08)
Based on: output/05_PRD_DOCUMENT.md FR-1
"""

import logging
from typing import Dict, List

from engines.sgrade_constants import POP_TARGET_TIMINGS, REHOOK_TARGET_TIMINGS
from engines.timing_utils import TimingHelper

logger = logging.getLogger(__name__)


class PopMessageValidator:
    """
    Pop 메시지 타이밍 검증 및 강제 보정 시스템

    S등급 조건:
    - Pop 개수: 정확히 3개
    - Pop 타이밍: 15.0s (±0.5s), 32.5s (±0.5s), 42.0s (±0.5s)
    - Re-hook 충돌 방지: Pop과 Re-hook 간 최소 1.5초 간격

    Usage:
        validator = PopMessageValidator()
        corrected_script = validator.validate_and_correct(script)
    """

    # S등급 표준 타이밍 (3개 고정) - SSOT from sgrade_constants
    TARGET_TIMINGS = POP_TARGET_TIMINGS
    TOLERANCE = 0.5  # ±0.5초 허용

    # Re-hook 충돌 방지 - SSOT from sgrade_constants
    REHOOK_TIMINGS = REHOOK_TARGET_TIMINGS
    REHOOK_CONFLICT_THRESHOLD = 1.5

    def __init__(self):
        logger.info(f"PopMessageValidator 초기화 완료 (S등급 타이밍: {', '.join(f'{t}s' for t in POP_TARGET_TIMINGS)})")

    def validate_and_correct(self, script: Dict) -> Dict:
        """
        Pop 타이밍 검증 및 자동 보정

        Args:
            script: 스크립트 딕셔너리 (segments 포함)

        Returns:
            보정된 스크립트

        Raises:
            ValueError: script가 None이거나 segments가 없을 경우
        """
        if not script or "segments" not in script:
            raise ValueError("Invalid script: 'segments' field required")

        # 1. 현재 Pop 위치 추출
        existing_pops = self._extract_pop_timings(script)
        logger.info(f"[Pop Validator] 현재 Pop 개수: {len(existing_pops)}개 (목표: 3개)")

        # 2. Pop 개수 체크
        if len(existing_pops) != 3:
            logger.warning(f"[Pop Validator] Pop 개수 오류: {len(existing_pops)}개 != 3개 → 강제 주입")
            script = self._inject_missing_pops(script)
            existing_pops = self._extract_pop_timings(script)  # 재추출

        # 3. Pop 타이밍 정확도 체크
        for i, (existing_timing, target_timing) in enumerate(zip(existing_pops, self.TARGET_TIMINGS)):
            deviation = abs(existing_timing - target_timing)

            if deviation > self.TOLERANCE:
                logger.warning(
                    f"[Pop Validator] Pop {i+1} 타이밍 이탈: "
                    f"{existing_timing:.1f}s → {target_timing:.1f}s (편차: {deviation:.1f}s)"
                )
                script = self._adjust_pop_timing(script, i, target_timing)
            else:
                logger.info(
                    f"[Pop Validator] Pop {i+1} 타이밍 정확: "
                    f"{existing_timing:.1f}s (목표: {target_timing:.1f}s, 편차: {deviation:.1f}s)"
                )

        # 4. Re-hook 충돌 체크
        script = self._check_rehook_conflicts(script)

        logger.info(f"[Pop Validator] Pop 타이밍 검증 완료 (3개, {'/'.join(f'{t}s' for t in POP_TARGET_TIMINGS)})")
        return script

    def _extract_pop_timings(self, script: Dict) -> List[float]:
        """
        스크립트에서 Pop 타이밍 추출

        Returns:
            Pop 타이밍 리스트 (오름차순 정렬)
        """
        pop_timings = []
        cumulative_time = 0.0

        for segment in script.get("segments", []):
            # Pop 효과가 있는 세그먼트만
            if segment.get("pop_effect") or segment.get("pop_message"):
                pop_timings.append(cumulative_time)
                logger.debug(f"[Pop Extract] Pop 발견: {cumulative_time:.1f}s (message: {segment.get('pop_message', 'N/A')})")

            # 다음 세그먼트로 시간 누적
            cumulative_time += TimingHelper.get_segment_duration(segment)

        return sorted(pop_timings)

    def _inject_missing_pops(self, script: Dict) -> Dict:
        """
        부족한 Pop을 TARGET_TIMINGS 위치에 강제 주입

        Returns:
            Pop이 주입된 스크립트
        """
        segments = script.get("segments", [])

        # 현재 Pop 위치 확인
        existing_pop_indices = []
        cumulative_time = 0.0

        for idx, segment in enumerate(segments):
            if segment.get("pop_effect") or segment.get("pop_message"):
                existing_pop_indices.append(idx)

            cumulative_time += TimingHelper.get_segment_duration(segment)

        # 정확히 3개가 될 때까지 주입
        if len(existing_pop_indices) < 3:
            pops_to_add = 3 - len(existing_pop_indices)
            logger.info(f"[Pop Inject] {pops_to_add}개 Pop 주입 필요")

            # TARGET_TIMINGS에 가장 가까운 세그먼트에 주입
            for target_timing in self.TARGET_TIMINGS:
                # 이미 Pop이 있는지 확인
                has_pop = any(
                    abs(self._get_segment_timing(segments, idx) - target_timing) < self.TOLERANCE
                    for idx in existing_pop_indices
                )

                if not has_pop and pops_to_add > 0:
                    # 가장 가까운 세그먼트 찾기
                    closest_idx = self._find_closest_segment(segments, target_timing)
                    if closest_idx is not None and closest_idx not in existing_pop_indices:
                        segments[closest_idx]["pop_effect"] = True
                        segments[closest_idx]["pop_message"] = self._generate_pop_message(target_timing)
                        existing_pop_indices.append(closest_idx)
                        pops_to_add -= 1
                        logger.info(
                            f"[Pop Inject] Pop 주입: {target_timing:.1f}s → "
                            f"segment {closest_idx} ('{segments[closest_idx].get('text', '')}...'')"
                        )

        # Pop이 3개 초과일 경우 제거
        elif len(existing_pop_indices) > 3:
            pops_to_remove = len(existing_pop_indices) - 3
            logger.warning(f"[Pop Inject] {pops_to_remove}개 Pop 제거 필요 (3개 초과)")

            # TARGET_TIMINGS에서 가장 먼 Pop부터 제거
            timings_with_idx = [
                (self._get_segment_timing(segments, idx), idx)
                for idx in existing_pop_indices
            ]
            timings_with_idx.sort(key=lambda x: min(abs(x[0] - t) for t in self.TARGET_TIMINGS), reverse=True)

            for _, idx in timings_with_idx[:pops_to_remove]:
                segments[idx]["pop_effect"] = False
                segments[idx].pop("pop_message", None)
                logger.info(f"[Pop Inject] Pop 제거: segment {idx}")

        script["segments"] = segments
        return script

    def _adjust_pop_timing(self, script: Dict, pop_index: int, target_timing: float) -> Dict:
        """
        Pop 타이밍을 target_timing으로 조정

        Args:
            pop_index: Pop 인덱스 (0, 1, 2)
            target_timing: 목표 타이밍 (15.0, 32.5, 42.0)

        Returns:
            타이밍이 조정된 스크립트
        """
        segments = script.get("segments", [])

        # 현재 Pop 세그먼트 찾기
        pop_segments = []
        cumulative_time = 0.0

        for idx, segment in enumerate(segments):
            if segment.get("pop_effect") or segment.get("pop_message"):
                pop_segments.append((cumulative_time, idx))

            cumulative_time += TimingHelper.get_segment_duration(segment)

        if pop_index >= len(pop_segments):
            logger.warning(f"[Pop Adjust] Pop {pop_index} 인덱스 범위 초과 (총 {len(pop_segments)}개)")
            return script

        current_timing, current_idx = pop_segments[pop_index]

        # 현재 Pop 제거
        segments[current_idx]["pop_effect"] = False
        segments[current_idx].pop("pop_message", None)

        # target_timing에 가장 가까운 세그먼트에 Pop 재배치
        new_idx = self._find_closest_segment(segments, target_timing)
        if new_idx is not None:
            segments[new_idx]["pop_effect"] = True
            segments[new_idx]["pop_message"] = self._generate_pop_message(target_timing)
            logger.info(
                f"[Pop Adjust] Pop {pop_index+1} 이동: "
                f"{current_timing:.1f}s (seg {current_idx}) → "
                f"{target_timing:.1f}s (seg {new_idx})"
            )

        script["segments"] = segments
        return script

    def _find_closest_segment(self, segments: List[Dict], target_timing: float) -> int:
        """
        target_timing에 가장 가까운 세그먼트 인덱스 찾기

        Returns:
            세그먼트 인덱스, 찾지 못하면 None
        """
        cumulative_time = 0.0
        closest_idx = None
        min_deviation = float('inf')

        for idx, segment in enumerate(segments):
            deviation = abs(cumulative_time - target_timing)
            if deviation < min_deviation:
                min_deviation = deviation
                closest_idx = idx

            cumulative_time += TimingHelper.get_segment_duration(segment)

        return closest_idx

    def _get_segment_timing(self, segments: List[Dict], segment_idx: int) -> float:
        """
        세그먼트의 시작 타이밍 계산

        Returns:
            누적 시간 (초)
        """
        return TimingHelper.calculate_cumulative_time(segments, segment_idx)

    def _generate_pop_message(self, timing: float) -> str:
        """
        타이밍에 맞는 Pop 메시지 생성

        Returns:
            Pop 메시지 텍스트
        """
        if timing < 10.0:
            return "60만원 지원"  # 5초 Pop: 가격 혜택
        elif timing < 25.0:
            return "재구매율 82%"  # 18초 Pop: 사회적 증거
        else:
            return "11년 검증"  # 40초 Pop: Trust

    def _check_rehook_conflicts(self, script: Dict) -> Dict:
        """
        Re-hook과 Pop의 충돌 체크 및 경고

        Returns:
            스크립트 (변경 없음, 경고만 출력)
        """
        pop_timings = self._extract_pop_timings(script)

        for pop_timing in pop_timings:
            for rehook_timing in self.REHOOK_TIMINGS:
                if abs(pop_timing - rehook_timing) < self.REHOOK_CONFLICT_THRESHOLD:
                    logger.warning(
                        f"[Pop Validator] 충돌 경고: Pop {pop_timing:.1f}s와 "
                        f"Re-hook {rehook_timing:.1f}s 간격 {abs(pop_timing - rehook_timing):.1f}s "
                        f"(최소 {self.REHOOK_CONFLICT_THRESHOLD}초 권장)"
                    )

        return script


# ============================================================================
# Convenience Function
# ============================================================================

def validate_pop_timing(script: Dict) -> Dict:
    """
    Pop 타이밍 검증 편의 함수

    Usage:
        corrected_script = validate_pop_timing(script)
    """
    validator = PopMessageValidator()
    return validator.validate_and_correct(script)


# ============================================================================
# Unit Tests (자동 실행 방지 - pytest에서만 실행)
# ============================================================================

if __name__ == "__main__":
    # 테스트는 pytest로 실행
    logging.basicConfig(level=logging.DEBUG)

    # 샘플 테스트 (실제 테스트는 tests/test_pop_message_validator.py)
    test_script = {
        "segments": [
            {"text": "Hook 시작", "duration": 4.0},
            {"text": "Pop 1", "duration": 2.0, "pop_effect": True, "pop_message": "60만원"},  # 4초 (목표: 5초)
            {"text": "Body 1", "duration": 10.0},
            {"text": "Pop 2", "duration": 2.0, "pop_effect": True, "pop_message": "재구매율 82%"},  # 16초 (목표: 18초)
            {"text": "Body 2", "duration": 20.0},
            {"text": "Pop 3", "duration": 2.0, "pop_effect": True, "pop_message": "11년"},  # 38초 (목표: 40초)
            {"text": "CTA", "duration": 10.0},
        ]
    }

    validator = PopMessageValidator()
    result = validator.validate_and_correct(test_script)

    print("\n=== Pop Timing Validation Result ===")
    print(f"Pop timings: {validator._extract_pop_timings(result)}")
    print(f"Target: {PopMessageValidator.TARGET_TIMINGS}")
