# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook - PathResolver Initialization

EXE 모드에서 프로젝트 루트와 에셋 경로를 초기화합니다.
이 파일은 PyInstaller spec의 runtime_hooks에 등록됩니다.
"""

import os
import sys

if getattr(sys, 'frozen', False):
    # EXE 번들 모드: 실행 파일 디렉토리를 프로젝트 루트로 설정
    exe_dir = os.path.dirname(sys.executable)

    # sys.path에 EXE 디렉토리 추가 (모듈 import 지원)
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

    # .env 파일 로드 (EXE 디렉토리에서)
    env_path = os.path.join(exe_dir, '.env')
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            # dotenv 미번들 시 수동 파싱
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
