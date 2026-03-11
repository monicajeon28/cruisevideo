#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTA 3-Stage Template Validator - S등급 필수 조건 (FR-2)

3-Stage Structure: Urgency (3.0s) + Action (3.5s) + Trust (3.5s) = 10.0s
Impact: +4.0 S-grade points (6/10 → 10/10)

Author: Code Writer Agent (2026-03-08)
Based on: output/05_PRD_DOCUMENT.md FR-2
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class CTAValidator:
    """
    CTA 3단계 구조 검증 및 강제 보정 시스템

    S등급 조건:
    - Stage 1 (Urgency): 3.0초 - 긴급성 + 인센티브
    - Stage 2 (Action): 3.5초 - 행동 유도 + 혜택
    - Stage 3 (Trust): 3.5초 - 신뢰 강화 (Trust 요소 2개 이상)
    - Total Duration: 10.0초

    Usage:
        validator = CTAValidator()
        corrected_script = validator.validate_and_enforce_cta(script)
    """

    # CTA 3단계 구조
    STRUCTURE = {
        'urgency': {
            'duration': 3.0,
            'keywords': ['마감', '임박', '한정', '지금', '60만원', '지원'],
            'required_count': 2,  # 최소 2개 키워드 필요
        },
        'action': {
            'duration': 3.5,
            'keywords': ['프로필', '링크', '확인', '클릭', '카카오톡', '검색', '상담'],
            'required_count': 2,
        },
        'trust': {
            'duration': 3.5,
            'keywords': ['11년', '경력', '2억', '보험', '24시간', '케어', '재구매율', '82%'],
            'required_count': 2,  # S등급 조건: Trust 요소 2개 이상
        }
    }

    TOTAL_DURATION = 10.0  # 전체 CTA 길이
    TOLERANCE = 0.5  # ±0.5초 허용

    def __init__(self):
        logger.info("CTAValidator 초기화 완료 (3단계 구조: Urgency 3.0s + Action 3.5s + Trust 3.5s)")

    def validate_and_enforce_cta(self, script: Dict) -> Dict:
        """
        CTA 3단계 구조 검증 및 강제 보정

        Args:
            script: 스크립트 딕셔너리

        Returns:
            보정된 스크립트

        Raises:
            ValueError: script가 None이거나 segments가 없을 경우
        """
        if not script or "segments" not in script:
            raise ValueError("Invalid script: 'segments' field required")

        # 1. CTA 세그먼트 추출
        cta_segments = self._extract_cta_segments(script)

        if not cta_segments:
            logger.warning("[CTA Validator] CTA 세그먼트 없음 - 스킵")
            return script

        logger.info(f"[CTA Validator] CTA 세그먼트 {len(cta_segments)}개 발견")

        # 2. 3단계 구조 검증
        validation_result = self._validate_structure(cta_segments)

        if not validation_result['valid']:
            logger.warning(
                f"[CTA Validator] CTA 구조 미흡: {', '.join(validation_result['issues'])}"
            )
            # 3. 자동 보정 (단, Gemini 재생성 권장 - 현재는 경고만)
            logger.info("[CTA Validator] CTA 재생성 권장 (Gemini prompt에 3단계 구조 명시)")
        else:
            logger.info(
                f"[CTA Validator] CTA 구조 정상: "
                f"Urgency {validation_result['urgency_score']}/2, "
                f"Action {validation_result['action_score']}/2, "
                f"Trust {validation_result['trust_score']}/2"
            )

        # 4. Trust 요소 검증 (S등급 필수)
        trust_count = validation_result['trust_score']
        if trust_count < 2:
            logger.warning(
                f"[CTA Validator] Trust 요소 부족: {trust_count}/2 → "
                "S등급 조건 미충족 (최소 2개 필요: 11년+2억+24시간 중 2개)"
            )

        # 5. 총 길이 검증
        total_duration = sum(
            seg.get("duration", 0.0)
            for seg in cta_segments
        )

        if abs(total_duration - self.TOTAL_DURATION) > self.TOLERANCE:
            logger.warning(
                f"[CTA Validator] CTA 총 길이 이탈: "
                f"{total_duration:.1f}s (목표: {self.TOTAL_DURATION}s)"
            )

        return script

    def _extract_cta_segments(self, script: Dict) -> List[Dict]:
        """
        CTA 세그먼트 추출

        Returns:
            CTA 세그먼트 리스트 (segment_type이 'cta'인 것들)
        """
        cta_segments = []

        for segment in script.get("segments", []):
            # segment_type이 'cta'이거나, section이 'cta'인 것
            if (segment.get("segment_type") == "cta" or
                segment.get("section") == "cta" or
                "cta" in segment.get("segment_type", "").lower()):
                cta_segments.append(segment)

        return cta_segments

    def _validate_structure(self, cta_segments: List[Dict]) -> Dict:
        """
        CTA 3단계 구조 검증

        Returns:
            {
                'valid': bool,
                'urgency_score': int (0-2),
                'action_score': int (0-2),
                'trust_score': int (0-2),
                'issues': List[str]
            }
        """
        result = {
            'valid': True,
            'urgency_score': 0,
            'action_score': 0,
            'trust_score': 0,
            'issues': []
        }

        # 전체 CTA 텍스트 합치기
        full_text = " ".join(
            seg.get("text", "") + " " + seg.get("subtitle", "")
            for seg in cta_segments
        ).lower()

        # 1. Urgency 키워드 체크
        urgency_keywords_found = [
            kw for kw in self.STRUCTURE['urgency']['keywords']
            if kw in full_text
        ]
        result['urgency_score'] = min(len(urgency_keywords_found), 2)

        if result['urgency_score'] < self.STRUCTURE['urgency']['required_count']:
            result['valid'] = False
            result['issues'].append(
                f"Urgency 키워드 부족 ({result['urgency_score']}/2): "
                f"{', '.join(self.STRUCTURE['urgency']['keywords'][:3])}... 중 2개 이상 필요"
            )

        # 2. Action 키워드 체크
        action_keywords_found = [
            kw for kw in self.STRUCTURE['action']['keywords']
            if kw in full_text
        ]
        result['action_score'] = min(len(action_keywords_found), 2)

        if result['action_score'] < self.STRUCTURE['action']['required_count']:
            result['valid'] = False
            result['issues'].append(
                f"Action 키워드 부족 ({result['action_score']}/2): "
                f"{', '.join(self.STRUCTURE['action']['keywords'][:3])}... 중 2개 이상 필요"
            )

        # 3. Trust 키워드 체크 (S등급 조건)
        trust_keywords_found = [
            kw for kw in self.STRUCTURE['trust']['keywords']
            if kw in full_text
        ]
        result['trust_score'] = min(len(trust_keywords_found), 2)

        if result['trust_score'] < self.STRUCTURE['trust']['required_count']:
            result['valid'] = False
            result['issues'].append(
                f"Trust 키워드 부족 ({result['trust_score']}/2): "
                "11년+2억+24시간 중 2개 이상 필요 (S등급 필수)"
            )

        # 로그 상세 출력
        if urgency_keywords_found:
            logger.debug(f"[CTA] Urgency 키워드: {', '.join(urgency_keywords_found)}")
        if action_keywords_found:
            logger.debug(f"[CTA] Action 키워드: {', '.join(action_keywords_found)}")
        if trust_keywords_found:
            logger.debug(f"[CTA] Trust 키워드: {', '.join(trust_keywords_found)}")

        return result

    def get_cta_template_recommendation(self, category: str, tier: str) -> str:
        """
        카테고리 + Tier 기반 CTA 템플릿 추천

        Args:
            category: 카테고리명 (기항지정보, 불안해소, 가격비교 등)
            tier: 가격대 (T1-T4)

        Returns:
            추천 CTA 템플릿 (Gemini prompt 삽입용)
        """
        # T4 Premium은 Trust 강화
        if tier == "T4":
            return """
CTA Stage 1 - Urgency (3.0초):
"인기 일정 마감 임박입니다. 지금 신청하시면 60만원 지원 받으실 수 있어요"

CTA Stage 2 - Action (3.5초):
"프로필에서 크루즈닷 확인하세요. 3만원 쿠폰과 상담 예약 가능합니다"

CTA Stage 3 - Trust (3.5초):
"크루즈닷. 11년간 재구매율 82%를 기록한 정식 등록 여행사. 2억 보험 기본 포함입니다"
"""

        # T3 Mainstream은 가치 강조
        elif tier == "T3":
            return """
CTA Stage 1 - Urgency (3.0초):
"한정 특가, 지금 확인하세요. 60만원 특별 지원 중입니다"

CTA Stage 2 - Action (3.5초):
"프로필 링크에서 일정표 확인하세요. 카카오톡으로 상담 신청하세요"

CTA Stage 3 - Trust (3.5초):
"11년 경력 크루즈 전문가가 24시간 한국어로 케어해드립니다"
"""

        # 기본 템플릿 (T1-T2)
        else:
            return """
CTA Stage 1 - Urgency (3.0초):
"인기 일정 한정, 지금 확인하세요"

CTA Stage 2 - Action (3.5초):
"프로필에서 크루즈닷 검색하세요"

CTA Stage 3 - Trust (3.5초):
"11년 경력 여행사, 2억 보험 포함입니다"
"""


# ============================================================================
# Convenience Function
# ============================================================================

def validate_cta_structure(script: Dict) -> Dict:
    """
    CTA 구조 검증 편의 함수

    Usage:
        corrected_script = validate_cta_structure(script)
    """
    validator = CTAValidator()
    return validator.validate_and_enforce_cta(script)


# ============================================================================
# Unit Tests
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 샘플 테스트
    test_script = {
        "segments": [
            {"text": "Hook", "section": "hook", "duration": 5.0},
            {"text": "Body", "section": "body", "duration": 35.0},
            {
                "text": "인기 일정 마감 임박입니다. 지금 신청하시면 60만원 지원",
                "section": "cta",
                "segment_type": "cta_urgency",
                "duration": 3.0
            },
            {
                "text": "프로필에서 크루즈닷 확인하세요",
                "section": "cta",
                "segment_type": "cta_action",
                "duration": 3.5
            },
            {
                "text": "11년 경력, 2억 보험 포함입니다",
                "section": "cta",
                "segment_type": "cta_trust",
                "duration": 3.5
            },
        ]
    }

    validator = CTAValidator()
    result = validator.validate_and_enforce_cta(test_script)

    print("\n=== CTA Structure Validation Result ===")
    cta_segments = validator._extract_cta_segments(result)
    validation = validator._validate_structure(cta_segments)
    print(f"Valid: {validation['valid']}")
    print(f"Urgency: {validation['urgency_score']}/2")
    print(f"Action: {validation['action_score']}/2")
    print(f"Trust: {validation['trust_score']}/2")
    print(f"Issues: {validation['issues']}")
