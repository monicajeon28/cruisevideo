#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimingHelper - Duration 계산 유틸리티 (WO v11.0 E-3)

세그먼트 duration 계산 중복 제거.
기존: pop_message_validator, rehook_injector, script_validation_orchestrator에서
동일 패턴 8회 이상 반복.

Usage:
    from engines.timing_utils import TimingHelper

    duration = TimingHelper.get_segment_duration(segment)
    cumulative = TimingHelper.calculate_cumulative_time(segments, up_to_index=5)
"""

from typing import Dict, List


class TimingHelper:
    """세그먼트 타이밍 계산 유틸리티"""

    @staticmethod
    def get_segment_duration(segment: Dict) -> float:
        """세그먼트 duration 계산 (duration 키 우선, 없으면 end_time-start_time)

        Args:
            segment: 세그먼트 딕셔너리

        Returns:
            duration (초), 계산 불가 시 0.0
        """
        duration = segment.get("duration", 0.0)
        if isinstance(duration, (int, float)) and duration > 0:
            return float(duration)
        if "end_time" in segment and "start_time" in segment:
            try:
                return float(segment["end_time"]) - float(segment["start_time"])
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    @staticmethod
    def calculate_cumulative_time(segments: List[Dict], up_to_index: int) -> float:
        """세그먼트 리스트의 누적 시간 계산

        Args:
            segments: 세그먼트 리스트
            up_to_index: 계산할 마지막 인덱스 (exclusive)

        Returns:
            누적 시간 (초)
        """
        return sum(
            TimingHelper.get_segment_duration(segments[i])
            for i in range(min(up_to_index, len(segments)))
        )
