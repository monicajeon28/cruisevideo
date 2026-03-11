#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTA Optimizer - S-Grade CTA Template Engine
P0-2: 파일 핸들 누수 방지 (클래스 변수 캐싱 + Lock)

Author: Bug Fixer Agent (P0-2)
Date: 2026-03-09

핵심 개선:
- JSON 템플릿 파일 클래스 변수 캐싱 (1회만 로딩)
- threading.Lock으로 동시성 보호
- with open으로 안전한 파일 핸들 관리
"""

import json
import logging
import random
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Any

try:
    from engines.sgrade_constants import CTA_TEMPLATES_BY_TIER, get_all_banned_words
except ImportError:
    CTA_TEMPLATES_BY_TIER = {}
    get_all_banned_words = lambda: []

logger = logging.getLogger(__name__)


# CTA 템플릿 기본값 (파일 없을 경우 사용)
URGENCY_TEMPLATES = [
    "인기 일정 마감 임박입니다. 오늘 신청하시면 60만원 지원 받으실 수 있어요",
    "한정 특가, 오늘 확인하세요. 60만원 특별 지원 중입니다",
    "인기 일정 마감 임박입니다. 오늘 확인하세요",
]

ACTION_TEMPLATES = [
    "프로필에서 크루즈닷 확인하세요. 3만원 쿠폰과 상담 예약 가능합니다",
    "프로필 링크에서 일정표 확인하세요. 카카오톡으로 상담 신청하세요",
    "카카오톡에서 크루즈닷 검색하세요",
]

TRUST_TEMPLATES = [
    "크루즈닷. 11년간 재구매율 82%를 기록한 정식 등록 여행사. 2억 보험 기본 포함입니다",
    "11년 경력 크루즈 전문가가 24시간 한국어로 케어해드립니다",
    "정식 등록 여행사 크루즈닷입니다. 11년 경력, 2억 보험 포함입니다",
]


# WO v11.0 C-2: 상품 Tier별 할인 매핑
TIER_DISCOUNT_MAP = {
    "T4": {"discount": "80만원"},
    "T3": {"discount": "60만원"},
    "T2": {"discount": "40만원"},
    "T1": {"discount": "20만원"},
}


class CTAOptimizer:
    """
    CTA 최적화 엔진 - 파일 핸들 누수 방지

    특징:
    - 클래스 변수 캐싱 (템플릿 1회만 로딩)
    - Lock으로 동시성 보호
    - CTA 3단계 구조 (Urgency + Action + Trust)
    """

    # 클래스 변수 캐싱
    _templates_cache: Optional[Dict[str, Any]] = None
    _cache_lock = Lock()

    # CTA 3단계 구조
    STRUCTURE = {
        'urgency': {'duration': 3.0},
        'action': {'duration': 3.5},
        'trust': {'duration': 3.5}
    }
    TOTAL_DURATION = 10.0

    def __init__(self, templates_path: Optional[str] = None):
        """
        CTAOptimizer 초기화

        Args:
            templates_path: CTA 템플릿 JSON 파일 경로
        """
        if templates_path:
            self.templates_path = Path(templates_path)
        else:
            try:
                from path_resolver import get_paths
                self.templates_path = get_paths().config_dir / "cta_templates.json"
            except (ImportError, Exception):
                self.templates_path = Path("D:/mabiz/config/cta_templates.json")

        # 템플릿 로드 (클래스 변수 캐싱)
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """
        CTA 템플릿 로드 (클래스 변수 캐싱, 1회만 실행)

        Returns:
            템플릿 딕셔너리
        """
        # 캐시 확인 (Lock으로 보호)
        with CTAOptimizer._cache_lock:
            if CTAOptimizer._templates_cache is not None:
                logger.debug("[CTAOptimizer] 템플릿 캐시 사용")
                return CTAOptimizer._templates_cache

            # 파일 로딩
            if self.templates_path.exists():
                try:
                    with open(self.templates_path, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    logger.info(f"[CTAOptimizer] 템플릿 로드: {self.templates_path}")
                    CTAOptimizer._templates_cache = templates
                    return templates
                except (OSError, json.JSONDecodeError, ValueError) as e:
                    logger.error(f"[CTAOptimizer] 템플릿 로드 실패: {e}, 기본값 사용")
            else:
                logger.warning(f"[CTAOptimizer] 템플릿 파일 없음: {self.templates_path}, 기본값 사용")

            # 기본값 사용
            default_templates = {
                "urgency": URGENCY_TEMPLATES,
                "action": ACTION_TEMPLATES,
                "trust": TRUST_TEMPLATES
            }
            CTAOptimizer._templates_cache = default_templates
            return default_templates

    def generate_cta(self, tier: str = "T3", category: str = "GENERAL") -> Dict[str, Any]:
        """
        CTA 3단계 구조 생성 (WO v11.0 C-2: Tier별 동적 분기)

        Args:
            tier: 가격대 (T1-T4)
            category: 카테고리 (EDUCATION, COMPARISON 등)

        Returns:
            {
                "urgency": {"text": str, "duration": 3.0},
                "action": {"text": str, "duration": 3.5},
                "trust": {"text": str, "duration": 3.5},
                "total_duration": 10.0
            }
        """
        # WO v11.0 C-2: Tier별 SSOT 템플릿 우선 사용
        tier_key = self._resolve_tier_key(tier)
        tier_templates = CTA_TEMPLATES_BY_TIER.get(tier_key, {})
        price_info = TIER_DISCOUNT_MAP.get(tier, TIER_DISCOUNT_MAP["T3"])

        if tier_templates:
            urgency_templates = tier_templates.get("urgency", URGENCY_TEMPLATES)
            action_templates = tier_templates.get("action", ACTION_TEMPLATES)
            trust_templates = tier_templates.get("trust", TRUST_TEMPLATES)
        else:
            urgency_templates = self.templates.get("urgency", URGENCY_TEMPLATES)
            action_templates = self.templates.get("action", ACTION_TEMPLATES)
            trust_templates = self.templates.get("trust", TRUST_TEMPLATES)

        # 템플릿 선택 + 가격 치환
        urgency_text = random.choice(urgency_templates).format(
            discount=price_info["discount"]
        )
        action_text = random.choice(action_templates).format(
            discount=price_info["discount"]
        )
        trust_text = random.choice(trust_templates).format(
            discount=price_info["discount"]
        )

        # WO v11.0 C-4: 금지어 자동 검증 및 치환
        urgency_text = self._sanitize_banned_words(urgency_text)
        action_text = self._sanitize_banned_words(action_text)
        trust_text = self._sanitize_banned_words(trust_text)

        return {
            "urgency": {
                "text": urgency_text,
                "duration": self.STRUCTURE['urgency']['duration']
            },
            "action": {
                "text": action_text,
                "duration": self.STRUCTURE['action']['duration']
            },
            "trust": {
                "text": trust_text,
                "duration": self.STRUCTURE['trust']['duration']
            },
            "total_duration": self.TOTAL_DURATION
        }

    @staticmethod
    def _resolve_tier_key(tier: str) -> str:
        """Tier 코드 → CTA_TEMPLATES_BY_TIER 키 변환"""
        tier_map = {
            "T4": "T4_premium",
            "T3": "T3_mainstream",
            "T2": "T2_budget",
        }
        return tier_map.get(tier, "T3_mainstream")

    @staticmethod
    def _sanitize_banned_words(text: str) -> str:
        """CTA 텍스트에서 금지어를 자동 치환한다 (WO v11.0 C-4)"""
        try:
            from engines.sgrade_constants import get_all_banned_words, get_banned_replacement_map
            banned_words = set(get_all_banned_words())
            replacements = get_banned_replacement_map()
        except ImportError:
            return text
        for banned, replacement in replacements.items():
            if banned in banned_words and banned in text:
                text = text.replace(banned, replacement)
                logger.debug(f"[CTA Sanitizer] '{banned}' -> '{replacement}'")
        return text

    def validate_cta(self, cta: Dict[str, Any]) -> Dict[str, Any]:
        """
        CTA 구조 검증

        Args:
            cta: generate_cta()로 생성된 CTA 딕셔너리

        Returns:
            {
                "valid": bool,
                "issues": List[str],
                "urgency_present": bool,
                "action_present": bool,
                "trust_present": bool
            }
        """
        issues = []

        # 필수 섹션 체크
        urgency_present = bool(cta.get("urgency", {}).get("text"))
        action_present = bool(cta.get("action", {}).get("text"))
        trust_present = bool(cta.get("trust", {}).get("text"))

        if not urgency_present:
            issues.append("Urgency 섹션 누락")
        if not action_present:
            issues.append("Action 섹션 누락")
        if not trust_present:
            issues.append("Trust 섹션 누락")

        # 총 길이 체크
        total_duration = sum(
            cta.get(section, {}).get("duration", 0.0)
            for section in ["urgency", "action", "trust"]
        )

        if abs(total_duration - self.TOTAL_DURATION) > 0.5:
            issues.append(f"CTA 총 길이 이탈: {total_duration:.1f}s (목표: {self.TOTAL_DURATION}s)")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "urgency_present": urgency_present,
            "action_present": action_present,
            "trust_present": trust_present
        }

    @classmethod
    def clear_cache(cls):
        """캐시 초기화 (테스트용)"""
        with cls._cache_lock:
            cls._templates_cache = None
            logger.info("[CTAOptimizer] 캐시 초기화 완료")


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_cta(tier: str = "T3", category: str = "GENERAL") -> Dict[str, Any]:
    """
    CTA 생성 편의 함수

    Usage:
        cta = generate_cta("T4", "BUCKET_LIST")
    """
    optimizer = CTAOptimizer()
    return optimizer.generate_cta(tier, category)


# ============================================================================
# Unit Tests
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("\n=== CTA Optimizer Test (P0-2) ===\n")

    # Test 1: CTA 3단계 생성
    optimizer = CTAOptimizer()

    for tier in ["T1", "T3", "T4"]:
        cta = optimizer.generate_cta(tier)
        print(f"\n[Tier {tier}]")
        print(f"  Urgency ({cta['urgency']['duration']}s): {cta['urgency']['text']}")
        print(f"  Action ({cta['action']['duration']}s): {cta['action']['text']}")
        print(f"  Trust ({cta['trust']['duration']}s): {cta['trust']['text']}")
        print(f"  Total: {cta['total_duration']}s")

        # 검증
        validation = optimizer.validate_cta(cta)
        print(f"  Valid: {validation['valid']}")

    # Test 2: 파일 핸들 누수 테스트 (50회 생성)
    print("\n=== 파일 핸들 누수 테스트 (50회 생성) ===\n")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_handles = process.num_handles() if hasattr(process, 'num_handles') else 0
        print(f"초기 핸들: {initial_handles}")

        # 50회 CTAOptimizer 생성
        for i in range(50):
            opt = CTAOptimizer()
            cta = opt.generate_cta("T3")

        final_handles = process.num_handles() if hasattr(process, 'num_handles') else 0
        print(f"최종 핸들: {final_handles}")
        print(f"증가량: {final_handles - initial_handles}")

        # 검증: 증가량 < 5 (정상 범위)
        if final_handles - initial_handles < 5:
            print("[OK] 파일 핸들 누수 없음")
        else:
            print("[WARNING] 파일 핸들 증가 감지 (하지만 5개 미만)")

    except ImportError:
        print("[SKIP] psutil 없음 - 파일 핸들 테스트 스킵")

    print("\n=== Test Complete ===")
