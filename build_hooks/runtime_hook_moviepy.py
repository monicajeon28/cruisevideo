# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook - MoviePy FFmpeg Path Setup

EXE 모드에서 동봉된 FFmpeg 바이너리를 moviepy/imageio에 알려줍니다.
이 파일은 PyInstaller spec의 runtime_hooks에 등록됩니다.
"""

import os
import sys

if getattr(sys, 'frozen', False):
    # EXE 번들 모드
    exe_dir = os.path.dirname(sys.executable)
    tools_dir = os.path.join(exe_dir, 'tools')

    # FFmpeg 경로 설정
    ffmpeg_exe = os.path.join(tools_dir, 'ffmpeg.exe')
    ffprobe_exe = os.path.join(tools_dir, 'ffprobe.exe')

    if os.path.exists(ffmpeg_exe):
        # imageio-ffmpeg용 (moviepy가 내부적으로 사용)
        os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_exe

        # PATH에 tools/ 추가 (subprocess.run(['ffmpeg', ...]) 대응)
        current_path = os.environ.get('PATH', '')
        if tools_dir not in current_path:
            os.environ['PATH'] = tools_dir + os.pathsep + current_path

    # Windows 콘솔 인코딩 (한글 깨짐 방지)
    if sys.platform == 'win32':
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except (AttributeError, OSError):
            pass
