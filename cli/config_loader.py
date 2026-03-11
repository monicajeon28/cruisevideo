"""
cli/config_loader.py - cruise_config.yaml 마스터 설정 로더

YAML 파싱 및 CruiseConfig 데이터클래스 제공.
검증 로직 포함 (weight 합계, 선박 weight, 가격 앵커 연속성).

Usage:
    from cli.config_loader import load_config, CruiseConfig
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import yaml
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 데이터클래스 정의
# ============================================================================


@dataclass
class CategoryConfig:
    """카테고리 설정"""
    code: str
    name: str
    priority: str
    weight: float                # "P0" / "P1" / "P2" / "P3"
    content_types: List[str]
    sub_topics_count: int = 0
    comparison_frame: str = ""
    port_dependent: bool = False
    positioning: str = ""
    notes: str = ""


@dataclass
class ShipConfig:
    """선박 설정"""
    code: str
    name: str
    company: str
    region: str
    capacity: int = 0


@dataclass
class PriceTierConfig:
    """가격 앵커 설정"""
    key: str
    name: str
    range: List[int]
    anchor_text: str
    positioning: str = ""
    description: str = ""
    content_type: str = ""
    rules: List[str] = field(default_factory=list)


@dataclass
class CruiseConfig:
    """크루즈닷 마스터 설정"""
    categories: List[CategoryConfig]
    ships: List[ShipConfig]
    price_tiers: List[PriceTierConfig]
    ports: Dict[str, List]
    generation_strategy: Dict
    content_type_hooks: Dict = field(default_factory=dict)
    cta_templates: Dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # 조회 메서드
    # ------------------------------------------------------------------

    def get_category_by_code(self, code: str) -> Optional[CategoryConfig]:
        """코드로 카테고리 조회"""
        for cat in self.categories:
            if cat.code == code:
                return cat
        return None

    def get_all_port_codes(self) -> List[str]:
        """전체 기항지 코드 목록 (지역 구분 없이 평탄화)"""
        codes = []
        for region, port_list in self.ports.items():
            for port in port_list:
                # dict 형태 {"code": "NAGASAKI", "name": "나가사키"} 또는 단순 문자열 처리
                if isinstance(port, dict):
                    codes.append(port.get("code", str(port)))
                else:
                    codes.append(str(port))
        return codes

    def get_categories_by_priority(self, priority: str) -> List[CategoryConfig]:
        """우선순위로 카테고리 목록 조회"""
        return [cat for cat in self.categories if cat.priority == priority]

    def get_anchor_text(self, tier_key: str) -> Optional[str]:
        """가격 티어로 앵커 텍스트 조회 ('T1_진입가' / 'T2_주력가' / 'T3_프리미엄')"""
        for pt in self.price_tiers:
            if pt.key == tier_key:
                return pt.anchor_text
        return None

    # ------------------------------------------------------------------
    # 검증 메서드
    # ------------------------------------------------------------------

    def validate(self) -> Tuple[bool, List[str]]:
        """
        설정 유효성 검증.

        Returns:
            (유효 여부, 오류 메시지 리스트)
        """
        errors = []

        # 1. 카테고리 weight 합계 검사
        total_weight = sum(cat.weight for cat in self.categories)
        if abs(total_weight - 1.0) > 0.02:
            errors.append(
                f"카테고리 weight 합계 오류: {total_weight:.3f} (기대: 1.0)"
            )

        # 2. 선박 목록 존재 검사
        if len(self.ships) == 0:
            errors.append("선박 목록이 비어 있습니다")

        # 3. 가격 앵커 range 연속성 검사 (T1.max <= T2.min, T2.max <= T3.min)
        tier_keys = ["T1_진입가", "T2_주력가", "T3_프리미엄"]
        for i in range(len(tier_keys) - 1):
            current = None
            next_tier = None
            for pt in self.price_tiers:
                if pt.key == tier_keys[i]:
                    current = pt
                if pt.key == tier_keys[i + 1]:
                    next_tier = pt
            if current and next_tier:
                if current.range[1] > next_tier.range[0]:
                    errors.append(
                        f"가격 앵커 range 불연속: {current.key}({current.range[1]}) "
                        f"> {next_tier.key}({next_tier.range[0]})"
                    )

        # 4. ProductLoader - cruise_config target_ports 교차 검증 (경고만)
        try:
            from cli.product_loader import ProductLoader
            pl = ProductLoader()
            valid_port_codes = pl.get_valid_port_codes()
            config_port_codes = set(self.get_all_port_codes())
            # ProductLoader에서 유효한 port 중 config에 없는 것 찾기
            missing = set()
            for pc in config_port_codes:
                if valid_port_codes and pc not in valid_port_codes:
                    missing.add(pc)
            if missing:
                logger.warning(
                    "ProductLoader 상품 미등록 기항지 %d개: %s",
                    len(missing), ", ".join(missing)
                )
        except Exception as e:
            logger.debug("ProductLoader 교차 검증 스킵: %s", e)

        # 5. content_types 문자열 리스트 검증
        if not isinstance(self.categories, list):
            errors.append("categories는 리스트 형식이어야 합니다")
        else:
            for cat in self.categories:
                if not isinstance(cat.content_types, list):
                    errors.append(
                        f"{cat.code} content_types 항목이 리스트가 아닙니다!"
                    )

        return len(errors) == 0, errors


# ============================================================================
# 2. 설정 로더
# ============================================================================

class CruiseConfigLoader:
    """cruise_config.yaml 로더"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "cruise_config.yaml"
        self.config_path = Path(config_path)

    def load(self) -> CruiseConfig:
        """YAML 파일을 읽어 CruiseConfig 인스턴스 반환"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raise ValueError(
                f"설정 파일이 비어있습니다: {self.config_path}"
            )

        # 카테고리 파싱
        categories = []
        for cat_raw in raw.get("categories", []):
            categories.append(
                CategoryConfig(
                    code=cat_raw.get("code", ""),
                    name=cat_raw.get("name", ""),
                    priority=cat_raw.get("priority", "P3"),
                    weight=cat_raw.get("weight", 0.0),
                    content_types=cat_raw.get("content_types", []),
                    sub_topics_count=cat_raw.get("sub_topics_count", 0),
                    comparison_frame=cat_raw.get("comparison_frame", ""),
                    port_dependent=cat_raw.get("port_dependent", False),
                    positioning=cat_raw.get("positioning", ""),
                    notes=cat_raw.get("notes", ""),
                )
            )

        # 선박 파싱
        ships = []
        for ship_raw in raw.get("ships", []):
            ships.append(
                ShipConfig(
                    code=ship_raw.get("code", ""),
                    name=ship_raw.get("name", ""),
                    company=ship_raw.get("company", ""),
                    region=ship_raw.get("region", ""),
                    capacity=ship_raw.get("capacity", 0),
                )
            )

        # 가격 티어 파싱
        price_tiers = []
        for tier_key, tier_raw in raw.get("price_tiers", {}).items():
            price_tiers.append(
                PriceTierConfig(
                    key=tier_key,
                    name=tier_raw.get("name", ""),
                    range=tier_raw.get("range", [0, 0]),
                    anchor_text=tier_raw.get("anchor_text", ""),
                    positioning=tier_raw.get("positioning", ""),
                    description=tier_raw.get("description", ""),
                    content_type=tier_raw.get("content_type", ""),
                    rules=tier_raw.get("rules", []),
                )
            )

        # ports 값을 문자열 리스트로 정규화
        ports = {}
        for region, port_list in raw.get("ports", {}).items():
            normalized = []
            for port in port_list:
                if isinstance(port, dict):
                    normalized.append(port)
                else:
                    normalized.append({"code": str(port), "name": str(port)})
            ports[region] = normalized

        config = CruiseConfig(
            categories=categories,
            ships=ships,
            price_tiers=price_tiers,
            ports=ports,
            generation_strategy=raw.get("generation_strategy", {}),
            content_type_hooks=raw.get("content_type_hooks", {}),
            cta_templates=raw.get("cta_templates", {}),
        )

        valid, errors = config.validate()
        if not valid:
            for err in errors:
                logger.warning("[CruiseConfig] 검증 오류: %s", err)
        else:
            logger.info(
                "[CruiseConfig] 설정 로드 완료 - 카테고리 %d개, 선박 %d개",
                len(categories),
                len(ships),
            )

        return config


# ============================================================================
# 3. 편의 함수
# ============================================================================

def load_config(config_path: str = None) -> CruiseConfig:
    """
    cruise_config.yaml 로드 편의 함수.

    Args:
        config_path: YAML 파일 경로 (None 이면 기본 경로 사용)

    Returns:
        CruiseConfig 인스턴스
    """
    return CruiseConfigLoader(config_path).load()
