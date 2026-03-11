#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AssetDiversityManager - 에셋 다양성 관리

100개 영상이 시각적으로 다르게 보이도록 에셋 사용 관리.

기능:
1. 에셋 사용 빈도 추적
2. 가중치 기반 랜덤 선택 (덜 사용된 에셋 우선)
3. 최근 N개 영상에서 사용된 에셋 제외
4. 카테고리별 균등 분배
5. S2-A3: 에셋 히스토리 영속 저장 (세션 간 중복 방지)
"""

import json
import logging
import random
import threading
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AssetUsageStats:
    """에셋 사용 통계"""
    path: str = ""
    count: int = 0
    category: str = ""
    last_used: str = ""


class AssetDiversityManager:
    """
    에셋 다양성 관리자

    100개 영상이 시각적으로 다르게 보이도록
    - 동일 에셋 과다 사용 방지
    - 최근 사용 에셋 회피
    - 카테고리별 균등 분배
    - S2-A3: 세션 간 히스토리 영속 저장
    """

    # 설정
    MAX_USAGE_PER_ASSET = 3       # 동일 에셋 최대 사용 횟수
    RECENT_EXCLUSION_COUNT = 10   # 최근 N개 영상에서 사용된 에셋 제외
    MIN_CANDIDATES = 3            # 최소 후보 수 (이하면 제한 완화)

    def __init__(self, asset_base_dir: Path = None, history_path: Path = None):
        """
        Args:
            asset_base_dir: 에셋 베이스 디렉토리 (Path)
            history_path: 에셋 히스토리 JSON 경로 (S2-A3)
        """
        self.asset_base_dir = asset_base_dir

        # 사용 통계
        self._usage_stats: Dict[str, AssetUsageStats] = {}

        # 최근 사용 기록 (deque로 FIFO 유지)
        self._recent_videos: deque = deque(maxlen=self.RECENT_EXCLUSION_COUNT)
        self._recent_images: deque = deque(maxlen=self.RECENT_EXCLUSION_COUNT)
        self._recent_bgm: deque = deque(maxlen=self.RECENT_EXCLUSION_COUNT)

        # 현재 배치 시퀀스
        self._batch_seq = 0

        # 스레드 안전
        self._lock = threading.Lock()

        # S2-A3: 히스토리 영속 저장
        if history_path:
            self._history_path = history_path
        elif asset_base_dir is not None:
            self._history_path = asset_base_dir.parent / "data" / "asset_history.json"
        else:
            try:
                from path_resolver import get_paths
                self._history_path = get_paths().data_dir / "asset_history.json"
            except (ImportError, Exception):
                self._history_path = Path("D:/mabiz/data/asset_history.json")
        self._load_history()

        logger.info("[AssetDiversityManager] 초기화 완료")

    # ─── S2-A3: 히스토리 영속 저장 ──────────────────────────
    def _load_history(self) -> None:
        """에셋 히스토리 파일에서 로드 (S2-A3)"""
        if not self._history_path.exists():
            logger.info(f"[AssetDiversity] 히스토리 파일 없음, 신규: {self._history_path}")
            return

        try:
            with open(self._history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 사용 통계 복원
            for key, stats in data.get("usage_stats", {}).items():
                self._usage_stats[key] = AssetUsageStats(**stats)

            # 최근 사용 기록 복원
            for path in data.get("recent_videos", []):
                self._recent_videos.append(path)
            for path in data.get("recent_images", []):
                self._recent_images.append(path)
            for path in data.get("recent_bgm", []):
                self._recent_bgm.append(path)

            self._batch_seq = data.get("batch_seq", 0)
            logger.info(
                f"[AssetDiversity] 히스토리 로드: "
                f"{len(self._usage_stats)}개 통계, "
                f"batch_seq={self._batch_seq}"
            )
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"[AssetDiversity] 히스토리 로드 실패, 초기화: {e}")

    def _save_history(self) -> None:
        """에셋 히스토리 파일로 저장 (S2-A3)"""
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "usage_stats": {k: asdict(v) for k, v in self._usage_stats.items()},
            "recent_videos": list(self._recent_videos),
            "recent_images": list(self._recent_images),
            "recent_bgm": list(self._recent_bgm),
            "batch_seq": self._batch_seq,
            "updated_at": datetime.now().isoformat(),
        }

        try:
            with open(self._history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning(f"[AssetDiversity] 히스토리 저장 실패: {e}")
    # ──────────────────────────────────────────────────────

    def select_video(self, keyword: str, category: str = "",
                     exclude: List[str] = None) -> Optional[str]:
        """비디오 에셋 선택 (다양성 보장)"""
        return self._select_asset(
            keyword, "video", category,
            exclude, self._recent_videos
        )

    def select_image(self, keyword: str, category: str = "",
                     exclude: List[str] = None) -> Optional[str]:
        """이미지 에셋 선택 (다양성 보장)"""
        return self._select_asset(
            keyword, "image", category,
            exclude, self._recent_images
        )

    def select_bgm(self, theme: str = "", persona: str = "",
                   mood: str = "") -> Optional[str]:
        """BGM 선택 (테마/페르소나 기반)"""
        keyword = f"{theme} {persona} {mood}".strip()
        return self._select_asset(
            keyword, "bgm", "",
            None, self._recent_bgm
        )

    def _select_asset(self, keyword: str, asset_type: str,
                      category: str, exclude: Optional[List[str]],
                      recent_deque: deque) -> Optional[str]:
        """에셋 선택 (공통 로직)"""
        with self._lock:
            # 1. 후보 검색
            candidates = self._search_candidates(keyword, asset_type, category)

            if not candidates:
                logger.warning(f"  [{asset_type}] 후보 없음: {keyword}, {category}")
                return self._fallback(asset_type)

            # 2. 필터링
            filtered = self._filter_candidates(
                candidates,
                exclude_paths=exclude,
                recent_deque=recent_deque
            )

            # 3. 후보가 너무 적으면 제한 완화
            if len(filtered) < self.MIN_CANDIDATES:
                logger.debug(f"  [{asset_type}] 후보 부족 ({len(filtered)}), 제한 완화")
                filtered = self._filter_candidates(
                    candidates,
                    exclude_paths=exclude,
                    recent_deque=deque()  # 최근 사용 제한 해제
                )

            if not filtered:
                filtered = candidates

            # 4. 가중치 기반 선택
            selected = self._weighted_select(filtered)

            if selected:
                # 5. 사용 기록
                self._record_usage(selected, asset_type, category)

            return selected

    def _search_candidates(self, keyword: str, asset_type: str,
                           category: str) -> List[str]:
        """후보 에셋 검색"""
        if self.asset_base_dir is None:
            return []

        try:
            if asset_type == "video":
                exts = list(self.asset_base_dir.rglob("*.mp4"))
            elif asset_type == "image":
                exts = list(self.asset_base_dir.rglob("*.jpg")) + \
                       list(self.asset_base_dir.rglob("*.png"))
            elif asset_type == "bgm":
                exts = list(self.asset_base_dir.rglob("*.mp3"))
            else:
                exts = []

            # 키워드 필터링
            if keyword:
                kw_lower = keyword.lower()
                matched = [str(f) for f in exts if kw_lower in f.stem.lower()]
                if matched:
                    return matched

            return [str(f) for f in exts]

        except OSError as e:
            logger.warning(f"  [{asset_type}] 검색 실패: {e}")
            return []

    def _filter_candidates(self, candidates: List[str],
                           exclude_paths: Optional[List[str]],
                           recent_deque: deque) -> List[str]:
        """후보 필터링"""
        filtered = []
        exclude_set = set(exclude_paths or [])
        recent_set = set(recent_deque)

        for path in candidates:
            # 명시적 제외
            if path in exclude_set:
                continue

            # 최근 사용 제외
            if path in recent_set:
                continue

            # 최대 사용 횟수 초과 제외
            stats = self._usage_stats.get(path)
            if stats and stats.count >= self.MAX_USAGE_PER_ASSET:
                continue

            filtered.append(path)

        return filtered

    def _weighted_select(self, candidates: List[str]) -> Optional[str]:
        """가중치 기반 랜덤 선택 (덜 사용된 에셋에 높은 가중치)"""
        if not candidates:
            return None

        weights = []
        for path in candidates:
            stats = self._usage_stats.get(path)
            count = stats.count if stats else 0
            # 가중치: 사용 횟수가 적을수록 높음
            weight = 1.0 / (count + 1)
            weights.append(weight)

        selected = random.choices(candidates, weights=weights, k=1)
        return selected[0]

    def _record_usage(self, path: str, asset_type: str, category: str):
        """에셋 사용 기록"""
        key = str(path)

        # 통계 업데이트
        if key not in self._usage_stats:
            self._usage_stats[key] = AssetUsageStats(path=key, category=category)

        self._usage_stats[key].count += 1
        self._usage_stats[key].last_used = datetime.now().isoformat()

        # 최근 사용 큐에 추가
        if asset_type == "video":
            self._recent_videos.append(key)
        elif asset_type == "image":
            self._recent_images.append(key)
        elif asset_type == "bgm":
            self._recent_bgm.append(key)

        # S2-A3: 히스토리 영속 저장
        self._save_history()

        logger.debug(f"  [{asset_type}] 사용 기록: {Path(path).name} (총 {self._usage_stats[key].count}회)")

    def _fallback(self, asset_type: str) -> Optional[str]:
        """폴백: 전체 에셋에서 랜덤 선택"""
        if self.asset_base_dir is None:
            return None

        try:
            if asset_type == "video":
                files = list(self.asset_base_dir.rglob("*.mp4"))
            elif asset_type == "image":
                files = list(self.asset_base_dir.rglob("*.jpg"))
            elif asset_type == "bgm":
                files = list(self.asset_base_dir.rglob("*.mp3"))
            else:
                files = []

            if files:
                return str(random.choice(files))
        except OSError as e:
            logger.warning(f"  [{asset_type}] 폴백 실패: {e}")

        return None

    def advance_batch(self):
        """배치 시퀀스 증가 (영상 1개 완료 시 호출)"""
        with self._lock:
            self._batch_seq += 1

    def reset_session(self):
        """새 배치 시작 시 초기화"""
        with self._lock:
            self._usage_stats.clear()
            self._recent_videos.clear()
            self._recent_images.clear()
            self._recent_bgm.clear()
            self._batch_seq = 0
            self._save_history()
            logger.info("[AssetDiversityManager] 세션 초기화 완료")

    def get_report(self) -> Dict:
        """사용 통계 리포트"""
        with self._lock:
            # 사용 빈도별 정렬
            sorted_stats = sorted(
                self._usage_stats.items(),
                key=lambda x: x[1].count,
                reverse=True
            )

            top_used = [
                {"path": s.path, "count": s.count}
                for _, s in sorted_stats[:10]
            ]

            total_assets = len(self._usage_stats)
            total_uses = sum(s.count for s in self._usage_stats.values())

            return {
                "total_assets": total_assets,
                "total_uses": total_uses,
                "avg_uses": round(total_uses / total_assets, 1) if total_assets else 0,
                "top_used": top_used,
                "batch_seq": self._batch_seq,
            }


# ──────────────────────────────────────────────────────────
# Hook 비디오 다양성 관리 (특별 처리)
# ──────────────────────────────────────────────────────────

class HookVideoDiversityManager:
    """
    Hook 비디오 다양성 관리

    Hook 영상은 첫 3초로 가장 중요하므로 특별 관리
    - 최소 5개 이상의 Hook 영상 풀
    - 같은 Hook 30% 이하로 제한
    - 순환 사용으로 균등 분배
    """

    def __init__(self, hook_video_dir: Path = None):
        if hook_video_dir is None:
            try:
                from path_resolver import get_paths
                hook_video_dir = get_paths().hook_videos_dir
            except (ImportError, Exception):
                hook_video_dir = Path("D:/AntiGravity/Assets/Hook/videos")
        self.hook_dir = hook_video_dir
        self._pool: List[Path] = []
        self._usage_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

        self._load_pool()

    def _load_pool(self):
        """Hook 영상 풀 로드"""
        extensions = ('.mp4', '.mov', '.avi', '.webm')

        if self.hook_dir.exists():
            self._pool = [
                f for f in self.hook_dir.iterdir()
                if f.suffix.lower() in extensions
            ]

        logger.info(f"[HookDiversity] 풀 로드: {len(self._pool)}개")

    def select_hook(self, batch_size: int = 10) -> Optional[Path]:
        """Hook 비디오 선택"""
        if not self._pool:
            logger.warning("[HookDiversity] 풀이 비어있음")
            return None

        with self._lock:
            max_uses = max(1, batch_size // 3)  # 30% 제한

            # 사용 가능한 Hook 필터링
            available = [
                h for h in self._pool
                if self._usage_counts.get(str(h), 0) < max_uses
            ]

            if not available:
                # 모두 제한 초과 시, 가장 적게 사용된 것 선택
                available = self._pool
                logger.debug("[HookDiversity] 모든 Hook 사용량 초과, 제한 완화")

            # 가중치 기반 선택
            weights = [
                1.0 / (self._usage_counts.get(str(h), 0) + 1)
                for h in available
            ]

            selected = random.choices(available, weights=weights, k=1)[0]

            # 사용 기록
            self._usage_counts[str(selected)] = self._usage_counts.get(str(selected), 0) + 1

            logger.info(f"[HookDiversity] 선택: {selected.name}")
            return selected

    def reset_batch(self):
        """배치 시작 시 초기화"""
        with self._lock:
            self._usage_counts.clear()

    def get_stats(self) -> Dict:
        """통계"""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "usage_counts": dict(self._usage_counts),
            }


# ──────────────────────────────────────────────────────────
# 테스트
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 매니저 테스트
    manager = AssetDiversityManager()

    # Hook 테스트
    hook_mgr = HookVideoDiversityManager()
    print(f"Hook 통계: {hook_mgr.get_stats()}")

    # 시뮬레이션: 10개 선택
    for i in range(10):
        hook = hook_mgr.select_hook()
        print(f"  Hook #{i+1}: {hook.name if hook else 'None'}")

    print(f"최종 Hook 통계: {hook_mgr.get_stats()}")
