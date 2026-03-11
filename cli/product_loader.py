#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli/product_loader.py - 크루즈 상품 정보 로더

CruiseDot의 실제 상품 정보를 JSON에서 로드하고,
기항지/선박/카테고리별로 조회 가능한 인터페이스를 제공한다.

스크립트 생성 시 실제 상품의 가격, 일정, 프로모션 정보를 컨텍스트에 주입하여
더욱 구체적이고 정확한 콘텐츠를 생성할 수 있도록 지원한다.

Usage:
    from cli.product_loader import ProductLoader
"""

import logging

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import os

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 상품 데이터클래스
# ============================================================================


@dataclass
class CruiseProduct:
    """크루즈 상품 정보"""
    product_code: str
    product_name: str
    ship_name: str
    category: str
    price: int
    nights: int
    days: int
    ports: List[str]
    description: str
    status: str
    is_popular: bool = False
    is_recommended: bool = False
    is_urgent: bool = False
    promo_text: str = ""
    urgency_text: str = ""
    departure_date: str = ""

    @property
    def monthly_price(self) -> int:
        """월 환산 가격 (박일 → 일 기준)"""
        if self.nights <= 0:
            return self.price
        return int((self.price / self.nights) * 30)

    @property
    def price_tier(self) -> str:
        """가격대 분류 (체험/실속/프리미엄/럭셔리/울트라)"""
        if self.price <= 500000:
            return "체험"
        if self.price <= 1500000:
            return "실속"
        if self.price <= 3000000:
            return "프리미엄"
        if self.price <= 5000000:
            return "럭셔리"
        return "울트라"

    def get_promo_tag(self) -> str:
        """프로모션 태그 추출 (예: "예약폭주", "매진임박")"""
        # promo_text에서 이모지 태그 추출
        for emoji in ["\U0001f525", "\U0001f680", "\u2b50"]:
            if emoji in self.promo_text:
                start = self.promo_text.index(emoji)
                if start + 1 < len(self.promo_text):
                    end = self.promo_text.index(emoji, start + 1) if emoji in self.promo_text[start + 1:] else -1
                    if end > 0:
                        return self.promo_text[start + 1:end].strip()
                    else:
                        # 두 번째 이모지가 없으면 첫 이모지만 반환
                        return ""
        for emoji in ["\U0001f4a5", "\U0001f31f", "\U0001f4ab"]:
            if emoji in self.promo_text:
                start = self.promo_text.index(emoji)
                if start + 1 < len(self.promo_text):
                    end = self.promo_text.index(emoji, start + 1) if emoji in self.promo_text[start + 1:] else -1
                    if end > 0:
                        return self.promo_text[start + 1:end].strip()
                    else:
                        return ""
        for emoji in ["\u26a1", "\U0001f4a8", "\u2728"]:
            if emoji in self.promo_text:
                start = self.promo_text.index(emoji)
                if start + 1 < len(self.promo_text):
                    end = self.promo_text.index(emoji, start + 1) if emoji in self.promo_text[start + 1:] else -1
                    if end > 0:
                        return self.promo_text[start + 1:end].strip()
                    else:
                        return ""
        if self.urgency_text:
            return self.urgency_text
        return ""

    def has_urgency(self) -> bool:
        """긴급성 메시지 포함 여부"""
        keywords = ["매진", "임박", "폭주", "유일한", "잔여"]
        return any(kw in self.urgency_text for kw in keywords)

    def ports_display(self) -> str:
        """기항지 목록 한글 문자열 (예: "라벤나, 코토르, 아테네")"""
        return ", ".join(self.ports)

    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "ship_name": self.ship_name,
            "category": self.category,
            "price": self.price,
            "nights": self.nights,
            "days": self.days,
            "ports": self.ports,
            "description": self.description,
            "status": self.status,
            "is_popular": self.is_popular,
            "is_recommended": self.is_recommended,
            "promo_text": self.promo_text,
            "urgency_text": self.urgency_text,
            "departure_date": self.departure_date,
            "monthly_price": self.monthly_price,
            "price_tier": self.price_tier,
            "promo_tag": self.get_promo_tag(),
            "ports_display": self.ports_display(),
        }


# ============================================================================
# 2. 상품 로더
# ============================================================================

class ProductLoader:
    """크루즈 상품 정보 로더"""

    def __init__(self, json_path: str = None, auto_sync: bool = True):
        """
        Args:
            json_path: JSON 파일 경로 (None이면 기본 경로)
            auto_sync: 24시간 경과 시 자동 동기화 (기본 True)
        """
        if json_path is None:
            json_path = Path(__file__).parent.parent / "data" / "products.json"

        self.json_path = Path(json_path)
        self.products: List[CruiseProduct] = []

        # 자동 동기화 체크 (24시간 경과 시)
        if auto_sync:
            self._check_auto_sync()

        self._load_products()

    def _check_auto_sync(self) -> None:
        """24시간 경과 시 자동 동기화"""
        try:
            if not self.json_path.exists():
                return

            import time
            age_hours = (time.time() - self.json_path.stat().st_mtime) / 3600

            if age_hours > 24:
                logger.info(
                    "[ProductLoader] 설정 파일 오래됨 (%.1f시간 경과). 자동 동기화 실행...",
                    age_hours
                )
                self._load_products()
                try:
                    os.utime(self.json_path)
                    logger.info("[ProductLoader] 자동 동기화 완료")
                except Exception:
                    pass
            else:
                logger.debug(
                    "[ProductLoader] 설정 파일 최신 상태 (%.1f시간 전)",
                    age_hours
                )
        except Exception as e:
            logger.warning(
                "[ProductLoader] 자동 동기화 실패 (기존 설정 사용): %s",
                e
            )

    def _load_products(self) -> None:
        """JSON에서 상품 목록 로드"""
        if not self.json_path.exists():
            logger.warning(
                "[ProductLoader] 설정 파일 없음: %s",
                self.json_path
            )
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("products", data)
            skipped = 0
            for item in items:
                status = item.get("status", "판매중")
                # 판매중인 상품만 로드 (판매종료/판매대기 제외)
                if status not in ("판매중",):
                    skipped = skipped + 1
                    continue
                product = CruiseProduct(
                    item.get("product_code", ""),
                    item.get("product_name", ""),
                    item.get("ship_name", ""),
                    item.get("category", ""),
                    item.get("price", 0),
                    item.get("nights", 0),
                    item.get("days", 0),
                    item.get("ports", []),
                    item.get("description", ""),
                    status,
                    item.get("is_popular", False),
                    item.get("is_recommended", False),
                    item.get("is_urgent", False),
                    item.get("promo_text", ""),
                    item.get("urgency_text", ""),
                    item.get("departure_date", ""),
                )
                self.products.append(product)
            if skipped:
                logger.debug("[ProductLoader] 비판매 상품 %d개 제외", skipped)

            logger.info(
                "[ProductLoader] 상품 %d개 로드 완료 (from %s)",
                len(self.products),
                self.json_path.name
            )

        except Exception as e:
            logger.error(
                "[ProductLoader] 상품 로드 실패: %s",
                e,
                exc_info=True
            )

    # ------------------------------------------------------------------
    # 조회 메서드
    # ------------------------------------------------------------------

    def get_product(self, product_code: str) -> Optional[CruiseProduct]:
        """상품 코드로 단일 상품 조회"""
        for product in self.products:
            if product.product_code == product_code:
                return product
        return None

    def search_by_port(
        self,
        port_name: str,
        limit: int = 5
    ) -> List[CruiseProduct]:
        """
        기항지로 상품 조회

        Args:
            port_name: 기항지명 (예: "산토리니", "라벤나")
            limit: 최대 반환 개수

        Returns:
            해당 기항지를 포함하는 상품 목록 (인기순/추천순 우선)
        """
        results = [
            p for p in self.products
            if port_name in p.ports
        ]

        # 정렬: is_popular → is_recommended → price (낮은 순)
        results.sort(
            key=lambda p: (
                not p.is_popular,
                not p.is_recommended,
                p.price if p.price > 0 else float('inf')
            )
        )

        return results[:limit]

    def search_by_ship(
        self,
        ship_name: str,
        limit: int = 5
    ) -> List[CruiseProduct]:
        """
        선박명으로 상품 조회

        Args:
            ship_name: 선박명 (예: "익스플로러 오브 더 시즈")
            limit: 최대 반환 개수

        Returns:
            해당 선박의 상품 목록
        """
        results = [
            p for p in self.products
            if ship_name.lower() in p.ship_name.lower()
            or p.ship_name.lower() in ship_name.lower()
        ]

        results.sort(
            key=lambda p: (
                not p.is_popular,
                not p.is_recommended,
                p.price if p.price > 0 else float('inf')
            )
        )

        return results[:limit]

    def search_by_category(
        self,
        category: str,
        limit: int = 5
    ) -> List[CruiseProduct]:
        """
        카테고리로 상품 조회

        Args:
            category: 카테고리 (예: "지중해", "알래스카")
            limit: 최대 반환 개수

        Returns:
            해당 카테고리의 상품 목록
        """
        results = [
            p for p in self.products
            if category.lower() in p.category.lower()
            or p.category.lower() in category.lower()
        ]

        results.sort(
            key=lambda p: (
                not p.is_popular,
                not p.is_recommended,
                p.price if p.price > 0 else float('inf')
            )
        )

        return results[:limit]

    def search_by_price_tier(
        self,
        price_tier: str,
        limit: int = 5
    ) -> List[CruiseProduct]:
        """
        가격대로 상품 조회

        Args:
            price_tier: "실속" / "프리미엄" / "럭셔리" / "울트라"
            limit: 최대 반환 개수

        Returns:
            해당 가격대의 상품 목록
        """
        results = [
            p for p in self.products
            if p.price_tier == price_tier
        ]

        results.sort(
            key=lambda p: (
                not p.is_popular,
                not p.is_recommended,
                p.price
            )
        )

        return results[:limit]

    def find_best_match(
        self,
        port: str = None,
        ship: str = None,
        category: str = None,
        price_tier: str = None,
    ) -> Optional[CruiseProduct]:
        """
        다중 조건으로 최적 상품 1개 찾기

        우선순위:
        1. 모든 조건 일치
        2. 3개 조건 일치
        3. 2개 조건 일치
        4. 1개 조건 일치
        5. 랜덤

        Args:
            port: 기항지명
            ship: 선박명
            category: 카테고리
            price_tier: 가격대

        Returns:
            최적 상품 또는 None
        """
        if not self.products:
            return None

        # 점수 계산 (조건 일치 개수)
        scored: List[Tuple[int, CruiseProduct]] = []
        for product in self.products:
            score = 0
            if port and port in product.ports:
                score = score + 1
            if ship and (
                ship.lower() in product.ship_name.lower()
                or product.ship_name.lower() in ship.lower()
            ):
                score = score + 1
            if category and (
                category.lower() in product.category.lower()
                or product.category.lower() in category.lower()
            ):
                score = score + 1
            if price_tier and product.price_tier == price_tier:
                score = score + 1

            scored.append((score, product))

        # 점수순 정렬 (점수 높은 순 -> 인기순 -> 추천순 -> 가격 낮은 순)
        scored.sort(
            key=lambda x: (
                -x[0],  # score 내림차순
                not x[1].is_popular,
                not x[1].is_recommended,
                x[1].price if x[1].price > 0 else float('inf')
            )
        )

        if not scored:
            return None

        # 최고 점수 상품들 중 랜덤 선택 (다양성 확보)
        top_score = scored[0][0]
        top_products = [p for s, p in scored if s == top_score]

        return random.choice(top_products) if top_products else None

    # ------------------------------------------------------------------
    # 2-1. 상품-기항지 매칭 (for config_loader cross-check)
    # ------------------------------------------------------------------

    def get_all_ports(self) -> List[str]:
        """전체 상품의 기항지 목록 (중복 제거)"""
        all_ports = set()
        for product in self.products:
            all_ports.update(product.ports)
        return sorted(all_ports)

    def has_port_product(self, port_name: str) -> bool:
        """
        특정 기항지(한글명)를 포함하는 상품이 있는지 확인.
        한글명 -> 영어명 자동 변환 후 products의 ports와 대조.

        Args:
            port_name: 기항지 한글명 (예: "나폴리", "바르셀로나")

        Returns:
            bool: 해당 기항지를 포함하는 상품이 1개 이상 존재
        """
        if not self.products:
            return False

        # 검색할 이름 목록 (한글 + 영어 변환)
        search_names = [port_name.lower()]

        # lower() 변환 후 대조
        port_name_lower = port_name.lower()
        search_names.append(port_name_lower)

        for product in self.products:
            for port in product.ports:
                port_lower = port.lower()
                if port_lower == port_name_lower:
                    return True
                # partial match (한글 기항지명이 포함되는 경우)
                if any(
                    name in port_lower or port_lower in name
                    for name in search_names
                ):
                    return True
        return False

    def filter_existing_ports(self, port_codes: List[str], code_to_name: Dict[str, str]) -> List[str]:
        """
        상품에 존재하는 기항지만 필터링하여 반환.

        Args:
            port_codes: 전체 기항지 코드 목록 (예: "BCN", "NAP")
            code_to_name: 코드->한글명 매핑 (예: "BCN": "바르셀로나")

        Returns:
            상품에 매칭되는 기항지 코드만 필터링된 리스트
        """
        filtered = []
        for code in port_codes:
            name = code_to_name.get(code, "")
            if name and self.has_port_product(name):
                filtered.append(code)
        return filtered

    def get_valid_port_codes(self) -> set:
        """유효한 기항지 코드 목록 반환"""
        codes = set()
        for product in self.products:
            for port in product.ports:
                codes.add(port)
        return codes

    def get_products_for_port(self, port_code: str) -> List[CruiseProduct]:
        """기항지 코드로 상품 조회 (auto_mode.py 호환)"""
        return self.search_by_port(port_code)

    # ------------------------------------------------------------------
    # 컨텍스트 보강
    # ------------------------------------------------------------------

    def enrich_context(
        self,
        context: dict,
        port: str = None,
        ship: str = None,
        category: str = None,
        price_tier: str = None,
    ) -> dict:
        """
        스크립트 생성 컨텍스트에 실제 상품 정보 추가

        Args:
            context: 기존 컨텍스트 dict
            port: 기항지명
            ship: 선박명
            category: 카테고리
            price_tier: 가격대

        Returns:
            상품 정보가 추가된 컨텍스트 dict
        """
        # 최적 상품 찾기
        product = self.find_best_match(
            port,
            ship,
            category,
            price_tier,
        )

        if product is None:
            logger.warning(
                "[ProductLoader] 조건 일치 상품 없음 (port=%s, ship=%s, cat=%s, tier=%s)",
                port, ship, category, price_tier
            )
            # 체험 상품 제외한 전체에서 랜덤
            candidates = [
                p for p in self.products
                if p.price_tier != "체험" and p.price_tier != "일체험"
            ]
            if candidates:
                product = random.choice(candidates)
                logger.info(
                    "[ProductLoader] 대체 상품 선택: %s (%s)",
                    product.product_name,
                    product.category
                )
            else:
                return context

        # 컨텍스트에 상품 정보 주입
        enriched = context.copy()
        enriched.update({
            "product_code": product.product_code,
            "product_name": product.product_name,
            "ship_name": product.ship_name,
            "category": product.category,
            "price": product.price,
            "nights": product.nights,
            "days": product.days,
            "ports_display": product.ports_display(),
            "description": product.description,
            "is_popular": product.is_popular,
            "is_recommended": product.is_recommended,
            "promo_text": product.promo_text,
            "urgency_text": product.urgency_text,
            "departure_date": product.departure_date,
            "monthly_price": product.monthly_price,
            "price_tier": product.price_tier,
            "promo_tag": product.get_promo_tag(),
        })

        logger.info(
            "[ProductLoader] 컨텍스트 보강 완료: %s / %s원 (%s원/월) / %s",
            product.product_name,
            f"{product.price:,}",
            f"{product.monthly_price:,}",
            product.category
        )

        return enriched

    def format_price(self, product: CruiseProduct) -> str:
        """
        가격 표시 텍스트 생성

        Returns:
            "월 XX만원 (N박N+1일 XX만원)" 형태
        """
        if product.price <= 0:
            return "가격 문의"

        monthly_man = product.monthly_price // 10000
        price_man = product.price // 10000

        return f"월 {monthly_man}만원 ({product.nights}박{product.days}일 {price_man}만원)"

    def get_statistics(self) -> dict:
        """상품 통계 정보"""
        total = len(self.products)
        prices = [p.price for p in self.products if p.price > 0]

        tiers: Dict[str, int] = {}
        for product in self.products:
            tier = product.price_tier
            tiers[tier] = tiers.get(tier, 0) + 1

        categories = set(p.category for p in self.products)

        return {
            "total": total,
            "valid": len(prices),
            "avg_price": sum(prices) // len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "popular": sum(1 for p in self.products if p.is_popular),
            "recommended": sum(1 for p in self.products if p.is_recommended),
            "categories": sorted(categories),
            "tiers": dict(sorted(tiers.items())),
            "ports": len(set(port for p in self.products for port in p.ports)),
        }


# ============================================================================
# 3. 편의 함수
# ============================================================================

def create_product_loader(json_path: str = None) -> ProductLoader:
    """
    상품 로더 인스턴스 생성 편의 함수

    Args:
        json_path: JSON 경로

    Returns:
        ProductLoader 인스턴스
    """
    return ProductLoader(json_path)


# ============================================================================
# 4. 테스트 실행
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    # Windows 콘솔 UTF-8 인코딩 설정
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    logging.basicConfig(level=logging.DEBUG)

    loader = ProductLoader()

    print("\n" + "=" * 60)
    print("크루즈 상품 로더 테스트")
    print("=" * 60)

    # 통계
    stats = loader.get_statistics()
    print("\n[통계]")
    print(f"  전체 상품: {stats['total']}개")
    print(f"  유효 상품: {stats['valid']}개")
    print(f"  평균 가격: {stats['avg_price']:,}원")
    print(f"  가격 범위: {stats['min_price']:,}원 ~ {stats['max_price']:,}원")
    print(f"  인기 상품: {stats['popular']}개")
    print(f"  카테고리: {', '.join(stats['categories'])}")

    # 기항지로 조회
    print("\n[기항지 조회: 산토리니]")
    results = loader.search_by_port("산토리니", 3)
    for p in results:
        print(f"  - {p.product_name}")
        print(f"    {p.ports_display()} / {p.price_tier}")

    # 선박으로 조회
    print("\n[선박 조회: 익스플로러]")
    results = loader.search_by_ship("익스플로러", 3)
    for p in results:
        print(f"  - {p.product_name}")
        print(f"    기항지: {p.ports_display()}")

    # 최적 매칭
    print("\n[최적 매칭: 산토리니 + 지중해 + 실속]")
    best = loader.find_best_match(
        port="산토리니",
        category="지중해",
        price_tier="실속"
    )
    if best:
        print(f"  상품코드: {best.product_code}")
        print(f"  상품명: {best.product_name}")
        print(f"  가격: {loader.format_price(best)}")
        print(f"  기항지: {best.ports_display()}")

    # 컨텍스트 보강
    print("\n[컨텍스트 보강]")
    ctx = {
        "topic": "크루즈",
        "port_info": "산토리니 기항지정보"
    }
    enriched = loader.enrich_context(
        ctx,
        port="산토리니",
        category="지중해",
        price_tier="실속"
    )
    print(f"  보강 전: {len(ctx)}개 필드")
    print(f"  보강 후: {len(enriched)}개 필드")
    print(f"  추가된 정보: {', '.join(sorted(set(enriched.keys()) - set(ctx.keys())))}")
