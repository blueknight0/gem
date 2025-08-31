@echo off
chcp 65001 >nul
echo ============================================
echo     DJS Development Server
echo ============================================
echo.

REM Python 설치 확인
set PYTHON_FOUND=0

REM python 명령어 확인
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :dev_python_found
)

REM python3 명령어 확인
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=1
    goto :dev_python_found
)

REM py 명령어 확인 (Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :dev_python_found
)

if %PYTHON_FOUND% equ 0 (
    echo Python을 찾을 수 없습니다!
    echo setup.bat를 먼저 실행해서 환경을 설정해주세요.
    pause
    exit /b 1
)

:dev_python_found
REM 가상환경 확인 및 활성화
if exist venv (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo 가상환경이 존재하지 않습니다. setup.bat를 먼저 실행해주세요.
    pause
    exit /b 1
)

REM 환경 변수 설정
set PYTHONPATH=%CD%

REM 개발 모드로 FastAPI 서버 시작
echo FastAPI 개발 서버를 시작합니다...
echo 서버 주소: http://localhost:8000
echo API 문서: http://localhost:8000/docs
echo 자동 재시작: 코드 변경시 자동으로 서버 재시작
echo.

REM 로그 레벨 설정
set PYTHONPATH=%CD%
set UVICORN_LOG_LEVEL=info

%PYTHON_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause
