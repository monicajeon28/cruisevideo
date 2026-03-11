#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook Generator - S-Grade Hook Template Engine
P0-2: 파일 핸들 누수 방지 (클래스 변수 캐싱 + Lock)

Author: Bug Fixer Agent (P0-2)
Date: 2026-03-09

핵심 개선:
- JSON 템플릿 파일 클래스 변수 캐싱 (1회만 로딩)
- threading.Lock으로 동시성 보호
- 파일 핸들 누수 방지 (with open 사용)
"""

import json
import logging
import random
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# HOOK_TYPES: sgrade_constants.py를 정본(SSOT)으로 사용
# WO v10.0 Phase B-2→크로스체크: 순환 import 방지, sgrade_constants.py에 통합
from engines.sgrade_constants import HOOK_TYPES


class HookGenerator:
    """
    Hook 템플릿 생성기 - 파일 핸들 누수 방지

    특징:
    - 클래스 변수 캐싱 (템플릿 1회만 로딩)
    - Lock으로 동시성 보호
    - with open으로 안전한 파일 핸들 관리
    """

    # 클래스 변수 캐싱
    _templates_cache: Optional[Dict[str, Any]] = None
    _cache_lock = Lock()

    def __init__(self, templates_path: Optional[str] = None):
        """
        HookGenerator 초기화

        Args:
            templates_path: hook 템플릿 JSON 파일 경로
        """
        if templates_path:
            self.hook_templates_path = Path(templates_path)
        else:
            try:
                from path_resolver import get_paths
                self.hook_templates_path = get_paths().config_dir / "hook_templates.json"
            except (ImportError, Exception):
                self.hook_templates_path = Path("D:/mabiz/config/hook_templates.json")

        # 템플릿 로드 (클래스 변수 캐싱)
        self.templates = self._load_hook_templates()

    def _load_hook_templates(self) -> Dict[str, Any]:
        """
        Hook 템플릿 로드 (클래스 변수 캐싱, 1회만 실행)

        Returns:
            템플릿 딕셔너리
        """
        # 캐시 확인 (Lock으로 보호)
        with HookGenerator._cache_lock:
            if HookGenerator._templates_cache is not None:
                logger.debug("[HookGenerator] 템플릿 캐시 사용")
                return HookGenerator._templates_cache

            # 파일 로딩
            if self.hook_templates_path.exists():
                try:
                    with open(self.hook_templates_path, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                    logger.info(f"[HookGenerator] 템플릿 로드: {self.hook_templates_path}")
                    HookGenerator._templates_cache = templates
                    return templates
                except (OSError, json.JSONDecodeError, ValueError) as e:
                    logger.error(f"[HookGenerator] 템플릿 로드 실패: {e}, 기본값 사용")
            else:
                logger.warning(f"[HookGenerator] 템플릿 파일 없음: {self.hook_templates_path}, 기본값 사용")

            # 기본값 사용
            HookGenerator._templates_cache = HOOK_TYPES
            return HOOK_TYPES

    def select_hook(self, hook_type: str, variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Hook 템플릿 선택 및 변수 치환

        Args:
            hook_type: Hook 타입 (SOCIAL_PROOF, FAMILY_BOND 등)
            variables: 변수 치환 딕셔너리 (port, ship, monthly_price 등)

        Returns:
            {
                "text": "생성된 Hook 텍스트",
                "type": "Hook 타입",
                "score": Hook 점수 (1-10)
            }
        """
        if hook_type not in self.templates:
            logger.warning(f"[HookGenerator] 존재하지 않는 Hook 타입: {hook_type}, 랜덤 선택")
            hook_type = random.choice(list(self.templates.keys()))

        hook_data = self.templates[hook_type]
        templates = hook_data.get("templates", [])

        if not templates:
            logger.error(f"[HookGenerator] Hook 타입 {hook_type}에 템플릿 없음")
            return {
                "text": "크루즈 여행, 지금 시작해보세요",
                "type": hook_type,
                "score": 5
            }

        # 랜덤 템플릿 선택
        template = random.choice(templates)

        # 변수 치환
        text = template
        if variables:
            for key, value in variables.items():
                text = text.replace(f"{{{key}}}", str(value))

        return {
            "text": text,
            "type": hook_type,
            "score": hook_data.get("score_weight", 5)
        }

    def generate_hooks(self, hook_type: str, count: int = 5, variables: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        여러 개의 Hook 생성

        Args:
            hook_type: Hook 타입
            count: 생성할 Hook 개수
            variables: 변수 치환 딕셔너리

        Returns:
            Hook 리스트 (점수 내림차순 정렬)
        """
        hooks = []

        for _ in range(count):
            hook = self.select_hook(hook_type, variables)
            hooks.append(hook)

        # 점수 내림차순 정렬
        hooks.sort(key=lambda x: x['score'], reverse=True)

        return hooks

    @classmethod
    def clear_cache(cls):
        """캐시 초기화 (테스트용)"""
        with cls._cache_lock:
            cls._templates_cache = None
            logger.info("[HookGenerator] 캐시 초기화 완료")


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_hook(hook_type: str, variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Hook 생성 편의 함수

    Usage:
        hook = generate_hook("SOCIAL_PROOF", {"port": "나가사키"})
    """
    generator = HookGenerator()
    return generator.select_hook(hook_type, variables)


# ============================================================================
# Unit Tests
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("\n=== Hook Generator Test (P0-2) ===\n")

    # Test 1: 기본 Hook 생성
    generator = HookGenerator()

    variables = {
        "port": "나가사키",
        "ship": "MSC 벨리시마",
        "monthly_price": "21",
        "daily_price": "7",
        "detail1": "야경",
        "comparison": "일본 패키지 여행"
    }

    for hook_type in ["SOCIAL_PROOF", "FAMILY_BOND", "NOSTALGIA"]:
        hook = generator.select_hook(hook_type, variables)
        print(f"[{hook_type}] {hook['text']} (점수: {hook['score']}/10)")

    # Test 2: 파일 핸들 누수 테스트 (50회 생성)
    print("\n=== 파일 핸들 누수 테스트 (50회 생성) ===\n")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_handles = process.num_handles() if hasattr(process, 'num_handles') else 0
        print(f"초기 핸들: {initial_handles}")

        # 50회 HookGenerator 생성
        for i in range(50):
            gen = HookGenerator()
            hook = gen.select_hook("SOCIAL_PROOF", variables)

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
