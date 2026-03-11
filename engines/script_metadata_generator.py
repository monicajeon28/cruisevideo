#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Metadata Generator - 제목/Pop/Re-Hook/출력 구성
God Object 분리: comprehensive_script_generator.py에서 추출

Usage:
    from engines.script_metadata_generator import ScriptMetadataGenerator

    meta = ScriptMetadataGenerator()
    title = meta.generate_title(topic, port, ship, content_type)
    pop_messages = meta.inject_pop_metadata(segments, port, ship)
"""

import logging
import random
from typing import Dict, List, Any

from engines.sgrade_constants import POP_TARGET_TIMINGS, REHOOK_TARGET_TIMINGS

logger = logging.getLogger(__name__)


class ScriptMetadataGenerator:
    """
    스크립트 메타데이터 생성기

    제목, Pop 메타데이터, Re-Hook 세그먼트, Dataclass 변환을 담당한다.
    comprehensive_script_generator.py의 God Object에서 분리된 모듈.
    """

    # WO v7.0: Re-Hook 타이밍 조정 (13->9초, 32->27초)
    # Re-Hook1: 8-10초 이탈 방지 (기존 13초는 이미 이탈 후)
    # Re-Hook2: Pop2(32.5초)와 5초 간격 확보 (기존 0.5초 충돌)
    REHOOK_PATTERNS_9S = [
        # 기존 5개
        "잠깐, 이건 꼭 들어보세요!",
        "여기서 반전이 있어요!",
        "근데 이게 시작일 뿐이에요!",
        "이 다음이 더 놀라워요!",
        "핵심은 바로 이거예요!",
        # S2-B2: 신규 7개
        "그런데 더 놀라운 건요!",
        "이건 아무도 모르는 팁인데요!",
        "여기서부터가 꿀팁이에요!",
        "한 가지 더 알려드릴게요!",
        "이 부분을 놓치면 안 돼요!",
        "잠깐만요, 이게 핵심이에요!",
        "여기서 제가 깜짝 놀랐어요!",
    ]

    REHOOK_PATTERNS_27S = [
        # 기존 5개
        "이게 끝이 아니에요!",
        "세 번째 이유가 가장 중요해요!",
        "여기서부터가 핵심이에요!",
        "결정적인 차이는 바로 이거예요!",
        "마지막 이유를 들으면 놀라실 거예요!",
        # S2-B2: 신규 7개
        "근데 핵심은 따로 있어요!",
        "이 한 가지가 모든 걸 바꿔요!",
        "여기서 포기하면 손해예요!",
        "솔직히 이건 저도 몰랐어요!",
        "이 부분이 가장 많이 물어보시는 거예요!",
        "마지막까지 보셔야 할 이유가 있어요!",
        "가장 중요한 부분이 남았어요!",
    ]

    def generate_title(
        self,
        topic: str,
        port: str,
        ship: str,
        content_type: str
    ) -> str:
        """
        제목 생성 (70자 이내)

        Args:
            topic: 주제
            port: 기항지
            ship: 선박
            content_type: 콘텐츠 유형

        Returns:
            제목 문자열
        """
        # Content Type별 제목 패턴
        title_patterns = {
            "EDUCATION": f"{port} 크루즈 완벽 가이드 - {topic}",
            "COMPARISON": f"{port} vs 육지 여행 비교 - {topic}",
            "SOCIAL_PROOF": f"2만 가족이 선택한 {port} 크루즈",
            "FEAR_RESOLUTION": f"{port} 크루즈 불안 해소 - {topic}",
            "VALUE_PROOF": f"{port} 크루즈 가성비 - {topic}",
            "CRITERIA_EDUCATION": f"{port} 크루즈 선택 기준 - {topic}",
            "BUCKET_LIST": f"{port} 크루즈 버킷리스트 - {topic}",
            "CONVENIENCE": f"{port} 크루즈 편의성 - {topic}",
            # 공포심리 7종 제목
            "FEAR_CRUISE_PORT": f"{port} 크루즈 항구 찾기, 이것만 알면 안전합니다",
            "FEAR_ONBOARD_SYSTEM": f"{port} 크루즈 선내 시스템, 미리 알고 가세요",
            "FEAR_HIDDEN_COST": f"{port} 크루즈 숨겨진 비용 없는 투명한 가격",
            "FEAR_TIME_WASTE": f"{port} 크루즈 시간 낭비 없는 완벽 일정",
            "FEAR_LANGUAGE": f"{port} 크루즈 언어 걱정 없는 한국어 케어",
            "FEAR_SAFETY": f"{port} 크루즈 안전하게 떠나는 방법",
            "FEAR_INFO_GAP": f"{port} 크루즈 정보 부족 해소 완벽 가이드",
        }

        title = title_patterns.get(content_type, f"{port} 크루즈 - {topic}")

        # 70자 제한
        if len(title) > 70:
            title = title[:67] + "..."

        return title

    def inject_pop_metadata(
        self,
        segments: List[Any],
        port: str,
        ship: str
    ) -> List[Dict[str, Any]]:
        """
        Pop Messages 메타데이터 자동 생성

        4-Block 누적 duration 기반으로 15.0s / 32.5s / 42.0s 위치에
        Pop 3개를 자동 배치한다.

        validator가 검사하는 형식:
            metadata["pop_messages"] = [
                {"timing": 15.0, "text": "..."},
                {"timing": 32.5, "text": "..."},
                {"timing": 42.0, "text": "..."}
            ]

        Args:
            segments: 세그먼트 리스트
            port: 기항지
            ship: 선박

        Returns:
            Pop messages 리스트 (3개)
        """
        # Pop 텍스트 풀 (포트/선박 맞춤)
        pop_text_pool = [
            # Pop 1 후보 (15.0초 - Block 1 후반, 가치 제안)
            [
                "숙박+식사+이동 전부 포함",
                f"하루 21만원에 {port} 여행",
                "호텔+식사+교통 올인원",
                f"{ship} 5성급 객실 포함",
            ],
            # Pop 2 후보 (32.5초 - Block 2-3 경계, 서비스 강점)
            [
                "24시간 한국어 케어 기본 제공",
                f"{port} 전문 가이드 동행",
                "하루 3끼 뷔페 무제한",
                "짐 풀 필요 없는 여행",
            ],
            # Pop 3 후보 (42.0초 - CTA 직전, Trust 강화)
            [
                "2억 보험 자동 포함",
                "11년 경력 전문가 동행",
                "재구매율 82% 검증 완료",
                "만족도 98.7% 인증",
            ],
        ]

        pop_messages = []
        # WO v7.0: Pop3 46.5->42초 (CTA 시작 43초 전에 배치, CTA 중간 Pop 방지)
        target_timings = POP_TARGET_TIMINGS

        for i, timing in enumerate(target_timings):
            text = random.choice(pop_text_pool[i])
            pop_messages.append({
                "timing": timing,
                "text": text,
            })

        logger.info(
            f"[FIX-POP-1] Pop 메타데이터 3개 자동 생성: "
            f"{[p['timing'] for p in pop_messages]}"
        )

        return pop_messages

    def inject_rehook_segments(
        self,
        segment_dicts: List[Dict[str, Any]],
        port: str,
        ship: str
    ) -> List[Dict[str, Any]]:
        """
        Re-Hook 세그먼트 자동 삽입

        Block 1->2 경계 (~9초)와 Block 2->3 경계 (~27초)에
        rehook segment를 삽입한다.

        validator가 검사하는 형식:
            segment_type == "rehook"
            timing: 9.0초 / 27.0초

        Args:
            segment_dicts: 기존 세그먼트 dict 리스트
            port: 기항지
            ship: 선박

        Returns:
            Re-Hook이 삽입된 세그먼트 리스트
        """
        # WO v7.0: 타이밍 9초/27초 (기존 13/32 -> 이탈 방지 + Pop 충돌 해소)
        result = []
        # Hook의 실제 duration 사용 (없으면 5.0초 기본값)
        hook_duration = segment_dicts[0].get("duration_target", 5.0) if segment_dicts else 5.0
        cumulative_time = hook_duration

        rehook_9_text = random.choice(self.REHOOK_PATTERNS_9S)
        rehook_27_text = random.choice(self.REHOOK_PATTERNS_27S)
        rehook_9_inserted = False
        rehook_27_inserted = False

        for seg in segment_dicts:
            seg_duration = seg.get("duration_target", 12.0)
            seg_end_time = cumulative_time + seg_duration

            # 8-10초 이탈 방지 -> 9초 Re-Hook
            if not rehook_9_inserted and seg_end_time >= 8.0:
                rehook_9 = {
                    "type": "rehook",
                    "segment_type": "rehook",
                    "text": rehook_9_text,
                    "tts_voice": "juho",
                    "emotion": "surprise",
                    "emotion_score": 0.70,
                    "duration_target": 1.5,
                    "timing": 9.0,
                    "start_time": 9.0,
                    "keywords": [],
                }
                result.append(seg)
                result.append(rehook_9)
                rehook_9_inserted = True
                cumulative_time = seg_end_time + 1.5
                continue

            # Pop2(32.5초)와 5초 간격 -> 27초 Re-Hook
            if not rehook_27_inserted and rehook_9_inserted and seg_end_time >= 22.0:
                rehook_27 = {
                    "type": "rehook",
                    "segment_type": "rehook",
                    "text": rehook_27_text,
                    "tts_voice": "juho",
                    "emotion": "surprise",
                    "emotion_score": 0.75,
                    "duration_target": 1.5,
                    "timing": 27.0,
                    "start_time": 27.0,
                    "keywords": [],
                }
                result.append(seg)
                result.append(rehook_27)
                rehook_27_inserted = True
                cumulative_time = seg_end_time + 1.5
                continue

            result.append(seg)
            cumulative_time = seg_end_time

        # 안전장치: 삽입 못한 경우 끝에 추가
        if not rehook_9_inserted:
            result.append({
                "type": "rehook", "segment_type": "rehook",
                "text": rehook_9_text, "tts_voice": "juho",
                "emotion": "surprise", "emotion_score": 0.70,
                "duration_target": 1.5, "timing": 9.0, "start_time": 9.0,
                "keywords": [],
            })
        if not rehook_27_inserted:
            result.append({
                "type": "rehook", "segment_type": "rehook",
                "text": rehook_27_text, "tts_voice": "juho",
                "emotion": "surprise", "emotion_score": 0.75,
                "duration_target": 1.5, "timing": 27.0, "start_time": 27.0,
                "keywords": [],
            })

        rehook_count = sum(
            1 for s in result if s.get("segment_type") == "rehook"
        )
        logger.info(f"[Re-Hook] {rehook_count}개 자동 삽입: 9.0초, 27.0초")

        return result

    def dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Dataclass를 Dict로 재귀 변환

        list 내부의 dataclass 객체도 함께 변환한다.

        Args:
            obj: Dataclass 객체 또는 일반 값

        Returns:
            변환된 Dict 또는 원본 값
        """
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, list):
                    result[field_name] = [
                        self.dataclass_to_dict(item)
                        if hasattr(item, '__dataclass_fields__')
                        else item
                        for item in value
                    ]
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self.dataclass_to_dict(value)
                else:
                    result[field_name] = value
            return result
        else:
            return obj
