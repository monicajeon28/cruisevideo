#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Trend RAG Collector - 크루즈/여행 트렌드 수집기

YouTube Data API v3를 사용하여 크루즈/여행 관련 Shorts 트렌드를 수집하고
RAG 컨텍스트로 변환한다.

쿼터 효율: 1회 수집당 ~303 유닛 (search 3회=300 + videos batch 3=3)
24시간 캐시 TTL (캐시 유효하면 API 호출 0)
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 프로젝트 루트
_PROJECT_ROOT = Path(__file__).parent.parent

# 캐시 / 학습 데이터 경로
CACHE_PATH = _PROJECT_ROOT / "data" / "trend_cache.json"
LEARNING_DATA_DIR = _PROJECT_ROOT / "Learning_Data"

# 검색 쿼리 (3개 = 300 유닛)
SEARCH_QUERIES = [
    "크루즈 여행 2026",
    "크루즈 꿀팁 50대",
    "cruise ship review korea",
]

# 캐시 TTL (24시간)
CACHE_TTL_HOURS = 24

# 트렌드 키워드 추출 시 제외할 불용어
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall",
    "이", "그", "저", "것", "수", "등", "더", "또", "및", "를", "을",
    "에", "의", "가", "는", "은", "로", "와", "과", "도", "한", "된",
    "하는", "있는", "없는", "하다", "있다", "없다", "합니다", "입니다",
    "shorts", "short", "youtube", "vlog", "브이로그",
}


class YouTubeTrendCollector:
    """YouTube 크루즈/여행 트렌드 수집기

    - YouTube Data API v3로 Shorts 트렌드 수집
    - 24시간 캐시 (API 호출 최소화)
    - 트렌드 키워드 추출 + RAG 컨텍스트 생성
    """

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self._cache: Optional[Dict] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect(self) -> Optional[Dict]:
        """트렌드 수집 (캐시 유효하면 스킵)

        Returns:
            수집 결과 dict 또는 None (API키 없거나 실패 시)
        """
        if not self.api_key:
            logger.debug("YOUTUBE_API_KEY 미설정 - 트렌드 수집 스킵")
            return None

        # 캐시 확인
        cached = self._load_cache()
        if cached and self._is_cache_valid(cached):
            logger.debug("트렌드 캐시 유효 (API 호출 스킵)")
            self._cache = cached
            return cached

        # API 수집
        try:
            result = self._fetch_from_api()
            if result:
                self._save_cache(result)
                self._save_learning_data(result)
                self._cache = result
                logger.info(
                    "YouTube 트렌드 수집 완료: %d개 영상, %d개 키워드",
                    result.get("total_videos", 0),
                    len(result.get("trending_keywords", [])),
                )
                return result
        except Exception as e:
            logger.warning("YouTube 트렌드 수집 실패: %s", e)

        return None

    def get_rag_context(self) -> str:
        """RAG 컨텍스트 문자열 반환 (Gemini 프롬프트 주입용)

        Returns:
            트렌드 요약 문자열 (없으면 빈 문자열)
        """
        data = self._cache or self._load_cache()
        if not data:
            return ""

        return self._build_rag_summary(data)

    # ------------------------------------------------------------------
    # API 호출
    # ------------------------------------------------------------------

    def _fetch_from_api(self) -> Optional[Dict]:
        """YouTube Data API v3 호출"""
        try:
            from googleapiclient.discovery import build
        except ImportError:
            logger.debug("google-api-python-client 미설치 - 트렌드 수집 스킵")
            return None

        youtube = build("youtube", "v3", developerKey=self.api_key)

        try:
            return self._execute_queries(youtube)
        finally:
            youtube.close()

    def _execute_queries(self, youtube) -> Optional[Dict]:
        """API 쿼리 실행 (리소스 해제는 호출자 책임)"""
        all_videos = []
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=30)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 3개 검색 쿼리 실행 (~300 유닛)
        for query in SEARCH_QUERIES:
            try:
                search_resp = (
                    youtube.search()
                    .list(
                        q=query,
                        part="snippet",
                        maxResults=20,
                        order="viewCount",
                        type="video",
                        videoDuration="short",
                        regionCode="KR",
                        publishedAfter=published_after,
                    )
                    .execute()
                )

                for item in search_resp.get("items", []):
                    video_id = item["id"].get("videoId", "")
                    if not video_id:
                        continue
                    snippet = item.get("snippet", {})
                    all_videos.append({
                        "video_id": video_id,
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "query": query,
                    })

            except Exception as e:
                logger.warning("검색 실패 (%s): %s", query, e)

        if not all_videos:
            return None

        # 중복 제거
        seen_ids = set()
        unique_videos = []
        for v in all_videos:
            if v["video_id"] not in seen_ids:
                seen_ids.add(v["video_id"])
                unique_videos.append(v)

        # videos.list로 통계 보강 (~3 유닛, 50개씩 batch)
        video_ids = [v["video_id"] for v in unique_videos]
        stats_map = {}

        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            try:
                stats_resp = (
                    youtube.videos()
                    .list(
                        id=",".join(batch),
                        part="statistics",
                    )
                    .execute()
                )
                for item in stats_resp.get("items", []):
                    vid = item["id"]
                    s = item.get("statistics", {})
                    stats_map[vid] = {
                        "view_count": int(s.get("viewCount", 0)),
                        "like_count": int(s.get("likeCount", 0)),
                        "comment_count": int(s.get("commentCount", 0)),
                    }
            except Exception as e:
                logger.warning("통계 조회 실패: %s", e)

        # 통계 병합
        for v in unique_videos:
            stats = stats_map.get(v["video_id"], {})
            v["view_count"] = stats.get("view_count", 0)
            v["like_count"] = stats.get("like_count", 0)
            v["comment_count"] = stats.get("comment_count", 0)

        # 조회수 기준 정렬
        unique_videos.sort(key=lambda x: x.get("view_count", 0), reverse=True)

        # 트렌드 키워드 추출
        trending_keywords = self._extract_keywords(unique_videos)

        result = {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "total_videos": len(unique_videos),
            "queries": SEARCH_QUERIES,
            "top_videos": unique_videos[:20],
            "trending_keywords": trending_keywords,
        }

        return result

    # ------------------------------------------------------------------
    # 키워드 추출
    # ------------------------------------------------------------------

    def _extract_keywords(self, videos: List[Dict]) -> List[Dict]:
        """제목에서 빈출 단어 추출 (간단 regex, 외부 의존성 없음)"""
        word_freq: Dict[str, int] = {}

        for v in videos:
            title = v.get("title", "")
            # 한글 단어 (2글자 이상) + 영문 단어 (3글자 이상)
            korean_words = re.findall(r"[가-힣]{2,}", title)
            english_words = re.findall(r"[a-zA-Z]{3,}", title.lower())

            for word in korean_words + english_words:
                w = word.lower()
                if w not in STOPWORDS and len(w) >= 2:
                    word_freq[w] = word_freq.get(w, 0) + 1

        # 빈도순 정렬, 상위 20개
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [
            {"keyword": kw, "count": cnt}
            for kw, cnt in sorted_keywords[:20]
        ]

    # ------------------------------------------------------------------
    # RAG 요약 (템플릿 기반, Gemini 호출 X)
    # ------------------------------------------------------------------

    def _build_rag_summary(self, data: Dict) -> str:
        """트렌드 데이터를 RAG 컨텍스트 문자열로 변환"""
        lines = []
        lines.append(f"수집일시: {data.get('collected_at', 'N/A')}")
        lines.append(f"분석 영상 수: {data.get('total_videos', 0)}개")

        # 트렌드 키워드
        keywords = data.get("trending_keywords", [])
        if keywords:
            kw_str = ", ".join(
                f"{k['keyword']}({k['count']}회)" for k in keywords[:10]
            )
            lines.append(f"인기 키워드: {kw_str}")

        # Top 5 영상
        top_videos = data.get("top_videos", [])[:5]
        if top_videos:
            lines.append("인기 영상 TOP 5:")
            for i, v in enumerate(top_videos, 1):
                views = v.get("view_count", 0)
                views_str = f"{views:,}" if views else "N/A"
                lines.append(
                    f"  {i}. [{v.get('channel', '')}] {v.get('title', '')} "
                    f"(조회수: {views_str})"
                )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 캐시
    # ------------------------------------------------------------------

    def _load_cache(self) -> Optional[Dict]:
        """캐시 파일 로드"""
        try:
            if CACHE_PATH.exists():
                with open(CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.debug("트렌드 캐시 로드 실패: %s", e)
        return None

    def _is_cache_valid(self, cached: Dict) -> bool:
        """캐시 TTL 확인 (24시간)"""
        collected_at = cached.get("collected_at", "")
        if not collected_at:
            return False
        try:
            collected_dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - collected_dt).total_seconds() < CACHE_TTL_HOURS * 3600
        except Exception:
            return False

    def _save_cache(self, data: Dict) -> None:
        """캐시 파일 저장"""
        try:
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("트렌드 캐시 저장: %s", CACHE_PATH)
        except Exception as e:
            logger.warning("트렌드 캐시 저장 실패: %s", e)

    # ------------------------------------------------------------------
    # 학습 데이터 축적
    # ------------------------------------------------------------------

    def _save_learning_data(self, data: Dict) -> None:
        """Learning_Data/youtube_trends_YYYYMMDD.json에 날짜별 저장"""
        try:
            LEARNING_DATA_DIR.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            path = LEARNING_DATA_DIR / f"youtube_trends_{date_str}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("트렌드 학습 데이터 저장: %s", path)
        except Exception as e:
            logger.warning("트렌드 학습 데이터 저장 실패: %s", e)
