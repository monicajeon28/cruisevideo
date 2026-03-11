"""
Pexels Video Fetcher
Pexels API를 사용하여 Shorts용 세로형 영상을 검색하고 다운로드
- 200 requests/hour, 20,000 requests/month (무료 플랜)
- Orientation: Portrait (1080x1920)
- Quality: Medium/Large
"""

import os
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PexelsVideoFetcher:
    """Pexels API 영상 검색 및 다운로드"""

    def __init__(self):
        self.api_key = os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not found in .env file")

        self.base_url = "https://api.pexels.com/v1"
        self.headers = {"Authorization": self.api_key}
        if os.getenv("LOCAL_FOOTAGE_DIR"):
            self.download_dir = Path(os.getenv("LOCAL_FOOTAGE_DIR")) / "Pexels"
        else:
            try:
                from path_resolver import get_paths
                self.download_dir = get_paths().footage_dir / "Pexels"
            except (ImportError, Exception):
                self.download_dir = Path("D:\\AntiGravity\\Assets\\Footage") / "Pexels"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def search_videos(
        self,
        query: str,
        per_page: int = 15,
        orientation: str = "portrait",
        size: str = "medium"
    ) -> List[Dict]:
        """
        Pexels 영상 검색

        Args:
            query: 검색 키워드 (예: "cruise ship", "ocean travel", "sea voyage")
            per_page: 결과 개수 (기본 15개)
            orientation: portrait (세로), landscape (가로), square (정사각형)
            size: small, medium, large

        Returns:
            영상 메타데이터 리스트
        """
        url = f"{self.base_url}/videos/search"
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": size
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            videos = data.get("videos", [])
            logger.info(f"Found {len(videos)} videos for query: '{query}'")
            return videos

        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels API request failed: {e}")
            return []

    def download_video(
        self,
        video_url: str,
        save_filename: str,
        overwrite: bool = False
    ) -> Optional[str]:
        """
        영상 다운로드

        Args:
            video_url: 영상 다운로드 URL
            save_filename: 저장할 파일명 (예: "cruise_ocean_001.mp4")
            overwrite: 기존 파일 덮어쓰기 여부

        Returns:
            다운로드된 파일 경로 (실패 시 None)
        """
        save_path = self.download_dir / save_filename

        # 이미 존재하는 파일 체크
        if save_path.exists() and not overwrite:
            logger.info(f"File already exists: {save_path}")
            return str(save_path)

        try:
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded video: {save_path}")
            return str(save_path)

        except requests.exceptions.RequestException as e:
            logger.error(f"Video download failed: {e}")
            return None

    def get_best_quality_url(self, video_files: List[Dict], preferred_quality: str = "hd") -> Optional[str]:
        """
        영상 파일 목록에서 최적 품질 URL 선택

        Args:
            video_files: Pexels API의 video_files 리스트
            preferred_quality: 선호 품질 (hd, sd, uhd)

        Returns:
            다운로드 URL (없으면 None)
        """
        # 품질 우선순위: hd > sd > uhd
        quality_priority = ["hd", "sd", "uhd"]

        if preferred_quality in quality_priority:
            # 선호 품질을 최우선으로
            quality_priority.remove(preferred_quality)
            quality_priority.insert(0, preferred_quality)

        for quality in quality_priority:
            for video_file in video_files:
                if video_file.get("quality") == quality:
                    return video_file.get("link")

        # 품질 매칭 실패 시 첫 번째 파일 반환
        if video_files:
            return video_files[0].get("link")

        return None

    def get_fallback_video(
        self,
        keywords: List[str],
        category_hint: str = "cruise"
    ) -> Optional[str]:
        """
        로컬 영상이 없을 때 Pexels에서 자동 검색 및 다운로드

        Args:
            keywords: 키워드 리스트 (예: ["나가사키", "항구", "일본"])
            category_hint: 카테고리 힌트 (cruise, ocean, travel 등)

        Returns:
            다운로드된 영상 경로 (실패 시 None)
        """
        # 한글 키워드 → 영어 변환 (기항지명, 선박명 등)
        english_kws = []
        try:
            from engines.keyword_extraction.intelligent_keyword_extractor import ENGLISH_KEYWORDS
            for kw in keywords[:3]:
                if kw in ENGLISH_KEYWORDS:
                    english_kws.append(ENGLISH_KEYWORDS[kw])
                elif all(ord(c) < 128 for c in kw):
                    english_kws.append(kw)  # 이미 영어
        except ImportError:
            english_kws = [kw for kw in keywords[:3] if all(ord(c) < 128 for c in kw)]

        # 검색 쿼리 생성 (기항지+크루즈 특화)
        location_query = ' '.join(english_kws[:2]) if english_kws else ''
        search_queries = [
            f"cruise ship {location_query}".strip(),           # 기항지별 크루즈
            f"{location_query} travel tourism".strip() if location_query else "cruise ship deck ocean",  # 기항지 관광
            "luxury cruise ship deck ocean",                   # 럭셔리 크루즈
            "cruise ship ocean voyage",                        # 크루즈 항해
        ]

        for query in search_queries:
            videos = self.search_videos(query, per_page=5)

            if not videos:
                continue

            # 첫 번째 영상 다운로드 시도
            video = videos[0]
            video_files = video.get("video_files", [])

            if not video_files:
                continue

            download_url = self.get_best_quality_url(video_files, preferred_quality="hd")

            if not download_url:
                continue

            # 파일명 생성 (video_id + .mp4)
            video_id = video.get("id", "unknown")
            filename = f"pexels_{category_hint}_{video_id}.mp4"

            downloaded_path = self.download_video(download_url, filename)

            if downloaded_path:
                logger.info(f"Fallback video downloaded: {downloaded_path}")
                return downloaded_path

        logger.warning(f"No fallback video found for keywords: {keywords}")
        return None

    def batch_download(
        self,
        query: str,
        count: int = 10,
        prefix: str = "cruise"
    ) -> List[str]:
        """
        배치 다운로드 (여러 영상을 한번에)

        Args:
            query: 검색 쿼리
            count: 다운로드할 영상 개수
            prefix: 파일명 접두사

        Returns:
            다운로드된 파일 경로 리스트
        """
        videos = self.search_videos(query, per_page=count)
        downloaded_paths = []

        for idx, video in enumerate(videos[:count], start=1):
            video_files = video.get("video_files", [])

            if not video_files:
                continue

            download_url = self.get_best_quality_url(video_files)

            if not download_url:
                continue

            video_id = video.get("id", f"{idx:03d}")
            filename = f"{prefix}_{video_id}.mp4"

            downloaded_path = self.download_video(download_url, filename)

            if downloaded_path:
                downloaded_paths.append(downloaded_path)

        logger.info(f"Batch download completed: {len(downloaded_paths)}/{count} videos")
        return downloaded_paths


# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    fetcher = PexelsVideoFetcher()

    # 1. 단일 검색
    videos = fetcher.search_videos("cruise ship ocean", per_page=5)
    print(f"Found {len(videos)} videos")

    # 2. 첫 번째 영상 다운로드
    if videos:
        video = videos[0]
        video_files = video.get("video_files", [])
        if video_files:
            url = fetcher.get_best_quality_url(video_files)
            if url:
                path = fetcher.download_video(url, "test_cruise.mp4")
                print(f"Downloaded: {path}")

    # 3. Fallback 영상 검색
    fallback_path = fetcher.get_fallback_video(
        keywords=["나가사키", "항구"],
        category_hint="cruise"
    )
    print(f"Fallback video: {fallback_path}")

    # 4. 배치 다운로드
    batch_paths = fetcher.batch_download("ocean travel", count=3, prefix="ocean")
    print(f"Batch downloaded: {len(batch_paths)} videos")
