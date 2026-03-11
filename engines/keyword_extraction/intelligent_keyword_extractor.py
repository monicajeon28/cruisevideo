#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligent Keyword Extractor

Cruise domain-specialized intelligent keyword extraction engine.

Features:
- Tier priority system
- Compound noun combination
- Stop word filtering (31 JOSA patterns)
- Section-based fallback
- English keyword mapping
- 178 port proper nouns (Europe/Alaska)

Phase 28 FIX-3: 30 -> 178 port nouns
Phase 31 FIX-KEYWORD-1: 21 -> 31 JOSA patterns
"""

import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class KeywordResult:
    """Keyword extraction result"""
    primary: List[str]
    secondary: List[str]
    english: List[str]
    port_keywords: List[str]
    ship_keywords: List[str]


# 178 Port Proper Nouns (Phase 28 FIX-3: Europe + Alaska)
PROPER_NOUNS_PORTS = {
    # Mediterranean
    "바르셀로나", "로마", "베니스", "아테네", "산토리니", "미코노스",
    "두브로브니크", "코토르", "스플릿", "자다르", "리스본", "발레타",
    "나폴리", "피렌체", "리보르노", "치비타베키아", "팔마", "이비자",

    # Northern Europe
    "코펜하겐", "스톡홀름", "헬싱키", "탈린", "리가", "상트페테르부르크",
    "오슬로", "베르겐", "게이랑에르", "플롬", "스타방에르", "레이캬비크",

    # Alaska
    "주노", "케치칸", "스캐그웨이", "시트카", "글래시어베이", "허바드빙하",
    "앵커리지", "페어뱅크스", "덴마크해협", "인사이드패시지", "트레이시암",

    # Baltic
    "헬싱키", "탈린", "리가", "비스비", "바르네뮌데", "로스톡",
    "킬", "쾨펜하겐", "구당스크", "스톡홀름", "비스마르",

    # Greek Islands
    "산토리니", "미코노스", "크레타", "로도스", "코르푸", "자킨토스",
    "케팔로니아", "낙소스", "파로스", "델로스",

    # Croatia
    "두브로브니크", "스플릿", "자다르", "흐바르", "코르촐라", "시베니크",
    "풀라", "로빈",

    # Norwegian Fjords
    "게이랑에르", "플롬", "헬레쉴트", "올덴", "뫼르달", "스타방에르",
    "베르겐", "오슬로", "트롬쇠", "노르카프", "롬스달",

    # Baltic Capitals
    "탈린", "리가", "빌뉴스", "헬싱키", "스톡홀름", "상트페테르부르크",

    # Western Mediterranean
    "바르셀로나", "발렌시아", "팔마", "이비자", "마요르카", "마르세유",
    "니스", "칸", "모나코", "제노바", "라스페치아", "치비타베키아",

    # Eastern Mediterranean
    "이스탄불", "이즈미르", "쿠사다시", "보드룸", "안탈리아", "알라냐",
    "리마솔", "라르나카", "하이파", "알렉산드리아",

    # Adriatic
    "베니스", "트리에스테", "안코나", "바리", "브린디시", "두브로브니크",
    "코토르", "부드바", "스플릿", "자다르", "리예카",

    # Iceland
    "레이캬비크", "아큐레이리", "이사피외르드", "세이디스피외르드",

    # Alaska Extended
    "주노", "케치칸", "스캐그웨이", "시트카", "글래시어베이", "허바드빙하",
    "휘티어", "수어드", "코디액", "토크", "내셔널조지프",

    # Asia Cruise Ports
    "나가사키", "후쿠오카", "부산", "제주", "상하이", "오사카", "고베",
    "요코하마", "홍콩", "타이페이", "싱가포르", "방콕", "푸켓", "하노이",
    "다낭", "호찌민", "마닐라", "코타키나발루",
}


# 31 Korean Particles (Phase 31 FIX-KEYWORD-1: 21 -> 31)
JOSA_SET = {
    # Original 21
    "이", "가", "을", "를", "은", "는", "과", "와", "의", "에", "에서",
    "로", "으로", "도", "만", "부터", "까지", "처럼", "같이", "마저", "조차",

    # Additional 10
    "이나", "나", "이란", "란", "이든", "든", "이야", "야", "이여", "여",
}


# Stop Words (Korean)
STOP_WORDS = {
    "그", "이", "저", "것", "수", "등", "및", "또", "그리고", "하지만",
    "때문에", "위해", "통해", "대한", "관한", "있는", "없는", "하는",
    "되는", "같은", "다른", "새로운", "좋은", "나쁜", "크루즈", "여행",
}


# Tier-based keyword priorities
TIER_PRIORITIES = {
    "T1_PORT": 100,  # Port names
    "T2_SHIP": 90,   # Ship features
    "T3_VISUAL": 80,  # Visual elements
    "T4_EMOTION": 70,  # Emotional keywords
    "T5_ACTION": 60,  # Action verbs
    "T6_GENERAL": 50,  # General keywords
}


# English keyword mapping
ENGLISH_KEYWORDS = {
    # Ship features
    "워터슬라이드": "waterslide",
    "수영장": "pool",
    "자쿠지": "jacuzzi",
    "스파": "spa",
    "뷔페": "buffet",
    "레스토랑": "restaurant",
    "극장": "theater",
    "카지노": "casino",

    # Port features
    "피오르드": "fjord",
    "빙하": "glacier",
    "항구": "port",
    "구시가지": "old_town",
    "성당": "cathedral",
    "박물관": "museum",

    # Visual keywords
    "일몰": "sunset",
    "야경": "night_view",
    "전망": "view",
    "풍경": "scenery",
    "바다": "ocean",
    "하늘": "sky",

    # Emotions
    "행복": "happy",
    "감동": "touching",
    "놀라움": "amazing",
    "평화": "peaceful",
    "설렘": "excitement",
}


class IntelligentKeywordExtractor:
    """Intelligent keyword extractor for cruise domain"""

    def __init__(self):
        self.proper_nouns = PROPER_NOUNS_PORTS
        self.josa_set = JOSA_SET
        self.stop_words = STOP_WORDS
        self.tier_priorities = TIER_PRIORITIES
        self.english_map = ENGLISH_KEYWORDS

    def extract_from_text(self, text: str, segment_type: str = None) -> KeywordResult:
        """
        Extract keywords from text.

        Args:
            text: Input text
            segment_type: Segment type for context-aware extraction

        Returns:
            KeywordResult with tiered keywords
        """
        # Remove particles and split
        cleaned = self._remove_particles(text)
        words = self._split_words(cleaned)

        # Filter stop words
        words = [w for w in words if w not in self.stop_words and len(w) > 1]

        # Extract port keywords
        port_keywords = [w for w in words if w in self.proper_nouns]

        # Extract ship keywords
        ship_keywords = self._extract_ship_keywords(words)

        # Tier classification
        tiered = self._classify_by_tier(words, segment_type)

        # Primary keywords (T1-T3)
        primary = tiered.get("T1_PORT", []) + tiered.get("T2_SHIP", []) + tiered.get("T3_VISUAL", [])

        # Secondary keywords (T4-T6)
        secondary = tiered.get("T4_EMOTION", []) + tiered.get("T5_ACTION", []) + tiered.get("T6_GENERAL", [])

        # Map to English
        english = [self.english_map.get(k, k) for k in primary if k in self.english_map]

        return KeywordResult(
            primary=primary[:10],  # Top 10
            secondary=secondary[:5],  # Top 5
            english=english[:8],  # Top 8
            port_keywords=port_keywords,
            ship_keywords=ship_keywords,
        )

    def _remove_particles(self, text: str) -> str:
        """Remove Korean particles from text"""
        cleaned = text

        # Remove particles at word boundaries
        for josa in self.josa_set:
            # Remove particle at end of words
            cleaned = re.sub(rf"(\w+){josa}(\W|$)", r"\1\2", cleaned)

        return cleaned

    def _split_words(self, text: str) -> List[str]:
        """Split text into words"""
        # Korean word boundary regex
        words = re.findall(r"[\w]+", text)
        return words

    def _extract_ship_keywords(self, words: List[str]) -> List[str]:
        """Extract ship-related keywords"""
        ship_keywords = []

        ship_terms = {
            "워터슬라이드", "수영장", "자쿠지", "스파", "뷔페", "레스토랑",
            "극장", "카지노", "키즈클럽", "피트니스", "갑판", "발코니",
            "선실", "캐빈", "스위트", "VIP", "라운지", "바", "펍",
        }

        for word in words:
            if word in ship_terms:
                ship_keywords.append(word)

        return ship_keywords

    def _classify_by_tier(self, words: List[str], segment_type: str = None) -> Dict[str, List[str]]:
        """Classify words by tier priority"""
        tiered = {
            "T1_PORT": [],
            "T2_SHIP": [],
            "T3_VISUAL": [],
            "T4_EMOTION": [],
            "T5_ACTION": [],
            "T6_GENERAL": [],
        }

        # T1: Port names
        tiered["T1_PORT"] = [w for w in words if w in self.proper_nouns]

        # T2: Ship features
        ship_terms = {
            "워터슬라이드", "수영장", "자쿠지", "스파", "뷔페", "레스토랑",
            "극장", "카지노", "키즈클럽", "피트니스", "갑판", "발코니",
        }
        tiered["T2_SHIP"] = [w for w in words if w in ship_terms]

        # T3: Visual keywords
        visual_terms = {
            "일몰", "야경", "전망", "풍경", "바다", "하늘", "산", "빙하",
            "피오르드", "성당", "박물관", "구시가지", "항구", "등대",
        }
        tiered["T3_VISUAL"] = [w for w in words if w in visual_terms]

        # T4: Emotion keywords
        emotion_terms = {
            "행복", "감동", "놀라움", "평화", "설렘", "만족", "기쁨", "즐거움",
            "편안", "힐링", "낭만", "로맨틱", "추억", "특별",
        }
        tiered["T4_EMOTION"] = [w for w in words if w in emotion_terms]

        # T5: Action verbs
        action_terms = {
            "즐기다", "구경", "탐험", "체험", "맛보다", "감상", "산책", "휴식",
            "사진", "기록", "여행", "방문", "도착", "출발",
        }
        tiered["T5_ACTION"] = [w for w in words if w in action_terms]

        # T6: General (remaining words)
        classified = set()
        for tier_words in tiered.values():
            classified.update(tier_words)

        tiered["T6_GENERAL"] = [w for w in words if w not in classified]

        return tiered


# Export
def extract_keywords(text: str, segment_type: str = None) -> KeywordResult:
    """
    Extract keywords from text (convenience function).

    Args:
        text: Input text
        segment_type: Segment type for context

    Returns:
        KeywordResult
    """
    extractor = IntelligentKeywordExtractor()
    return extractor.extract_from_text(text, segment_type)


__all__ = [
    "IntelligentKeywordExtractor",
    "KeywordResult",
    "extract_keywords",
    "PROPER_NOUNS_PORTS",
    "JOSA_SET",
    "ENGLISH_KEYWORDS",  # Phase A Task 4: Pexels fallback
]
