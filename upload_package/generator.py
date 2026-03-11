#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_package/generator.py — YouTube 업로드 준비 패키지 생성

생성 파일 종류:
    title.txt           최적화 제목 (100자 이내)
    description.txt     3문단 설명 + 해시태그 (5000개 이내)
    tags.txt            쉼표 구분 태그 (500자 이내)
    thumbnail.png       썸네일 (1280x720)

고가 세일즈 포지셔닝 규칙:
    - 가격 덤핑 금지어 필터 필수
    - 가격대(price_tier)에 따라 제목/설명 톤 차별화
    - premium 가격 숫자 제목 노출 금지, 경험 가치 중심
"""

import logging
import re
import random
from pathlib import Path
from typing import Optional, List, Dict

try:
    from path_resolver import get_paths
except ImportError:
    get_paths = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

logger = logging.getLogger(__name__)

# --- 가격 덤핑 금지어 (브랜드 이미지 보호) ---
PRICE_DUMP_WORDS = ["저렴", "싸다", "싸게", "할인", "특가", "최저가", "파격", "세일", "초특가"]

# --- 크루즈 고정 해시태그 (항상 포함) ---
FIXED_HASHTAGS = [
    "#크루즈여행", "#크루즈닷", "#크루즈추천",
    "#여행", "#시니어여행", "#크루즈패키지",
    "#유람선여행", "#해외여행",
]

# --- 카테고리별 추가 해시태그 ---
CATEGORY_HASHTAGS: Dict[str, List[str]] = {
    "기항지정보":     ["#기항지", "#해외여행지", "#도시여행"],
    "불안해소":       ["#안심크루즈", "#크루즈초보", "#크루즈팁"],
    "선내시설":       ["#크루즈시설", "#선내생활", "#크루즈다이닝"],
    "여행기준교육":   ["#크루즈선택법", "#여행전문가", "#크루즈기준"],
    "프리미엄경험":   ["#럭셔리크루즈", "#프리미엄여행", "#크루즈스위트"],
    "음식":           ["#크루즈맛집", "#크루즈뷔페", "#크루즈다이닝"],
    "가격가성비":     ["#크루즈가격", "#가성비여행", "#크루즈할인"],
    "꿀팁":           ["#크루즈꿀팁", "#여행준비", "#크루즈초보"],
    "비교":           ["#크루즈여행", "#크루즈선택", "#여행비교"],
    "럭셔리":         ["#럭셔리크루즈", "#프리미엄크루즈", "#크루즈스위트"],
    "버킷리스트":     ["#버킷리스트", "#인생여행", "#크루즈버킷"],
    "시니어":         ["#시니어크루즈", "#어른여행", "#크루즈"],
    "안전정보":       ["#크루즈안전", "#안심여행", "#크루즈보험"],
    "후기":           ["#크루즈후기", "#여행후기", "#크루즈실후기"],
}

# --- 가격대별 제목 톤 ---
PRICE_TIER_TONE: Dict[str, Dict] = {
    "budget": {
        "tone": "가성비강조",
        "suffix": " | 크루즈닷",
    },
    "standard": {
        "tone": "가치설득",
        "suffix": " | 크루즈닷 전문가 추천",
    },
    "premium": {
        "tone": "경험서사",
        "suffix": " | 크루즈닷 프리미엄",
        "no_price": True,  # 제목에 가격 숫자 금지
    },
}

# --- 카테고리별 제목 템플릿 ---
CATEGORY_TITLE_TEMPLATES: Dict[str, Dict] = {
    "기항지정보": {
        "budget":    "{ship} 크루즈로 떠나는 {port} 여행 완벽 가이드",
        "standard":  "{port}, 배에서 눈 뜨면 보이는 풍경 | 크루즈닷",
        "premium": "{port}의 아침을 갑판에서 맞이하는 법",
    },
    "불안해소": {
        "budget":    "크루즈 처음이세요? 걱정 없이 즐기는 법",
        "standard":  "{ship} 크루즈, 이것만 알면 걱정 없어요",
        "premium": "11년 경력이 당신의 {port} 여행을 책임집니다",
    },
    "선내시설": {
        "budget":    "{ship} 크루즈 선내 시설 총정리",
        "standard":  "바다 위 5성급 리조트, {ship} 크루즈",
        "premium": "17만 톤 위에서의 하루 — {ship} 크루즈닷 프리미엄",
    },
    "여행기준교육": {
        "budget":    "크루즈 vs 육지 여행, 어떤 게 더 좋을까?",
        "standard":  "고급 여행 고를 때 이것만 따지세요 | 크루즈닷",
        "premium": "평생 한 번의 여행, 기준이 달라야 합니다",
    },
    "프리미엄경험": {
        "budget":    "{ship} 크루즈 특별한 경험",
        "standard":  "{port}에서의 프리미엄 크루즈 경험",
        "premium": "{port}, 말이 필요 없는 그 여행 | 크루즈닷",
    },
    "음식": {
        "budget":    "{ship} 크루즈 음식 솔직 후기",
        "standard":  "하루 세 끼, 전부 공짜 — {ship} 크루즈 다이닝",
        "premium": "{ship} 크루즈 레스토랑 10개, 전부 포함입니다",
    },
    "가격가성비": {
        "budget":    "{ship} 크루즈, 얼마면 될까?",
        "standard":  "{ship} 크루즈 가격, 제대로 따져봤습니다",
        "premium": None,  # premium 에서 사용 금지
    },
    "꿀팁": {
        "budget":    "{ship} 크루즈 꿀팁 5선",
        "standard":  "크루즈 전문가가 알려주는 {port} 꿀팁",
        "premium": "11년 경력이 전하는 크루즈 비밀 | 크루즈닷",
    },
    "비교": {
        "budget":    "유럽 혼자 가기 vs 크루즈, 뭐가 더 좋을까?",
        "standard":  "육지 여행 vs 크루즈, 5가지 기준으로 비교했습니다",
        "premium": "제대로 된 여행의 기준은 따로 있습니다 | 크루즈닷",
    },
}


class UploadPackageGenerator:
    """
    YouTube 업로드 준비 패키지 생성기

    고가 세일즈 포지셔닝 원칙:
    1. 가격 덤핑 금지어 자동 필터
    2. price_tier에 따른 톤 차별화
    3. premium 가격 숫자 제목 금지, 경험 가치 중심
    4. 비교 프레임: 여행사 패키지 < 육지 개별 여행 < 크루즈
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/upload_packages")
        self._product_loader = None

    def _get_product_loader(self):
        """ProductLoader 싱글톤 반환 (최초 호출 시 초기화)"""
        if self._product_loader is None:
            try:
                from cli.product_loader import ProductLoader
                self._product_loader = ProductLoader()
                self._product_loader.load()
                logger.info("ProductLoader 로드 성공")
            except ImportError:
                logger.info("ProductLoader 없음 — 폴백 모드")
                self._product_loader = None
            except Exception as e:
                logger.warning("ProductLoader 초기화 실패: %s", e)
                self._product_loader = None
        return self._product_loader

    def generate(
        self,
        script_dict: dict,
        video_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Dict:
        """
        업로드 패키지 전체 생성

        Args:
            script_dict:     스크립트 딕셔너리 (segments, metadata, hook 포함)
            video_path:      생성된 mp4 경로
            output_dir:      패키지 저장 디렉토리
            metadata:        {
                "port_name": "나가사키",
                "category_name": "기항지정보",
                "price_tier": "",
                "ship_name": "MSC 벨리시마",
                "port_code": "",
                "category_code": "",
            }

        Returns:
            Dict
        """
        output_dir = Path(output_dir) if output_dir else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        price_tier = metadata.get("price_tier", "standard") if metadata else "standard"

        title = self._generate_title(script_dict, metadata, price_tier)
        description = self._generate_description(script_dict, title, metadata, price_tier)
        tags = self._generate_tags(script_dict, title, metadata)

        (output_dir / "title.txt").write_text(title, encoding="utf-8")
        (output_dir / "description.txt").write_text(description, encoding="utf-8")
        (output_dir / "tags.txt").write_text(tags, encoding="utf-8")

        # 썸네일 생성 비활성화 (2026-03-11)
        # self._generate_thumbnail(script_dict, title, output_dir, metadata)

        logger.info("업로드 패키지 생성 완료: %s", output_dir)
        logger.info("  제목: %s", title)
        return {
            "title": title,
            "description": description,
            "tags": tags,
            "output_dir": str(output_dir),
        }

    def _filter_price_dump(self, text: str, price_tier: str = "") -> str:
        """
        가격 덤핑 금지어 필터

        - 모든 PRICE_DUMP_WORDS 제거/대체
        - premium 가격 숫자 패턴도 제거 (예: "59만원", "100만원")
        """
        for word in PRICE_DUMP_WORDS:
            text = text.replace(word, "")

        if price_tier == "premium":
            # 가격 숫자 패턴 제거: 만원, 만원, ,원 등
            text = re.sub(r"\d+만원", "", text)
            text = re.sub(r"[\d,]*원", "", text)

        # 이중 공백 정리
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _generate_title(self, script_dict: dict, metadata: Optional[dict], price_tier: str) -> str:
        """
        YouTube 최적화 제목 생성 (100자 이내)

        우선순위:
            1. "title" 존재 시 (price_dump 필터 적용 후 사용)
            2. 카테고리별 템플릿 사용
            3. 범용 템플릿 폴백
        """
        ship_name = metadata.get("ship_name", "크루즈") if metadata else "크루즈"
        port_name = metadata.get("port_name", "") if metadata else ""

        # 스크립트 제목 활용
        if script_dict.get("title"):
            title = str(script_dict["title"]).strip()
            title = self._filter_price_dump(title, price_tier)
            return title[:100]

        # 카테고리별 템플릿
        category = metadata.get("category_name", "") if metadata else ""
        if category in CATEGORY_TITLE_TEMPLATES:
            templates = CATEGORY_TITLE_TEMPLATES[category]
            template = templates.get(price_tier)

            # premium 사용 금지 카테고리 (가격가성비) → standard 폴백
            if template is None:
                template = templates.get("standard", "{ship} 크루즈 | 크루즈닷")

            title = template.format(ship=ship_name, port=port_name)
        else:
            # 범용 폴백
            fallback_templates = {
                "budget":    "{ship} 크루즈 | 크루즈닷",
                "standard":  "{port} {ship} 크루즈닷 전문가 추천",
                "premium": "{port} 크루즈닷 프리미엄",
            }
            template = fallback_templates.get(price_tier, "{ship} 크루즈 | 크루즈닷")
            title = template.format(ship=ship_name, port=port_name)

        title = self._filter_price_dump(title, price_tier)
        return title[:100]

    def _generate_description(
        self,
        script_dict: dict,
        title: str,
        metadata: Optional[dict],
        price_tier: str,
    ) -> str:
        """
        YouTube 설명 생성 (5000자 이내)

        구조:
            1문단: CTA 링크 (카카오톡 클릭 - 1줄 CTA.)
            공백
            2문단: Hook 텍스트
            공백
            3문단: 상세 내용 (가격대별 톤 차별화)
            공백
            해시태그
        """
        ship_name = metadata.get("ship_name", "크루즈") if metadata else "크루즈"
        port_name = metadata.get("port_name", "크루즈선") if metadata else "크루즈선"
        category = metadata.get("category_name", "") if metadata else ""

        # 1문단 CTA. 단순화 + 무료 일정표 통합 (2026-03 사용자 피드백)
        cta_line1 = "✅ 크루즈 상담 신청 → 유튜브 프로필 링크 클릭"
        cta_line2 = "🎁 특별 지원 10만원 + 무료 일정표 받기"
        cta_line3 = "👆 프로필 링크에서 원클릭 상담 신청"

        # Hook 텍스트 추출 (스크립트 첫 번째 hook 섹션)
        hook_text = self._extract_hook_text(script_dict)

        # 가격대별 본문 톤
        body_text = self._generate_body_text(metadata, ship_name, price_tier)

        # 해시태그 조합
        cat_tags = CATEGORY_HASHTAGS.get(category, [])
        port_tag = self._port_to_hashtag(port_name)
        all_tags = FIXED_HASHTAGS + cat_tags + [port_tag]

        # premium 가격/할인 관련 해시태그 제거
        if price_tier == "premium":
            filtered_tags = []
            for tag in all_tags:
                if "가격" not in tag and "할인" not in tag:
                    filtered_tags.append(tag)
            all_tags = filtered_tags

        hashtag_line = " ".join(all_tags)

        # CTA를 최상단 배치 (전환율 +12% 목표)
        parts = [cta_line1, cta_line2, cta_line3, "", hook_text, "", body_text, "", hashtag_line]
        description = "\n".join(parts)
        return description[:5000]

    def _extract_hook_text(self, script_dict: dict) -> str:
        """스크립트 dict에서 hook 섹션 텍스트 추출"""
        segments = script_dict.get("segments", [])
        for segment in segments:
            if segment.get("type") == "hook":
                return segment.get("text", "")
        return ""

    def _generate_body_text(self, metadata: Optional[dict], ship_name: str, price_tier: str) -> str:
        """가격대별 본문 문단 생성"""
        port_name = metadata.get("port_name", "") if metadata else ""
        if price_tier == "premium":
            return (
                f"{port_name}에서의 크루즈 여행은 단순한 여행이 아닙니다.\n"
                f"11년 경력의 크루즈닷이 선별한 프리미엄 {ship_name} 여정,\n"
                f"한국어 24시간 케어와 1억 여행보험으로 완벽하게 준비해드립니다."
            )
        elif price_tier == "standard":
            return (
                f"{port_name} 크루즈 여행을 계획 중이신가요?\n"
                f"크루즈닷은 11년 경력의 크루즈 전문 여행사입니다.\n"
                f"{ship_name}을 타고 떠나는 {port_name} 크루즈, 한국어 24시간 케어로 안심하세요."
            )
        else:  # budget
            return (
                f"{port_name} 크루즈 여행, 어렵지 않습니다.\n"
                f"크루즈닷이 처음부터 끝까지 도와드립니다.\n"
                f"한국어 24시간 케어 + 1억 여행보험 기본 포함."
            )

    def _port_to_hashtag(self, port_name: str) -> str:
        """항구명에서 해시태그 생성 (공백/괄호 제거)"""
        cleaned = re.sub(r"[()（）\s]", "", port_name)
        return "#" + cleaned

    def _generate_tags(self, script_dict: dict, title: str, metadata: Optional[dict]) -> str:
        """YouTube 태그 생성 (쉼표 구분, 500자 이내)"""
        ship_name = metadata.get("ship_name", "") if metadata else ""
        port_name = metadata.get("port_name", "") if metadata else ""
        category = metadata.get("category_name", "") if metadata else ""
        price_tier = metadata.get("price_tier", "") if metadata else ""

        base_tags = [
            "크루즈여행", "크루즈닷", "크루즈추천", "크루즈패키지",
            "여행", "시니어여행", "해외여행", "유람선여행",
        ]

        if ship_name:
            base_tags.append(ship_name.replace(" ", ""))
        if port_name:
            base_tags.append(port_name.replace(" ", ""))
        if category:
            base_tags.append(category)

        # 스크립트 키워드
        segments = script_dict.get("segments", [])
        for segment in segments:
            text = segment.get("text", "")
            if text:
                words = re.findall(r"[가-힣]{2,6}", text)
                for word in words:
                    if word not in base_tags and not any(w in word for w in PRICE_DUMP_WORDS):
                        if len(word) >= 2:
                            base_tags.append(word)

        tags = list(dict.fromkeys(base_tags))

        # 가격 덤핑 금지어 필터
        filtered_tags = []
        for tag in tags:
            cleaned = self._filter_price_dump(tag, price_tier)
            if cleaned:
                filtered_tags.append(cleaned)

        result = ", ".join(filtered_tags)
        return result[:500]

    def _generate_thumbnail(
        self,
        script_dict: dict,
        title: str,
        output_dir: Path,
        metadata: Optional[dict],
    ):
        """
        썸네일 생성 (2단계 폴백 체인)

        1순위: path_resolver로 에셋 기반 썸네일
        2순위: PIL 기반 Pillow 썸네일
        3순위: 오류 로그만 기록 (파일 없어도 패키지 생성 계속)
        """
        output_path = output_dir / "thumbnail.png"

        # 1순위: path_resolver 에셋
        if get_paths is not None:
            try:
                paths = get_paths()
                port_name = (
                    metadata.get("port_name", "") if metadata else ""
                )
                font_title, font_sub = self._load_fonts()
                self._generate_pillow_thumbnail(
                    output_path,
                    title,
                    port_name,
                    font_title,
                    font_sub,
                )
                logger.info("썸네일 생성 완료: %s", output_path)
                return
            except Exception as e:
                logger.warning("썸네일 생성 실패: %s — Pillow 폴백 시도", e)

        # 2순위: Pillow 폴백
        try:
            font_title, font_sub = self._load_fonts()
            port_name = metadata.get("port_name", "") if metadata else ""
            self._generate_pillow_thumbnail(output_path, title, port_name, font_title, font_sub)
            logger.info("Pillow 폴백 생성 완료: %s", output_path)
        except Exception as e:
            logger.warning("Pillow 폴백도 실패: %s — 썸네일 없이 계속", e)

    def _generate_pillow_thumbnail(
        self, output_path: Path, title: str, port_name: str = "",
        font_title=None, font_sub=None,
    ):
        """PIL 기반 Pillow 썸네일 생성 (1280x720, 네이비)"""
        if Image is None:
            logger.warning("PIL 미설치 — 썸네일 생성 스킵")
            return

        # 크루즈닷 브랜드 컬러: 네이비 배경
        img = Image.new("RGB", (1280, 720), (20, 40, 80))
        draw = ImageDraw.Draw(img)

        display_title = (title[:30] + "...") if len(title) > 30 else title
        display_sub = port_name if port_name else "크루즈닷"

        # 폰트 로드 (자산 폴더 → 시스템 폴백 → 기본 폰트)
        if font_title is None or font_sub is None:
            font_title, font_sub = self._load_fonts()

        # 텍스트 중앙 배치
        draw.text((640, 300), display_title, fill="white", font=font_title, anchor="mm")
        if port_name:
            draw.text((640, 420), display_sub, fill=(200, 220, 255), font=font_sub, anchor="mm")
        draw.text((640, 600), "크루즈닷", fill=(200, 220, 255), font=font_sub, anchor="mm")

        img.save(str(output_path), "PNG", quality=95)

    @staticmethod
    def _load_fonts():
        """용도별 폰트 로드 (3단계 폴백)"""
        if ImageFont is None:
            return None, None

        # 1순위: 자산 폴더 폰트
        try:
            if get_paths is not None:
                fonts_dir = get_paths().fonts_dir
                font_files = list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf"))
                if font_files:
                    font_title = ImageFont.truetype(str(font_files[0]), 60)
                    font_sub = ImageFont.truetype(str(font_files[0]), 36)
                    return font_title, font_sub
        except Exception:
            pass

        # 2순위: Windows 시스템 폰트
        try:
            sys_font = Path("C:/Windows/Fonts/malgunbd.ttf")
            if sys_font.exists():
                font_title = ImageFont.truetype(str(sys_font), 60)
                font_sub = ImageFont.truetype(str(sys_font), 36)
                return font_title, font_sub
        except Exception:
            pass

        # 3순위: PIL 기본 폰트
        font_default = ImageFont.load_default()
        return font_default, font_default
