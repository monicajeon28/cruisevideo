"""
CardRenderer - 정보 카드 시각화 모듈 (WO v12.0 Phase 5)

PIL 기반 정보 카드를 1080x1920 RGBA numpy 배열로 렌더링.
MoviePy ImageClip(array)으로 오버레이 가능.

Usage:
    from pipeline_render.card_renderer import CardRenderer

    renderer = CardRenderer()
    arr = renderer.render_number_highlight("1인 가격", "89만원")
    clip = ImageClip(arr, is_mask=False, transparent=True)

카드 5종: NumberHighlight, Comparison, ProsCons, Itinerary, PriceBreakdown
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# 디자인 상수
CARD_WIDTH = 960       # 카드 최대 너비 (좌우 60px 여백)
CANVAS_W, CANVAS_H = 1080, 1920
MARGIN_X = (CANVAS_W - CARD_WIDTH) // 2
CARD_BG_ALPHA = 170    # 카드 배경 투명도
CARD_RADIUS = 24       # 카드 모서리 반경
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
GREEN = (80, 200, 80)
RED = (220, 80, 80)
DARK_BG = (20, 20, 20)


class CardRenderer:
    """정보 카드 PIL 렌더러 (WO v12.0 Phase 5)"""

    def __init__(self, config=None):
        self.config = config
        # 폰트 로드 (subtitle_image_renderer와 동일 우선순위)
        self.font_path = None
        for fp in [
            Path("D:/AntiGravity/Assets/fonts/BMDOHYEON_ttf.ttf"),
            Path("D:/AntiGravity/Assets/fonts/JalnanGothicTTF.ttf"),
            Path("D:/AntiGravity/Assets/fonts/GmarketSansTTFBold.ttf"),
            Path("C:/Windows/Fonts/malgunbd.ttf"),
        ]:
            if fp.exists():
                self.font_path = str(fp)
                break

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """폰트 로드 (graceful fallback)"""
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except (OSError, ValueError):
                pass
        return ImageFont.load_default()

    def _new_canvas(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        """투명 1080x1920 캔버스 생성"""
        img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        return img, ImageDraw.Draw(img)

    def _draw_card_bg(self, draw: ImageDraw.Draw, rect: list, alpha: int = CARD_BG_ALPHA):
        """반투명 카드 배경 그리기"""
        draw.rounded_rectangle(rect, radius=CARD_RADIUS, fill=(*DARK_BG, alpha))

    def render_number_highlight(self, label: str, value: str,
                                 accent_color: tuple = None) -> np.ndarray:
        """숫자 강조 카드 — 큰 골드 숫자 + 작은 흰색 라벨"""
        img, draw = self._new_canvas()
        color = accent_color or GOLD
        font_label = self._get_font(36)
        font_value = self._get_font(72)

        # 텍스트 크기 측정
        lbbox = draw.textbbox((0, 0), label, font=font_label)
        vbbox = draw.textbbox((0, 0), value, font=font_value)
        lh = lbbox[3] - lbbox[1]
        vh = vbbox[3] - vbbox[1]
        total_h = lh + vh + 20  # 20px 간격

        # 카드 중앙 배치
        cy = CANVAS_H // 2
        card_top = cy - total_h // 2 - 40
        card_bottom = cy + total_h // 2 + 40
        self._draw_card_bg(draw, [MARGIN_X, card_top, CANVAS_W - MARGIN_X, card_bottom])

        # 라벨 (흰색)
        label_y = cy - total_h // 2
        draw.text((CANVAS_W // 2, label_y), label, font=font_label,
                  fill=(*WHITE, 255), anchor="mt")
        # 값 (골드)
        value_y = label_y + lh + 20
        draw.text((CANVAS_W // 2, value_y), value, font=font_value,
                  fill=(*color, 255), anchor="mt")

        return np.array(img)

    def render_comparison(self, left: dict, right: dict) -> np.ndarray:
        """좌우 비교 카드 — left/right에 name, price 키"""
        img, draw = self._new_canvas()
        font_title = self._get_font(40)
        font_price = self._get_font(56)
        font_vs = self._get_font(32)

        cy = CANVAS_H // 2
        card_h = 220
        self._draw_card_bg(draw, [MARGIN_X, cy - card_h // 2, CANVAS_W - MARGIN_X, cy + card_h // 2])

        # 좌측
        left_x = MARGIN_X + CARD_WIDTH // 4
        draw.text((left_x, cy - 40), left.get('name', ''), font=font_title,
                  fill=(*WHITE, 255), anchor="mm")
        draw.text((left_x, cy + 30), left.get('price', ''), font=font_price,
                  fill=(*GOLD, 255), anchor="mm")

        # VS
        draw.text((CANVAS_W // 2, cy), "VS", font=font_vs,
                  fill=(*GRAY, 255), anchor="mm")

        # 우측
        right_x = CANVAS_W - MARGIN_X - CARD_WIDTH // 4
        draw.text((right_x, cy - 40), right.get('name', ''), font=font_title,
                  fill=(*WHITE, 255), anchor="mm")
        draw.text((right_x, cy + 30), right.get('price', ''), font=font_price,
                  fill=(*WHITE, 255), anchor="mm")

        return np.array(img)

    def render_pros_cons(self, pros: list, cons: list) -> np.ndarray:
        """장단점 카드 — 녹색 체크 / 빨간 X"""
        img, draw = self._new_canvas()
        font = self._get_font(36)
        line_h = 50

        items = [(p, True) for p in pros] + [(c, False) for c in cons]
        total_h = len(items) * line_h + 40
        cy = CANVAS_H // 2
        card_top = cy - total_h // 2
        card_bottom = cy + total_h // 2
        self._draw_card_bg(draw, [MARGIN_X, card_top - 20, CANVAS_W - MARGIN_X, card_bottom + 20])

        for i, (text, is_pro) in enumerate(items):
            y = card_top + i * line_h + 20
            icon = "✓" if is_pro else "✗"
            icon_color = GREEN if is_pro else RED
            draw.text((MARGIN_X + 40, y), icon, font=font, fill=(*icon_color, 255))
            draw.text((MARGIN_X + 80, y), text, font=font, fill=(*WHITE, 255))

        return np.array(img)

    def render_itinerary(self, stops: list) -> np.ndarray:
        """타임라인 카드 — 세로 점선 + 기항지"""
        img, draw = self._new_canvas()
        font_day = self._get_font(28)
        font_port = self._get_font(40)
        font_desc = self._get_font(24)
        step_h = 100

        total_h = len(stops) * step_h + 40
        cy = CANVAS_H // 2
        start_y = cy - total_h // 2
        self._draw_card_bg(draw, [MARGIN_X, start_y - 20, CANVAS_W - MARGIN_X, start_y + total_h + 20])

        dot_x = MARGIN_X + 60
        text_x = MARGIN_X + 100

        for i, stop in enumerate(stops):
            y = start_y + i * step_h + 20
            # 연결선
            if i < len(stops) - 1:
                draw.line([(dot_x, y + 12), (dot_x, y + step_h)], fill=(*GRAY, 180), width=2)
            # 골드 점
            draw.ellipse([dot_x - 8, y - 8 + 12, dot_x + 8, y + 8 + 12], fill=(*GOLD, 255))
            # Day + Port
            draw.text((text_x, y), stop.get('day', ''), font=font_day, fill=(*GRAY, 255))
            draw.text((text_x, y + 28), stop.get('port', ''), font=font_port, fill=(*WHITE, 255))
            hl = stop.get('highlight', '')
            if hl:
                draw.text((text_x, y + 68), hl, font=font_desc, fill=(*GOLD, 200))

        return np.array(img)

    def render_price_breakdown(self, items: list) -> np.ndarray:
        """가격 비교표 — 크루즈 vs 호텔+항공"""
        img, draw = self._new_canvas()
        font_label = self._get_font(32)
        font_value = self._get_font(36)
        row_h = 60

        total_h = (len(items) + 1) * row_h + 40  # +1 for header
        cy = CANVAS_H // 2
        start_y = cy - total_h // 2
        self._draw_card_bg(draw, [MARGIN_X, start_y - 10, CANVAS_W - MARGIN_X, start_y + total_h + 10])

        # 헤더
        col1 = MARGIN_X + 40
        col2 = MARGIN_X + CARD_WIDTH // 2
        col3 = MARGIN_X + CARD_WIDTH * 3 // 4
        y = start_y + 20
        draw.text((col1, y), "항목", font=font_label, fill=(*GRAY, 255))
        draw.text((col2, y), "크루즈", font=font_label, fill=(*GOLD, 255))
        draw.text((col3, y), "호텔+항공", font=font_label, fill=(*GRAY, 255))

        # 행
        for i, item in enumerate(items):
            y = start_y + (i + 1) * row_h + 20
            draw.text((col1, y), item.get('label', ''), font=font_label, fill=(*WHITE, 255))
            draw.text((col2, y), item.get('cruise', ''), font=font_value, fill=(*GOLD, 255))
            draw.text((col3, y), item.get('hotel', ''), font=font_value, fill=(*WHITE, 255))

        return np.array(img)


__all__ = ["CardRenderer"]
