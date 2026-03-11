#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PathResolver - EXE 배포 대응 경로 해결 모듈

PyInstaller EXE 환경과 개발 환경 모두에서 올바른 경로를 반환합니다.

경로 해결 우선순위:
  1. 환경변수 (CRUISEDOT_ASSETS_ROOT, CRUISEDOT_OUTPUT_ROOT 등)
  2. config/paths.yaml (프로젝트 루트 기준)
  3. EXE 실행 디렉토리 기준 상대 경로
  4. 개발 환경 기본값 (D:/AntiGravity/* 등)

Usage:
    from path_resolver import PathResolver

    paths = PathResolver()
    paths.assets_root       # -> Path("D:/AntiGravity/Assets") 또는 EXE 기준 경로
    paths.output_root       # -> Path("D:/AntiGravity/Output")
    paths.project_root      # -> Path("D:/mabiz") 또는 EXE 기준 경로
    paths.temp_dir          # -> Path("D:/mabiz/temp")
    paths.config_dir        # -> project_root / "config"
    paths.data_dir          # -> project_root / "data"

    # 세부 경로 (assets_root 기준)
    paths.sfx_dir           # -> assets_root / "SoundFX"
    paths.music_dir         # -> assets_root / "Music"
    paths.fonts_dir         # -> assets_root / "fonts"
    paths.image_dir         # -> assets_root / "Image"
    paths.footage_dir       # -> assets_root / "Footage"

Author: Claude Code (code-writer)
Created: 2026-03-10
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _is_frozen() -> bool:
    """PyInstaller EXE 환경인지 확인"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def _get_bundle_dir() -> Path:
    """PyInstaller 번들 내부 리소스 디렉토리 (sys._MEIPASS)"""
    if _is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _get_exe_dir() -> Path:
    """EXE 실행 파일이 위치한 디렉토리 (사용자가 배치한 위치)"""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _load_paths_yaml(project_root: Path) -> dict:
    """config/paths.yaml 로드 (없으면 빈 dict 반환)"""
    yaml_path = project_root / "config" / "paths.yaml"
    if not yaml_path.exists():
        return {}

    try:
        # PyYAML 없이도 동작하는 간이 파서
        # paths.yaml은 단순 key: "value" 구조만 사용
        result = {}
        with open(yaml_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value and not key.startswith('#'):
                        result[key] = value
        return result
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"[PathResolver] paths.yaml 로드 실패: {e}")
        return {}


class PathResolver:
    """EXE 배포 대응 경로 해결기 (싱글턴)

    인스턴스를 여러 번 생성해도 동일한 경로를 반환합니다.
    첫 초기화 시 경로를 확정하고 이후에는 캐시된 값을 사용합니다.
    """

    _instance: Optional['PathResolver'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._resolve_all()

    def _resolve_all(self):
        """모든 경로를 우선순위에 따라 해결"""
        # 1단계: 프로젝트 루트 결정
        self.project_root = self._resolve_project_root()

        # 2단계: paths.yaml 로드
        yaml_config = _load_paths_yaml(self.project_root)

        # 3단계: 핵심 경로 해결 (환경변수 > yaml > 기본값)
        self.assets_root = self._resolve_path(
            env_key='CRUISEDOT_ASSETS_ROOT',
            yaml_value=yaml_config.get('assets_root'),
            default_dev=Path("D:/AntiGravity/Assets"),
            default_exe=_get_exe_dir() / "Assets",
        )

        self.output_root = self._resolve_path(
            env_key='CRUISEDOT_OUTPUT_ROOT',
            yaml_value=yaml_config.get('output_root'),
            default_dev=Path("D:/AntiGravity/Output"),
            default_exe=_get_exe_dir() / "Output",
        )

        self.temp_dir = self._resolve_path(
            env_key='CRUISEDOT_TEMP_DIR',
            yaml_value=yaml_config.get('temp_dir'),
            default_dev=self.project_root / "temp",
            default_exe=_get_exe_dir() / "temp",
        )

        # 4단계: 파생 경로 (project_root 기준)
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.env_file = self.project_root / ".env"

        # 5단계: 에셋 세부 경로 (assets_root 기준)
        self.sfx_dir = self.assets_root / "SoundFX"
        self.music_dir = self.assets_root / "Music"
        self.music_backup_dir = self.assets_root.parent / "Assets_Backup" if _is_frozen() else Path(str(self.music_dir).replace("Music", "Music_Backup"))
        self.fonts_dir = self.assets_root / "fonts"
        self.image_dir = self.assets_root / "Image"
        self.footage_dir = self.assets_root / "Footage"
        self.hook_videos_dir = self.footage_dir / "Hook"
        self.narration_temp_dir = self.assets_root / "narration" / "temp"
        self.cutouts_manual_dir = self.assets_root / "누끼파일"

        # 6단계: 출력 세부 경로 (output_root 기준)
        self.final_videos_dir = self.output_root / "4_Final_Videos"
        self.raw_images_dir = self.output_root / "1_Raw_Images"
        self.face_swapped_dir = self.output_root / "2_Face_Swapped"
        self.ai_videos_dir = self.output_root / "3_Videos"
        self.cutouts_auto_dir = self.output_root / "Cutouts_Auto"
        self.logs_dir = self.output_root / "logs"

        # 7단계: 특수 경로
        self.intro_sfx_path = self.sfx_dir / "level-up-08-402152.mp3"
        self.logo_path = self.image_dir / "로고" / "크루즈닷로고투명.png"

        # 8단계: 시스템 폰트 경로 (Windows 전용, EXE에서도 동작)
        self.system_font_path = self._resolve_font_path(
            yaml_value=yaml_config.get('font_path')
        )

        logger.info(f"[PathResolver] project_root = {self.project_root}")
        logger.info(f"[PathResolver] assets_root  = {self.assets_root}")
        logger.info(f"[PathResolver] output_root  = {self.output_root}")
        logger.info(f"[PathResolver] frozen={_is_frozen()}")

    def _resolve_project_root(self) -> Path:
        """프로젝트 루트 디렉토리 결정

        우선순위:
        1. 환경변수 CRUISEDOT_PROJECT_ROOT
        2. EXE 환경이면 EXE 디렉토리
        3. 개발 환경이면 이 파일의 부모 디렉토리
        """
        env_val = os.environ.get('CRUISEDOT_PROJECT_ROOT')
        if env_val:
            return Path(env_val).resolve()

        if _is_frozen():
            return _get_exe_dir()

        return Path(__file__).resolve().parent

    def _resolve_path(
        self,
        env_key: str,
        yaml_value: Optional[str],
        default_dev: Path,
        default_exe: Path,
    ) -> Path:
        """단일 경로를 우선순위에 따라 해결

        1. 환경변수
        2. paths.yaml 값
        3. EXE면 default_exe, 아니면 default_dev
        """
        # 1. 환경변수
        env_val = os.environ.get(env_key)
        if env_val:
            resolved = Path(env_val).resolve()
            logger.debug(f"[PathResolver] {env_key} from env: {resolved}")
            return resolved

        # 2. paths.yaml
        if yaml_value:
            resolved = Path(yaml_value)
            if resolved.is_absolute():
                logger.debug(f"[PathResolver] {env_key} from yaml: {resolved}")
                return resolved
            # 상대 경로면 project_root 기준
            resolved = (self.project_root / resolved).resolve()
            logger.debug(f"[PathResolver] {env_key} from yaml (relative): {resolved}")
            return resolved

        # 3. 기본값
        if _is_frozen():
            logger.debug(f"[PathResolver] {env_key} default (exe): {default_exe}")
            return default_exe
        else:
            logger.debug(f"[PathResolver] {env_key} default (dev): {default_dev}")
            return default_dev

    def _resolve_font_path(self, yaml_value: Optional[str] = None) -> str:
        """시스템 폰트 경로 해결

        우선순위:
        1. paths.yaml font_path
        2. assets/fonts/ 내 폰트 파일
        3. Windows 시스템 폰트 (맑은 고딕 Bold)
        4. 기본 폰트 (fallback)
        """
        # 1. yaml
        if yaml_value:
            p = Path(yaml_value)
            if p.exists():
                return str(p)

        # 2. assets/fonts/ (디자인 폰트 우선 → 시스템 폰트)
        fonts_candidates = [
            self.fonts_dir / "BMDOHYEON_ttf.ttf",
            self.fonts_dir / "JalnanGothicTTF.ttf",
            self.fonts_dir / "GmarketSansTTFBold.ttf",
            self.fonts_dir / "malgunbd.ttf",
            self.fonts_dir / "NanumGothicBold.ttf",
        ]
        for fp in fonts_candidates:
            if fp.exists():
                return str(fp)

        # 3. Windows 시스템 폰트
        if sys.platform == 'win32':
            win_font = Path("C:/Windows/Fonts/malgunbd.ttf")
            if win_font.exists():
                return str(win_font)

        # 4. fallback
        logger.warning("[PathResolver] 맑은 고딕 Bold 폰트를 찾을 수 없습니다. 기본 폰트 사용.")
        return "C:/Windows/Fonts/malgunbd.ttf"

    def get_allowed_script_dirs(self):
        """Path Traversal 방어를 위한 허용 디렉토리 목록"""
        dirs = [self.project_root.resolve()]
        # assets_root와 output_root의 공통 부모를 포함
        assets_parent = self.assets_root.resolve().parent
        if assets_parent not in dirs:
            dirs.append(assets_parent)
        return dirs

    def ensure_dirs(self):
        """필수 디렉토리 생성 (최초 실행 시)"""
        for d in [
            self.temp_dir,
            self.final_videos_dir,
            self.logs_dir,
            self.data_dir,
            self.narration_temp_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def reset(cls):
        """싱글턴 인스턴스 초기화 (테스트용)"""
        cls._instance = None

    def __repr__(self):
        return (
            f"PathResolver(\n"
            f"  project_root={self.project_root},\n"
            f"  assets_root={self.assets_root},\n"
            f"  output_root={self.output_root},\n"
            f"  temp_dir={self.temp_dir},\n"
            f"  frozen={_is_frozen()}\n"
            f")"
        )


# 모듈 레벨 편의 함수 (자주 사용하는 경우)
def get_paths() -> PathResolver:
    """PathResolver 싱글턴 인스턴스 반환"""
    return PathResolver()


def resolve_korean_font(size: int = 48):
    """한글 디자인 폰트 로드 유틸리티 (SSOT)

    subtitle_image_renderer, video_composer, card_renderer 공통 사용.
    PathResolver의 system_font_path(디자인 폰트 포함)를 사용.

    Returns:
        PIL ImageFont 객체
    """
    from PIL import ImageFont
    try:
        font_path = get_paths().system_font_path
        return ImageFont.truetype(font_path, size)
    except (OSError, ValueError, Exception):
        return ImageFont.load_default()
