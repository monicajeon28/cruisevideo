#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asset Matcher - 키워드 기반 로컬 에셋 매칭 엔진

역할:
- 키워드 기반으로 로컬 이미지/영상 에셋 매칭
- 기항지 우선순위 부여 (Phase 28 FIX-3: 178개 기항지)
- Content Type별 이미지 우선순위
- Hook 영상 3단계 fallback
- Visual Interleave (80% 이미지, 20% 영상)
- Ken Burns 효과 지원

Author: Claude Code (code-writer)
Created: 2026-03-08
Phase: B-9 Asset Matcher Reconstruction
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import random

# 키워드 추출기 import
try:
    from engines.keyword_extraction.intelligent_keyword_extractor import (
        PROPER_NOUNS_PORTS,
        PORT_MAP,
        IntelligentKeywordExtractor,
        ENGLISH_KEYWORDS
    )
except ImportError:
    PROPER_NOUNS_PORTS = []
    PORT_MAP = {}
    IntelligentKeywordExtractor = None
    ENGLISH_KEYWORDS = {}

# Phase A Task 4: Pexels API Fallback
try:
    from engines.pexels_video_fetcher import PexelsVideoFetcher
except ImportError:
    PexelsVideoFetcher = None

logger = logging.getLogger("AssetMatcher")


# ====================
# Constants
# ====================

def _build_asset_paths() -> dict:
    """PathResolver 기반 에셋 경로 빌드 (EXE 배포 대응)"""
    try:
        from path_resolver import get_paths
        p = get_paths()
        return {
            # 이미지
            "cruise_photos": p.image_dir / "크루즈정보사진정리",
            "review_images": p.image_dir / "후기",
            "general_images": p.image_dir,
            "ai_generated": p.raw_images_dir,
            "face_swapped": p.face_swapped_dir,
            "cutouts": p.cutouts_auto_dir,
            "cutouts_manual": p.cutouts_manual_dir,
            # 영상
            "hook_videos": p.hook_videos_dir,
            "footage": p.footage_dir,
            "ai_videos": p.ai_videos_dir,
        }
    except (ImportError, Exception):
        # Fallback: 기존 하드코딩 경로
        return {
            "cruise_photos": Path("D:/AntiGravity/Assets/Image/크루즈정보사진정리"),
            "review_images": Path("D:/AntiGravity/Assets/Image/후기"),
            "general_images": Path("D:/AntiGravity/Assets/Image"),
            "ai_generated": Path("D:/AntiGravity/Output/1_Raw_Images"),
            "face_swapped": Path("D:/AntiGravity/Output/2_Face_Swapped"),
            "cutouts": Path("D:/AntiGravity/Output/Cutouts_Auto"),
            "cutouts_manual": Path("D:/AntiGravity/Assets/누끼파일"),
            "hook_videos": Path("D:/AntiGravity/Assets/Footage/Hook"),
            "footage": Path("D:/AntiGravity/Assets/Footage"),
            "ai_videos": Path("D:/AntiGravity/Output/3_Videos"),
        }

# 로컬 에셋 경로
ASSET_PATHS = _build_asset_paths()

# 지원 확장자
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}

# Content Type별 우선순위 (Phase 28 FIX-8)
CONTENT_TYPE_PRIORITY = {
    "Hook": ["hook_videos", "footage", "ai_videos"],  # Hook 전용 폴더 우선
    "Body": ["cruise_photos", "general_images", "ai_generated", "face_swapped"],
    "Trust": ["review_images", "cruise_photos"],  # 후기 이미지 우선
    "CTA": ["review_images", "cruise_photos"],  # 후기 이미지 우선
    "Outro": ["review_images", "cruise_photos"],  # 후기 이미지 우선
}

# 누끼 파일 카테고리 (Phase 28 FIX-8C)
CUTOUT_CATEGORIES = {
    "식사": ["뷔페", "정찬", "다이닝", "레스토랑", "요리"],
    "선내시설": ["수영장", "스파", "카지노", "극장", "워터파크"],
    "액티비티": ["공연", "쇼", "파티", "이벤트"],
    "기항지": PROPER_NOUNS_PORTS,  # 178개 기항지
    "Trust": ["후기", "만족", "리뷰", "체험"],
}


# ====================
# Data Classes
# ====================

@dataclass
class AssetMatch:
    """에셋 매칭 결과"""
    path: Path
    score: float  # 매칭 점수 (0-100)
    matched_keywords: List[str]  # 매칭된 키워드
    asset_type: str  # "image" or "video"
    is_cutout: bool = False  # 누끼 파일 여부
    is_hook: bool = False  # Hook 전용 영상 여부


@dataclass
class VisualSegment:
    """비주얼 세그먼트 (이미지/비디오 교차)"""
    path: Path
    duration: float
    asset_type: str  # "image" or "video"
    ken_burns_type: Optional[str] = None  # "zoom_in", "zoom_out", "pan_left", "pan_right"
    keywords: List[str] = None


# ====================
# Asset Matcher Class
# ====================

class AssetMatcher:
    """키워드 기반 에셋 매칭 엔진"""

    def __init__(self):
        """초기화 (Phase A Task 4: Pexels fallback 추가)"""
        self.keyword_extractor = IntelligentKeywordExtractor() if IntelligentKeywordExtractor else None
        self._asset_cache = {}  # 경로별 에셋 캐시
        self._keyword_cache = {}  # 키워드별 에셋 캐시

        # Phase A Task 4: Pexels API Fallback
        try:
            self.pexels_fetcher = PexelsVideoFetcher() if PexelsVideoFetcher else None
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            logger.warning(f"[AssetMatcher] Pexels API 초기화 실패: {e}")
            self.pexels_fetcher = None

        # 에셋 인덱싱
        self._index_assets()

        logger.info(f"[AssetMatcher] 초기화 완료 - 인덱싱: {len(self._asset_cache)}개 에셋, Pexels: {'사용' if self.pexels_fetcher else '비활성'}")

    def _index_assets(self):
        """에셋 파일 인덱싱 (시작 시 1회 실행)"""
        for asset_key, asset_path in ASSET_PATHS.items():
            if not asset_path.exists():
                logger.warning(f"[AssetMatcher] 경로 없음: {asset_path}")
                continue

            # 재귀 탐색
            for file_path in asset_path.rglob("*"):
                if not file_path.is_file():
                    continue

                ext = file_path.suffix.lower()

                if ext in IMAGE_EXTENSIONS:
                    asset_type = "image"
                elif ext in VIDEO_EXTENSIONS:
                    asset_type = "video"
                else:
                    continue

                # 캐시 저장
                self._asset_cache[str(file_path)] = {
                    "path": file_path,
                    "type": asset_type,
                    "category": asset_key,
                    "keywords": self._extract_keywords_from_path(file_path),
                }

        logger.info(f"[AssetMatcher] 인덱싱 완료: {len(self._asset_cache)}개 에셋")

    def _extract_keywords_from_path(self, file_path: Path) -> List[str]:
        """파일 경로에서 키워드 추출

        예시:
            "D:/Assets/Image/크루즈정보사진정리/일본 나가사키/IMG_001.jpg"
            → ["일본", "나가사키", "크루즈"]
        """
        keywords = []

        # 경로 전체에서 키워드 추출
        path_str = str(file_path)

        # 1. 기항지명 추출 (178개)
        for port in PROPER_NOUNS_PORTS:
            if port in path_str:
                keywords.append(port)

                # 기항지 확장 키워드 추가
                if port in PORT_MAP:
                    keywords.extend(PORT_MAP[port][:3])  # 상위 3개

        # 2. 일반 한글 키워드 (2자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', path_str)
        keywords.extend(korean_words)

        # 3. 영어 키워드 (3자 이상)
        english_words = re.findall(r'[A-Za-z]{3,}', path_str)
        keywords.extend(english_words)

        # 중복 제거
        return list(set(keywords))

    def match_assets(
        self,
        keywords: List[str],
        content_type: str = "Body",
        max_results: int = 10,
        prefer_images: bool = True,
        allow_videos: bool = True,
        exclude_paths: set = None
    ) -> List[AssetMatch]:
        """키워드 기반 에셋 매칭

        Args:
            keywords: 검색 키워드 리스트
            content_type: "Hook", "Body", "Trust", "CTA", "Outro"
            max_results: 최대 결과 개수
            prefer_images: 이미지 우선 (Visual Interleave 80%)
            allow_videos: 영상 허용 (Visual Interleave 20%)
            exclude_paths: 제외할 에셋 경로 문자열 set (중복 방지)

        Returns:
            매칭된 에셋 리스트 (점수 내림차순)
        """
        matches = []

        # Content Type별 우선순위 경로
        priority_categories = CONTENT_TYPE_PRIORITY.get(content_type, ["cruise_photos"])

        # 에셋 매칭
        for asset_key, asset_info in self._asset_cache.items():
            asset_type = asset_info["type"]
            asset_category = asset_info["category"]
            asset_keywords = asset_info["keywords"]

            # 타입 필터링
            if asset_type == "video" and not allow_videos:
                continue

            # 키워드 매칭 점수 계산
            score = self._calculate_match_score(
                keywords=keywords,
                asset_keywords=asset_keywords,
                asset_category=asset_category,
                priority_categories=priority_categories
            )

            if score >= 15:  # Lowered from 30 to match broader scoring
                matches.append(AssetMatch(
                    path=asset_info["path"],
                    score=score,
                    matched_keywords=[k for k in keywords if k in asset_keywords],
                    asset_type=asset_type,
                    is_hook=(asset_category == "hook_videos")
                ))

        # 제외 경로 필터링 (중복 방지)
        if exclude_paths:
            matches = [m for m in matches if str(m.path) not in exclude_paths]

        # 점수 내림차순 정렬
        matches.sort(key=lambda x: x.score, reverse=True)

        # 로컬 매칭 실패 시: 우선 카테고리에서 랜덤 선택 (Pexels 전에)
        if not matches:
            logger.info(f"[AssetMatcher] 키워드 매칭 0건 - 우선 카테고리 랜덤 선택 시도")
            category_assets = [
                asset for asset in self._asset_cache.values()
                if asset["category"] in priority_categories
                and (asset["type"] == "image" if prefer_images else True)
                and (asset["type"] != "video" or allow_videos)
            ]
            if category_assets:
                selected = random.sample(category_assets, min(max_results, len(category_assets)))
                for asset in selected:
                    matches.append(AssetMatch(
                        path=asset["path"],
                        score=10.0,  # 랜덤 선택 최소 점수
                        matched_keywords=[],
                        asset_type=asset["type"],
                        is_hook=(asset["category"] == "hook_videos")
                    ))
                logger.info(f"[AssetMatcher] 우선 카테고리 랜덤: {len(matches)}개 선택")

        # 이미지 우선 필터링 (prefer_images=True)
        if prefer_images:
            image_matches = [m for m in matches if m.asset_type == "image"]
            video_matches = [m for m in matches if m.asset_type == "video"]

            # 80% 이미지, 20% 영상
            image_count = int(max_results * 0.8)
            video_count = max_results - image_count

            matches = image_matches[:image_count] + video_matches[:video_count]

        # Phase A Task 4: Pexels API Fallback (로컬 에셋 부족 시)
        if len(matches) < max_results and self.pexels_fetcher and allow_videos:
            shortage = max_results - len(matches)
            logger.info(f"[AssetMatcher] 로컬 에셋 부족 ({len(matches)}/{max_results}) - Pexels API fallback 시도")

            # 한국어 키워드 → 영어 키워드 변환
            english_keywords = []
            for kw in keywords[:3]:  # 상위 3개 키워드만
                if kw in ENGLISH_KEYWORDS:
                    english_keywords.append(ENGLISH_KEYWORDS[kw])
                else:
                    english_keywords.append(kw)  # 영어 키워드 그대로 사용

            # Pexels 검색 쿼리 생성
            query = " ".join(english_keywords) if english_keywords else "cruise travel"

            try:
                # Pexels에서 비디오 검색
                fallback_path = self.pexels_fetcher.get_fallback_video(
                    keywords=keywords,
                    category_hint="cruise"
                )

                if fallback_path:
                    # Pexels 비디오를 matches에 추가
                    matches.append(AssetMatch(
                        path=Path(fallback_path),
                        score=25.0,  # 낮은 점수 (로컬보다 우선순위 낮음)
                        matched_keywords=keywords[:2],
                        asset_type="video",
                        is_hook=False
                    ))
                    logger.info(f"[AssetMatcher] Pexels fallback 성공: {fallback_path}")
                else:
                    logger.warning(f"[AssetMatcher] Pexels fallback 실패: {query}")

            except (OSError, ValueError, RuntimeError) as e:
                logger.error(f"[AssetMatcher] Pexels API 오류: {e}")

        return matches[:max_results]

    # 크루즈 관련 암묵적 키워드 (cruise_photos/footage 카테고리 보너스)
    IMPLICIT_CRUISE_KEYWORDS = {"크루즈", "cruise", "ship", "여행", "바다", "ocean"}

    def _calculate_match_score(
        self,
        keywords: List[str],
        asset_keywords: List[str],
        asset_category: str,
        priority_categories: List[str]
    ) -> float:
        """매칭 점수 계산 (0-100)

        점수 구성:
        - 기항지 매칭: +50점 (Phase 28 FIX-3 기항지 우선)
        - 일반 키워드 정확 매칭: +10점/개
        - 부분 매칭 (substring): +5점/개
        - 카테고리 우선순위: +20점 (1순위), +10점 (2순위)
        - 우선 카테고리 기본 점수: +15점
        - 크루즈 카테고리 암묵적 매칭: +10점/개
        """
        score = 0.0

        # 1. 키워드 매칭 (정확 + 부분)
        matched_exact = set()
        for keyword in keywords:
            if keyword in asset_keywords:
                matched_exact.add(keyword)
                # 기항지 키워드는 2배 가중치
                if keyword in PROPER_NOUNS_PORTS:
                    score += 50.0
                else:
                    score += 10.0
            else:
                # 부분 매칭: keyword가 asset_keyword의 substring이거나 반대
                for ak in asset_keywords:
                    if len(keyword) >= 2 and len(ak) >= 2:
                        if keyword in ak or ak in keyword:
                            score += 5.0
                            break  # 한 번만 카운트

        # 2. 카테고리 우선순위
        if asset_category in priority_categories:
            priority_index = priority_categories.index(asset_category)
            if priority_index == 0:
                score += 20.0
            elif priority_index == 1:
                score += 10.0
            # 우선 카테고리 기본 점수 (키워드 매칭 없어도)
            score += 15.0

        # 3. 크루즈 카테고리 암묵적 매칭
        if asset_category in ("cruise_photos", "footage", "review_images"):
            for ck in self.IMPLICIT_CRUISE_KEYWORDS:
                if ck in keywords:
                    score += 10.0

        return min(score, 100.0)

    def get_hook_video(
        self,
        keywords: List[str],
        fallback: bool = True
    ) -> Optional[Path]:
        """Hook 영상 선택 (3단계 fallback)

        Phase 28 FIX-4: Hook 전용 폴더 104개 우선 선택

        Fallback 순서:
        1. Hook 폴더에서 키워드 매칭
        2. Footage 폴더에서 키워드 매칭
        3. AI 생성 영상에서 키워드 매칭
        4. Hook 폴더 랜덤 선택 (최후)

        Args:
            keywords: 검색 키워드
            fallback: fallback 허용 여부

        Returns:
            Hook 영상 경로 (없으면 None)
        """
        # 1단계: Hook 폴더 키워드 매칭
        matches = self.match_assets(
            keywords=keywords,
            content_type="Hook",
            max_results=1,
            prefer_images=False,
            allow_videos=True
        )

        if matches:
            logger.info(f"[Hook] 1단계 매칭: {matches[0].path.name} (점수: {matches[0].score})")
            return matches[0].path

        if not fallback:
            return None

        # 2단계: Footage 폴더
        footage_videos = [
            asset for asset in self._asset_cache.values()
            if asset["category"] == "footage" and asset["type"] == "video"
        ]

        if footage_videos:
            video = random.choice(footage_videos)
            logger.info(f"[Hook] 2단계 fallback: {video['path'].name}")
            return video["path"]

        # 3단계: AI 영상
        ai_videos = [
            asset for asset in self._asset_cache.values()
            if asset["category"] == "ai_videos" and asset["type"] == "video"
        ]

        if ai_videos:
            video = random.choice(ai_videos)
            logger.info(f"[Hook] 3단계 fallback: {video['path'].name}")
            return video["path"]

        # 4단계: Hook 폴더 랜덤
        hook_videos = [
            asset for asset in self._asset_cache.values()
            if asset["category"] == "hook_videos" and asset["type"] == "video"
        ]

        if hook_videos:
            video = random.choice(hook_videos)
            logger.warning(f"[Hook] 4단계 랜덤: {video['path'].name}")
            return video["path"]

        logger.error("[Hook] 영상을 찾을 수 없음")
        return None

    def get_visual_segments(
        self,
        keywords: List[str],
        total_duration: float,
        content_type: str = "Body",
        interleave_ratio: float = 0.8  # 80% 이미지, 20% 영상
    ) -> List[VisualSegment]:
        """Visual Interleave: 이미지/비디오 교차 세그먼트 생성

        Args:
            keywords: 키워드 리스트
            total_duration: 전체 길이 (초)
            content_type: "Hook", "Body", "Trust", "CTA", "Outro"
            interleave_ratio: 이미지 비율 (0.8 = 80%)

        Returns:
            시각 세그먼트 리스트
        """
        segments = []

        # 세그먼트당 평균 길이 (5-7초)
        avg_segment_duration = random.uniform(5.0, 7.0)
        num_segments = max(1, int(total_duration / avg_segment_duration))

        # 이미지/비디오 개수 계산
        num_images = int(num_segments * interleave_ratio)
        num_videos = num_segments - num_images

        # 에셋 매칭
        matches = self.match_assets(
            keywords=keywords,
            content_type=content_type,
            max_results=num_segments * 2,  # 여유 있게
            prefer_images=True,
            allow_videos=True
        )

        # 이미지/비디오 분리
        image_matches = [m for m in matches if m.asset_type == "image"]
        video_matches = [m for m in matches if m.asset_type == "video"]

        # 세그먼트 생성 (이미지 우선)
        used_duration = 0.0

        for i in range(num_segments):
            # 남은 시간 계산
            remaining_duration = total_duration - used_duration
            if remaining_duration <= 0:
                break

            # 세그먼트 길이
            if i < num_segments - 1:
                segment_duration = min(avg_segment_duration, remaining_duration)
            else:
                segment_duration = remaining_duration

            # 이미지 우선, 영상 교차
            if i < num_images and image_matches:
                match = image_matches.pop(0)

                # Ken Burns 효과 타입 랜덤
                ken_burns_type = random.choice([
                    "zoom_in", "zoom_out", "pan_left", "pan_right"
                ])

                segments.append(VisualSegment(
                    path=match.path,
                    duration=segment_duration,
                    asset_type="image",
                    ken_burns_type=ken_burns_type,
                    keywords=match.matched_keywords
                ))

            elif video_matches:
                match = video_matches.pop(0)

                segments.append(VisualSegment(
                    path=match.path,
                    duration=segment_duration,
                    asset_type="video",
                    keywords=match.matched_keywords
                ))

            used_duration += segment_duration

        logger.info(f"[VisualSegments] {len(segments)}개 생성 (이미지: {num_images}, 영상: {num_videos})")
        return segments

    def get_cutout_asset(
        self,
        keywords: List[str],
        category: Optional[str] = None
    ) -> Optional[Path]:
        """누끼 파일 매칭 (Phase 28 FIX-8C)

        Args:
            keywords: 키워드 리스트
            category: "식사", "선내시설", "액티비티", "기항지", "Trust"

        Returns:
            누끼 파일 경로 (없으면 None)
        """
        cutout_assets = [
            asset for asset in self._asset_cache.values()
            if asset["category"] in ["cutouts", "cutouts_manual"]
        ]

        if not cutout_assets:
            return None

        # 카테고리별 필터링
        if category and category in CUTOUT_CATEGORIES:
            category_keywords = CUTOUT_CATEGORIES[category]

            # 카테고리 키워드 + 검색 키워드
            all_keywords = list(set(keywords + category_keywords))
        else:
            all_keywords = keywords

        # 매칭
        matches = []
        for asset in cutout_assets:
            score = self._calculate_match_score(
                keywords=all_keywords,
                asset_keywords=asset["keywords"],
                asset_category=asset["category"],
                priority_categories=["cutouts_manual", "cutouts"]
            )

            if score >= 20:
                matches.append((asset["path"], score))

        if not matches:
            return None

        # 점수 내림차순 정렬
        matches.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"[Cutout] 매칭: {matches[0][0].name} (점수: {matches[0][1]})")
        return matches[0][0]


# ====================
# Singleton Instance
# ====================

_instance = None

def get_asset_matcher() -> AssetMatcher:
    """싱글톤 인스턴스 반환"""
    global _instance
    if _instance is None:
        _instance = AssetMatcher()
    return _instance


# ====================
# Legacy Compatibility
# ====================

def match_assets(keywords: List[str], **kwargs) -> List[Path]:
    """레거시 호환 함수"""
    matcher = get_asset_matcher()
    matches = matcher.match_assets(keywords, **kwargs)
    return [m.path for m in matches]


# ====================
# CLI Test
# ====================

if __name__ == "__main__":
    import sys

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # AssetMatcher 초기화
    matcher = AssetMatcher()

    # 테스트 케이스
    test_cases = [
        (["나가사키", "하우스텐보스"], "Body"),
        (["산토리니", "그리스"], "Body"),
        (["MSC 벨리시마"], "Body"),
        (["후기", "만족"], "Trust"),
        (["크루즈"], "Hook"),
    ]

    print("=" * 80)
    print("AssetMatcher 테스트")
    print("=" * 80)

    for keywords, content_type in test_cases:
        print(f"\n[테스트] 키워드: {keywords} | Type: {content_type}")

        matches = matcher.match_assets(
            keywords=keywords,
            content_type=content_type,
            max_results=5
        )

        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match.path.name}")
            print(f"     점수: {match.score:.1f} | 타입: {match.asset_type}")
            print(f"     매칭 키워드: {', '.join(match.matched_keywords)}")

    print("\n" + "=" * 80)
    print("Hook 영상 테스트")
    print("=" * 80)

    hook_video = matcher.get_hook_video(["크루즈", "나가사키"])
    if hook_video:
        print(f"  선택: {hook_video.name}")
    else:
        print("  Hook 영상 없음")

    print("\n" + "=" * 80)
    print("Visual Interleave 테스트 (46초)")
    print("=" * 80)

    segments = matcher.get_visual_segments(
        keywords=["산토리니", "그리스", "에게해"],
        total_duration=46.0,
        content_type="Body",
        interleave_ratio=0.8
    )

    for i, seg in enumerate(segments, 1):
        print(f"  {i}. {seg.path.name}")
        print(f"     길이: {seg.duration:.1f}초 | 타입: {seg.asset_type}")
        if seg.ken_burns_type:
            print(f"     Ken Burns: {seg.ken_burns_type}")
        print(f"     키워드: {', '.join(seg.keywords or [])}")

    print("\n" + "=" * 80)
