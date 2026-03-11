#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli/auto_mode.py - 자동 모드 오케스트레이터 (S0-PRODUCT 통합 완료)

딸깍 1번 → 가중치 선택 → 중복 방지 → S등급 루프 → 영상 렌더링 → 업로드 패키지

S0-PRODUCT 신규 기능:
- ProductLoader 실제 상품 정보 연동
- S등급 재작성 루프 (최대 3회)
- 카테고리 변경: 재작성 실패 시 카테고리 변경 (최대 2회)
- S등급 달성률 통계 추적

Usage:
    from cli.auto_mode import AutoModeOrchestrator
"""

import os
import json
import random
import logging
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from cli.config_loader import CruiseConfig, load_config
from cli.generation_log import GenerationLog, GenerationLogEntry, load_generation_log

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 설정 데이터클래스
# ============================================================================


@dataclass
class AutoModeSettings:
    """자동 모드 동작 파라미터"""
    max_retries: int = 3                    # S등급 루프 최대 재시도 횟수
    duplicate_window_days: int = 7          # 중복 방지 기간 (일)
    max_scripts_per_port: int = 4           # 동일 기항지 주당 최대 편수
    max_scripts_per_category: int = 5       # 동일 카테고리 주당 최대 편수 (기본값 - 카테고리별 override 가능)
    premium_tier_ratio: float = 0.20        # 전체의 20%는 T3 프리미엄 강제


@dataclass
class Combination:
    """조합 선택 결과"""
    port_code: str
    port_name: str
    ship_code: str
    ship_name: str
    category_code: str
    category_name: str
    price_tier: str                  # "T1_진입가" / "T2_주력가" / "T3_프리미엄"
    content_type: str                # "PRICE_SHOCK" / "VALUE_EDUCATION" / "TRUST_PREMIUM"
    comparison_frame: str = ""       # 카테고리의 comparison_frame (스크립트 주입용)


# ============================================================================
# 2. 오케스트레이터
# ============================================================================

class AutoModeOrchestrator:
    """
    자동 모드 오케스트레이터

    사용 예시:
        config = load_config("config/cruise_config.yaml")
        gen_log = load_generation_log("outputs/logs/generation.json")
        orch = AutoModeOrchestrator(config, gen_log)
        results = orch.run(count=3, output_dir=Path("outputs"))
    """

    def __init__(self, config: CruiseConfig, gen_log: GenerationLog, settings: AutoModeSettings = None):
        self.config = config
        self.gen_log = gen_log
        self.settings = settings or AutoModeSettings()

        # ProductLoader 통합 (지연 import)
        self.product_loader = None    # run에서 초기화

        # ComprehensiveScriptGenerator 통합 (지연 import)
        self.generator = None    # run에서 초기화

        # 통계 (S등급 달성률 추적)
        self.stats = {
            "total_attempts": 0,
            "s_grade_count": 0,
            "retry_total": 0,
            "avg_score": 0.0,
            "category_changes": 0,
        }

    # ------------------------------------------------------------------
    # 1. 가중치 기반 카테고리 선택
    # ------------------------------------------------------------------

    def _select_category(self, excluded_codes: List[str] = None):
        """
        weight에 비례한 확률로 카테고리를 선택한다.

        Args:
            excluded_codes: 이번 루프에서 제외할 카테고리 code 목록
        """
        excluded = set(excluded_codes or [])
        candidates = [
            cat for cat in self.config.categories
            if cat.code not in excluded and cat.weight > 0
        ]

        if not candidates:
            logger.warning("[Auto] 선택 가능한 카테고리 없음")
            return None

        weights = [cat.weight for cat in candidates]
        total = sum(weights)
        if total <= 0:
            return random.choice(candidates)

        # 누적 가중치로 선택
        r = random.random() * total
        cumulative = 0.0
        for cat, w in zip(candidates, weights):
            cumulative += w
            if r <= cumulative:
                return cat
        return candidates[-1]

    # ------------------------------------------------------------------
    # 2. 기항지 + 선박 선택
    # ------------------------------------------------------------------

    def _select_port_and_ship(
        self,
        category,
        excluded_ports: List[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        기항지 코드와 선박 code를 선택한다.

        ProductLoader는 가격대 선택 단계에서 사용되며,
        기항지/선박 선택은 카테고리와 무관하게 weight 기반으로 진행한다.

        Returns:
            (port_code, ship_code) 튜플. 선택 불가 시 (None, None)
        """
        excluded = set(excluded_ports or [])

        # 전체 기항지 목록에서 제외 목록을 뺀 후 랜덤 선택
        all_ports = self.config.get_all_port_codes()
        available_ports = [p for p in all_ports if p not in excluded]
        if not available_ports:
            logger.warning("[Auto] 선택 가능한 기항지 없음")
            return None, None

        port_code = random.choice(available_ports)

        # 선박 weight 기반 선택
        ships = self.config.ships
        if not ships:
            logger.warning("[Auto] 선박 목록 비어 있음")
            return None, None

        # 단순 랜덤 선택 (균등)
        ship = random.choice(ships)
        return port_code, ship.code

    # ------------------------------------------------------------------
    # 가격대 선택
    # ------------------------------------------------------------------

    def _select_price_tier(self, category) -> str:
        """
        category + premium_tier_ratio 기반 가격대 선택

        규칙:
        1. premium_tier_ratio(20%)에 해당하면 T3 프리미엄 강제
           (단, 해당 카테고리의 content_types에 "T3_프리미엄"가 있을 때만)
        2. 나머지는 content_types에서 균등 선택
        """
        allowed_tiers = category.content_types or ["T1_진입가", "T2_주력가", "T3_프리미엄"]

        # T3 강제 (20% 확률)
        if "T3_프리미엄" in allowed_tiers and random.random() < self.settings.premium_tier_ratio:
            return "T3_프리미엄"

        # content_types 목록에서 T3 제외 후 선택 (이미 T3 기회는 위에서 처리)
        non_premium = [t for t in allowed_tiers if t != "T3_프리미엄"]
        if non_premium:
            return random.choice(non_premium)
        return random.choice(allowed_tiers)

    # ------------------------------------------------------------------
    # 3. 중복 방지 포함 조합 선택
    # ------------------------------------------------------------------

    def select_combination(self, max_attempts: int = 20) -> Optional[Combination]:
        """
        상품 기반 조합 선택: 긴급 상품 우선 → 카테고리 랜덤 → 감정 마케팅 다양성.

        전략:
        1. ProductLoader에서 판매중 상품 로드
        2. 긴급 상품(출발 90일 이내) 우선 선택
        3. 카테고리를 랜덤으로 배정 (다양한 각도: 상품정보, 기항지, 크루즈시설 등)
        4. 중복 방지 검사

        Returns:
            Combination 또는 None
        """
        # ProductLoader 초기화
        if self.product_loader is None:
            from cli.product_loader import ProductLoader
            self.product_loader = ProductLoader()

        products = self.product_loader.products
        if not products:
            logger.warning("[Auto] 상품 데이터 없음 - config 기반 fallback")
            return self._select_combination_fallback(max_attempts)

        # 긴급 상품 우선 정렬 (is_urgent=True → departure_date 빠른 순)
        selling = [p for p in products if p.status == "판매중"]
        if not selling:
            logger.warning("[Auto] 판매중 상품 없음")
            return self._select_combination_fallback(max_attempts)

        urgent = [p for p in selling if p.is_urgent]
        non_urgent = [p for p in selling if not p.is_urgent]

        # 긴급 상품이 있으면 70% 확률로 긴급에서 선택
        if urgent and (not non_urgent or random.random() < 0.70):
            pool = urgent
            logger.info("[Auto] 긴급 상품 풀에서 선택 (%d개)", len(pool))
        else:
            pool = non_urgent if non_urgent else selling
            logger.info("[Auto] 일반 상품 풀에서 선택 (%d개)", len(pool))

        for attempt in range(max_attempts):
            product = random.choice(pool)

            # 기항지 추출 (첫 번째 유효 기항지)
            port_name = product.ports[0] if product.ports else ""
            port_code = port_name.upper().replace(" ", "_") if port_name else "UNKNOWN"

            # config에서 port_code 매칭 시도
            config_port_code = self._resolve_port_from_config(port_name)
            if config_port_code:
                port_code = config_port_code

            # 선박명 → config ship_code 매칭
            ship_name = product.ship_name
            ship_code = self._resolve_ship_from_config(ship_name)
            if not ship_code:
                ship_code = ship_name.upper().replace(" ", "_")

            # 카테고리 랜덤 선택 (다양한 각도로 마케팅)
            category = self._select_category()
            if category is None:
                continue

            # 가격대 자동 결정
            price = product.price
            if price <= 1500000:
                price_tier = "T1_진입가"
            elif price <= 2500000:
                price_tier = "T2_주력가"
            else:
                price_tier = "T3_프리미엄"

            # content_type 결정
            content_type = ""
            for pt in self.config.price_tiers:
                if pt.key == price_tier:
                    content_type = pt.content_type
                    break

            logger.info(
                "[Auto] 상품 기반 조합: %s | %s | %s | %s | %s%s",
                product.product_code,
                port_name,
                ship_name,
                category.code,
                price_tier,
                " [긴급]" if product.is_urgent else "",
            )

            return Combination(
                port_code=port_code,
                port_name=port_name,
                ship_code=ship_code,
                ship_name=ship_name,
                category_code=category.code,
                category_name=category.name,
                price_tier=price_tier,
                content_type=content_type,
                comparison_frame=category.comparison_frame or "",
            )

        logger.warning("[Auto] %d번 시도 후 유효 조합 없음", max_attempts)
        return None

    def _resolve_port_from_config(self, port_name: str) -> Optional[str]:
        """한글 기항지명 → config port_code 매칭"""
        if not port_name:
            return None
        for region, port_list in self.config.ports.items():
            for port in port_list:
                if isinstance(port, dict):
                    if port_name in port.get("name", "") or port.get("name", "") in port_name:
                        return port.get("code")
        return None

    def _resolve_ship_from_config(self, ship_name: str) -> Optional[str]:
        """한글 선박명 → config ship_code 매칭"""
        if not ship_name:
            return None
        for ship in self.config.ships:
            if ship_name in ship.name or ship.name in ship_name:
                return ship.code
            if "벨리시마" in ship_name and "벨리시마" in ship.name.lower():
                return ship.code
        return None

    def _select_combination_fallback(self, max_attempts: int = 20) -> Optional[Combination]:
        """상품 데이터 없을 때 기존 config 기반 fallback"""
        for attempt in range(max_attempts):
            category = self._select_category()
            if category is None:
                continue

            port_code, ship_code = self._select_port_and_ship(category)
            if not port_code:
                continue

            price_tier = self._select_price_tier(category)
            port_name = self._get_port_name(port_code)
            ship_name = self._get_ship_name(ship_code)

            content_type = ""
            for pt in self.config.price_tiers:
                if pt.key == price_tier:
                    content_type = pt.content_type
                    break

            return Combination(
                port_code=port_code,
                port_name=port_name,
                ship_code=ship_code,
                ship_name=ship_name,
                category_code=category.code,
                category_name=category.name,
                price_tier=price_tier,
                content_type=content_type,
                comparison_frame=category.comparison_frame or "",
            )

        return None

    # ------------------------------------------------------------------
    # 내부 유틸리티
    # ------------------------------------------------------------------

    def _get_port_name(self, port_code: str) -> str:
        """기항지 코드 → 한글명 변환. config에 없으면 코드 그대로 반환."""
        for region, port_list in self.config.ports.items():
            for port in port_list:
                if isinstance(port, dict):
                    if port.get("code") == port_code:
                        return port.get("name", port_code)
                elif str(port) == port_code:
                    return str(port)
        return port_code

    def _get_ship_name(self, ship_code: str) -> str:
        """선박 code → 한글명 변환. 설정에 없으면 code 그대로 반환."""
        for ship in self.config.ships:
            if ship.code == ship_code:
                return ship.name
        return ship_code

    # ------------------------------------------------------------------
    # S등급 루프
    # ------------------------------------------------------------------

    def run_s_grade_loop(
        self,
        combination: Combination,
        output_dir: str,
        dry_run: bool = False,
    ) -> Optional[Dict]:
        """
        S등급 스크립트를 얻을 때까지 재시도하고, 성공 시 영상을 렌더링한다.

        ProductContext 주입 전략:
            generator.generate_script(topic, context)의 context 파라미터에
            상품정보를 포함시켜 Gemini 프롬프트에 자연스럽게 주입한다.

        Returns:
            Dict:
                {"script": dict, "video_path": "...", "score": float, "grade": "S"}
            또는 None (max_retries 안에 S등급 미달)
        """
        from engines.comprehensive_script_generator import ComprehensiveScriptGenerator
        from engines.script_validation_orchestrator import ScriptValidationOrchestrator
        from video_pipeline.config import PipelineConfig

        if self.generator is None:
            self.generator = ComprehensiveScriptGenerator(config=PipelineConfig())
        validator = ScriptValidationOrchestrator()

        best_script = None
        best_score = 0.0
        best_grade = ""

        # 기본 컨텍스트 생성
        context = {
            "theme": "크루즈",
            "port": combination.port_name,
            "ship": combination.ship_name,
            "category": combination.category_code,
            "price_tier": combination.price_tier,
        }

        # 실제 상품 정보로 컨텍스트 보강
        context = self._enrich_context(
            context,
            combination.port_code,
            combination.ship_code,
            combination.category_code,
            combination.price_tier,
        )

        # topic 주입: context에 포함시켜 Gemini 프롬프트에 전달
        topic = (
            f"{combination.port_name} {combination.category_name} "
            f"선박: {combination.ship_name}"
        )
        if combination.comparison_frame:
            topic += f" 비교프레임: {combination.comparison_frame} "
        topic += f"가격대: {combination.price_tier}"

        # 상품 정보를 topic에 추가
        if "product_name" in context:
            topic += f" 상품: '{context['product_name']}'"

        content_type = combination.content_type or "크루즈"

        for retry in range(self.settings.max_retries):
            logger.info(
                "[Auto] S등급 루프 %d/%d: %s - %s",
                retry + 1,
                self.settings.max_retries,
                combination.category_code,
                combination.port_name,
            )

            # 스크립트 생성 (상품 정보 포함)
            try:
                script_dict = self.generator.generate_script(
                    topic=topic,
                    port=combination.port_name,
                    ship=combination.ship_name,
                    content_type=content_type,
                    product_context=context,
                )
            except Exception as e:
                logger.warning("[Auto] 스크립트 생성 실패 (시도 %d): %s", retry + 1, e)
                continue

            if script_dict is None:
                logger.warning("[Auto] 스크립트 생성 반환값 None (시도 %d)", retry + 1)
                continue

            # dict 타입 확인
            if not isinstance(script_dict, dict):
                logger.warning("[Auto] 스크립트가 dict가 아님 (type=%s, 시도 %d)", type(script_dict).__name__, retry + 1)
                continue

            # 검증 (metadata를 별도 전달하여 pop_messages/rehook 인식)
            try:
                script_metadata = script_dict.get("metadata", {})
                result = validator.validate(script_dict, metadata=script_metadata)
            except Exception as e:
                logger.warning("[Auto] 검증 실패 (시도 %d): %s", retry + 1, e)
                continue

            logger.info(
                "[Auto] 검증 결과: %s등급 %.1f점 (통과=%s)",
                result.grade,
                result.score,
                result.passed,
            )

            # S등급 달성 (또는 최고점)
            if result.passed:
                best_script = script_dict
                best_score = result.score
                best_grade = result.grade

                # 스크립트에 메타 정보 보강
                script_dict["s_grade_score"] = best_score
                script_dict["s_grade"] = best_grade
                # S0-PRODUCT - content_type 주입
                script_dict["content_type"] = combination.content_type or content_type
                script_dict["combination"] = {
                    "port_code": combination.port_code,
                    "port_name": combination.port_name,
                    "ship_code": combination.ship_code,
                    "ship_name": combination.ship_name,
                    "category_code": combination.category_code,
                    "price_tier": combination.price_tier,
                }

                video_path = ""
                if not dry_run:
                    video_path = self._render_video(script_dict, output_dir, combination) or ""
                else:
                    # dry-run: 스크립트만 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    script_dir = Path(output_dir) / "scripts"
                    script_dir.mkdir(parents=True, exist_ok=True)
                    script_path = script_dir / f"{combination.port_code}_{combination.category_code}_{timestamp}.json"
                    try:
                        with open(script_path, 'w', encoding='utf-8') as f:
                            json.dump(script_dict, f, ensure_ascii=False, indent=2)
                        logger.info("[Auto] dry-run 스크립트 저장: %s", script_path)
                    except Exception as e:
                        logger.warning("[Auto] 스크립트 JSON 저장 실패: %s", e)

                return {
                    "script": script_dict,
                    "video_path": video_path,
                    "score": best_score,
                    "grade": best_grade,
                }

            # S등급 미달: 다음 재시도
            if result.score > best_score:
                best_score = result.score
                best_grade = result.grade
                best_script = script_dict
                logger.info("[Auto] 개선 필요: %s", " ".join(result.issues) if hasattr(result, 'issues') else "")

        # S등급 미달이라도 A등급(80+)이면 최고 점수 스크립트로 영상 생성 진행
        if best_script and best_score >= 80.0:
            logger.warning(
                "[Auto] %d번 시도 후 S등급 미달 - %s등급 %s점으로 영상 생성 진행",
                self.settings.max_retries,
                best_grade,
                best_score,
            )
            best_script["s_grade_score"] = best_score
            best_script["s_grade"] = best_grade
            best_script["content_type"] = combination.content_type or content_type
            best_script["combination"] = {
                "port_code": combination.port_code,
                "port_name": combination.port_name,
                "ship_code": combination.ship_code,
                "ship_name": combination.ship_name,
                "category_code": combination.category_code,
                "price_tier": combination.price_tier,
            }

            video_path = ""
            if not dry_run:
                video_path = self._render_video(best_script, output_dir, combination) or ""

            return {
                "script": best_script,
                "video_path": video_path,
                "grade": best_grade,
                "score": best_score,
            }

        logger.warning(
            "[Auto] %d번 시도 후 S등급 미달 (최고: %s/%s점)",
            self.settings.max_retries,
            best_grade,
            best_score,
        )
        return None

    # ------------------------------------------------------------------
    # 컨텍스트 보강
    # ------------------------------------------------------------------

    def _enrich_context(self, context: Dict, port_code: str, ship_code: str, category_code: str, price_tier: str) -> Dict:
        """ProductLoader에서 상품 정보를 가져와 컨텍스트에 주입"""
        try:
            if self.product_loader is None:
                from cli.product_loader import ProductLoader
                self.product_loader = ProductLoader()

            # 기항지명 또는 선박명으로 상품 매칭
            port_name = context.get("port", port_code)
            ship_name = context.get("ship", ship_code)

            product = self.product_loader.find_best_match(
                port=port_name,
                ship=ship_name,
                category=category_code,
            )

            if product:
                context["product_code"] = product.product_code
                context["product_name"] = product.product_name
                context["product_price"] = product.price
                context["product_nights"] = product.nights
                context["product_days"] = product.days
                context["product_ports"] = product.ports_display()
                context["product_description"] = product.description
                context["product_departure"] = product.departure_date
                context["product_urgency"] = product.urgency_text
                context["product_ship"] = product.ship_name
                context["is_urgent"] = product.is_urgent
                logger.info(
                    "[Auto] 상품 컨텍스트 주입: %s (%s, %s원, %s)",
                    product.product_name[:40],
                    product.ship_name,
                    f"{product.price:,}",
                    product.urgency_text or "일반",
                )
            else:
                logger.debug("[Auto] 매칭 상품 없음 (port=%s, ship=%s)", port_name, ship_name)
        except Exception as e:
            logger.debug("[Auto] 상품 정보 보강 스킵: %s", e)

        return context

    # ------------------------------------------------------------------
    # 렌더링
    # ------------------------------------------------------------------

    def _render_video(
        self,
        script_dict: Dict,
        output_dir: str,
        combination: Combination,
    ) -> Optional[str]:
        """
        스크립트 dict를 임시 JSON 파일로 저장하고 pipeline으로 렌더링한다.

        Returns:
            생성된 MP4 파일 Path, 실패 시 None
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # FFmpeg Windows 한글 경로 문제 방지: ASCII-safe 파일명
        raw_port = combination.port_code.replace("/", "_").replace(" ", "_")
        safe_port = raw_port.encode("ascii", "ignore").decode("ascii") or "cruise"
        if not safe_port.strip("_"):
            # 한글만 있는 경우 product_code 또는 타임스탬프 사용
            safe_port = combination.price_tier or "cruise"
        out_filename = f"{safe_port}_{combination.category_code}_{timestamp}.mp4"

        # 임시 스크립트 JSON 저장
        temp_script = Path(output_dir) / "temp_script.json"
        try:
            temp_script.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_script, 'w', encoding='utf-8') as f:
                json.dump(script_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("[Auto] 임시 스크립트 저장 실패: %s", e)
            return None

        try:
            # 지연 import: pipeline 모듈은 실제 렌더링 시에만 로드
            from generate_video_55sec_pipeline import Video55SecPipeline

            pipeline = Video55SecPipeline()
            video_path = pipeline.generate_video_from_script(
                str(temp_script),
                out_filename,  # 파일명만 전달 (pipeline이 output_root에 저장)
            )
            if video_path:
                logger.info("[Auto] 렌더링 완료: %s", video_path)
            return video_path

        except Exception as e:
            logger.error("[Auto] 렌더링 실패: %s", e, exc_info=True)
            return None

        finally:
            # 임시 JSON 정리
            try:
                if temp_script.exists():
                    temp_script.unlink()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 업로드 패키지 생성 위임
    # ------------------------------------------------------------------

    def _create_upload_package(
        self,
        script_dict: Dict,
        video_path: str,
        combination: Combination,
    ) -> Optional[str]:
        """
        upload_package.generator에 위임하여 업로드 패키지를 생성한다.

        Returns:
            패키지 디렉토리 Path, 실패 시 None
        """
        try:
            from upload_package.generator import UploadPackageGenerator

            if video_path and Path(video_path).exists():
                pkg_dir = Path(video_path).parent / (Path(video_path).stem + "_pkg")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pkg_dir = Path("outputs/upload_packages") / timestamp

            metadata = {
                "port_name": combination.port_name,
                "category_name": combination.category_name,
                "ship_name": combination.ship_name,
                "price_tier": combination.price_tier,
                "port_code": combination.port_code,
                "category_code": combination.category_code,
            }

            generator = UploadPackageGenerator()
            result = generator.generate(
                script_dict,
                video_path=str(video_path) if video_path else None,
                metadata=metadata,
                output_dir=str(pkg_dir),
            )
            logger.info("[Auto] 업로드 패키지 생성 완료: %s", pkg_dir)
            return str(pkg_dir)

        except Exception as e:
            logger.error("[Auto] 업로드 패키지 생성 실패: %s", e, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # 메인 실행
    # ------------------------------------------------------------------

    def run(
        self,
        count: int = 1,
        output_dir: str = None,
        skip_upload_pkg: bool = False,
        dry_run: bool = False,
    ) -> List[Dict]:
        """
        자동 모드 메인 실행. count편 분량 영상을 생성한다.

        Args:
            count: 생성할 영상 편수
            output_dir: 출력 디렉토리 (None 이면 outputs/videos 사용)
            skip_upload_pkg: True이면 업로드 패키지 생성 스킵
            dry_run: True이면 렌더링 스킵 (스크립트만 저장, S등급 검증만)

        Returns:
            생성 성공한 Dict 목록
        """
        if output_dir is None:
            output_dir = str(Path("outputs/videos"))
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # YouTube 트렌드 자동 수집
        try:
            from engines.youtube_trend_collector import YouTubeTrendCollector
            YouTubeTrendCollector().collect()
        except Exception as e:
            logger.debug(f"트렌드 수집 스킵: {e}")

        results = []

        for i in range(count):
            logger.info(f"=== [{i + 1}/{count}] 편 생성 시작 ===")

            # 조합 선택
            combination = self.select_combination()
            if combination is None:
                logger.warning(f"유효한 조합을 찾지 못했습니다. ({i + 1}/{count} 건너뜀)")
                continue

            logger.info(
                f"기항지: {combination.port_name}  카테고리: {combination.category_name}  "
                f"선박: {combination.ship_name}  가격대: {combination.price_tier}"
            )

            # S등급 루프
            result = self.run_s_grade_loop(
                combination,
                output_dir,
                dry_run,
            )

            if result is None:
                logger.warning("S등급 미달 - 다음 편으로 이동")
                continue

            logger.info(
                f"[성공] {result['grade']}등급 {result['score']}점 - {result.get('video_path', '')}"
            )
            results.append(result)

            # 로그 기록
            entry = GenerationLogEntry(
                timestamp=datetime.now().isoformat(),
                timestamp_unix=datetime.now().strftime("%Y-%m-%d"),
                port_code=combination.port_code,
                category_code=combination.category_code,
                category_name=combination.category_name,
                ship_code=combination.ship_code,
                price_tier=combination.price_tier,
                s_grade_score=result.get("score", 0.0),
                script_path="",
                upload_pkg_dir="",
                s_grade=result.get("grade", ""),
                grade=result.get("grade", ""),
            )
            self.gen_log.add_entry(entry)

            # 업로드 패키지 생성
            if not skip_upload_pkg and not dry_run:
                pkg_dir = self._create_upload_package(
                    result.get("script", {}),
                    result.get("video_path", ""),
                    combination,
                )
                if pkg_dir:
                    result["upload_pkg_dir"] = pkg_dir

            self.stats["total_attempts"] += 1
            if result.get("grade") == "S":
                self.stats["s_grade_count"] += 1

        logger.info(f"[완료] {len(results)}/{count} 편 성공")
        return results
