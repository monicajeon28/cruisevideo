@echo off
REM build_exe.bat - PyInstaller --onedir 빌드

echo [1/3] 가상환경 생성...
python -m venv venv_exe
call venv_exe\Scripts\activate

echo [2/3] 최소 의존성 설치...
pip install -r requirements_exe.txt

echo [3/3] PyInstaller 빌드...
pyinstaller ^
    --onedir ^
    --name CruiseVideoGenerator ^
    --hidden-import google.generativeai ^
    --hidden-import PIL ^
    --exclude-module pandas ^
    --exclude-module anthropic ^
    --exclude-module librosa ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    generate_video_55sec_pipeline.py

echo.
echo 빌드 완료: dist\CruiseVideoGenerator\
pause
