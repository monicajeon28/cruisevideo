# -*- mode: python ; coding: utf-8 -*-
"""
CruiseDot Video Pipeline - PyInstaller Spec (onedir mode)

Usage:
    pyinstaller cruisedot.spec

Output:
    dist/cruisedot/
        cruisedot.exe          <- 메인 실행 파일
        _internal/             <- 런타임 라이브러리
        config/                <- 설정 파일 (사용자 복사)
        tools/                 <- FFmpeg (사용자 배치)
        .env                   <- API 키 (사용자 작성)

Prerequisites:
    pip install pyinstaller
    requirements.txt 패키지 설치 완료
"""

import os
from pathlib import Path

block_cipher = None

# 프로젝트 루트
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPECPATH))

# ============================================================================
# 1. Analysis - 모듈 수집
# ============================================================================
a = Analysis(
    ['generate.py'],  # 진입점

    pathex=[PROJECT_ROOT],

    binaries=[],  # FFmpeg는 사용자가 tools/ 폴더에 배치

    # 번들에 포함할 데이터 파일
    datas=[
        # config 디렉토리
        ('config', 'config'),
        # path_resolver (핵심 모듈)
        ('path_resolver.py', '.'),
        # .env.example (사용자 가이드용)
        ('.env.example', '.'),
    ],

    # PyInstaller가 자동 감지 못하는 import
    hiddenimports=[
        # engines 패키지 전체
        'engines',
        'engines.__init__',
        'engines.comprehensive_script_generator',
        'engines.script_quality_validator',
        'engines.segment_enhancer',
        'engines.script_metadata_generator',
        'engines.sgrade_constants',
        'engines.ffmpeg_pipeline',
        'engines.ffmpeg_image_overlay_composer',
        'engines.subtitle_image_renderer',
        'engines.supertone_tts',
        'engines.supertone_emotion_mapper',
        'engines.bgm_matcher',
        'engines.color_correction',
        'engines.hook_generator',
        'engines.timeline_validator',
        'engines.s_grade_validator',
        'engines.script_validation_orchestrator',
        'engines.hook_structure_validator',
        'engines.emotion_curve_validator',
        'engines.pop_message_validator',
        'engines.cta_validator',
        'engines.cta_optimizer',
        'engines.rehook_injector',
        'engines.viral_score_calculator',
        'engines.pexels_video_fetcher',
        'engines.anti_abuse_video_editor',
        'engines.asset_diversity_manager',
        'engines.gemini_script_writer',
        # engines.keyword_extraction 서브패키지
        'engines.keyword_extraction',
        'engines.keyword_extraction.__init__',
        'engines.keyword_extraction.intelligent_keyword_extractor',
        'engines.keyword_extraction.context_analyzer',
        # video_pipeline 패키지
        'video_pipeline',
        'video_pipeline.__init__',
        'video_pipeline.config',
        'video_pipeline.gpu_detector',
        # pipeline_render 패키지
        'pipeline_render',
        'pipeline_render.__init__',
        'pipeline_render.audio_mixer',
        'pipeline_render.visual_loader',
        'pipeline_render.video_composer',
        # pipeline_effects 패키지
        'pipeline_effects',
        'pipeline_effects.__init__',
        'pipeline_effects.visual_effects',
        # src 패키지
        'src',
        'src.__init__',
        'src.utils',
        'src.utils.asset_matcher',
        # config 패키지 (Python 모듈)
        'config',
        'config.__init__',
        'config.api_config',
        'config.config_validator',
        'config.error_messages',
        'config.path_config',
        'config.pop_message_loader',
        'config.settings',
        'config.validate_config_v3',
        'config.validate_pop_messages',
        'config.validate_v3_simple',
        # cli 패키지 전체
        'cli',
        'cli.__init__',
        'cli.auto_mode',
        'cli.config_loader',
        'cli.product_loader',
        'cli.generation_log',
        'cli.batch_renderer',
        'cli.batch_quality_gate',
        'cli.weekly_report',
        # upload_package 패키지
        'upload_package',
        'upload_package.__init__',
        'upload_package.generator',
        # 파이프라인 메인
        'generate_video_55sec_pipeline',
        'path_resolver',
        # 런타임 의존성
        'dotenv',
        'yaml',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'numpy',
        'imageio',
        'imageio_ffmpeg',
        'tqdm',
        'requests',
        'google.genai',
        'google.genai.types',
        'moviepy',
        'moviepy.editor',
        'moviepy.video.fx',
        'moviepy.video.fx.all',
    ],

    hookspath=[],

    hooksconfig={},

    # PyInstaller runtime hooks (EXE 시작 시 실행)
    runtime_hooks=[
        'build_hooks/runtime_hook_paths.py',
        'build_hooks/runtime_hook_moviepy.py',
    ],

    # 제외할 모듈 (EXE 크기 최소화)
    excludes=[
        'scipy',
        'matplotlib',
        'pandas',
        'sklearn',
        'torch',
        'tensorflow',
        'cv2',
        'tkinter',
        'unittest',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
    ],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# 2. PYZ - 바이트코드 압축
# ============================================================================
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================================
# 3. EXE - 실행 파일 생성
# ============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # onedir 모드
    name='cruisedot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX 압축 비활성화 (안정성 우선)
    console=True,  # 콘솔 앱 (로그 출력)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일 (나중에 추가 가능)
)

# ============================================================================
# 4. COLLECT - onedir 모드 디렉토리 수집
# ============================================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='cruisedot',
)
