@echo off
chcp 65001 >nul
echo ============================================
echo    DJS - Data-based Junction Search System
echo ============================================
echo.

REM Python 설치 확인
set PYTHON_FOUND=0

REM python 명령어 확인
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :server_python_found
)

REM python3 명령어 확인
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=1
    goto :server_python_found
)

REM py 명령어 확인 (Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :server_python_found
)

if %PYTHON_FOUND% equ 0 (
    echo Python을 찾을 수 없습니다!
    echo setup.bat를 먼저 실행해서 환경을 설정해주세요.
    pause
    exit /b 1
)

:server_python_found
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

REM 데이터베이스 초기화 확인
if not exist data\djs.db (
    echo 데이터베이스가 존재하지 않습니다. 초기화 중...
    python backend\core\init_db.py
    if errorlevel 1 (
        echo 데이터베이스 초기화 실패!
        pause
        exit /b 1
    )
)

REM 설정 파일 확인
if not exist config.yaml (
    if exist config.example.yaml (
        echo config.yaml이 존재하지 않습니다. config.example.yaml을 복사합니다.
        copy config.example.yaml config.yaml
        echo.
        echo *** 중요: config.yaml 파일을 열어서 API 키를 설정해주세요 ***
        echo 1. gemini_api_key 설정
        echo 2. naver_api_client_id 및 naver_api_client_secret 설정
        echo.
        pause
    ) else (
        echo 설정 파일이 존재하지 않습니다!
        pause
        exit /b 1
    )
)

REM FastAPI 서버 시작
echo FastAPI 서버를 시작합니다...
echo 서버 주소: http://localhost:8000
echo API 문서: http://localhost:8000/docs
echo.

%PYTHON_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
