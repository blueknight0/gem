@echo off
chcp 65001 >nul
echo ============================================
echo       DJS Database Initialization
echo ============================================
echo.

REM Python 설치 확인
set PYTHON_FOUND=0

REM python 명령어 확인
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :db_python_found
)

REM python3 명령어 확인
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=1
    goto :db_python_found
)

REM py 명령어 확인 (Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :db_python_found
)

if %PYTHON_FOUND% equ 0 (
    echo Python을 찾을 수 없습니다!
    echo setup.bat를 먼저 실행해서 환경을 설정해주세요.
    pause
    exit /b 1
)

:db_python_found
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

REM 데이터베이스 초기화
echo 데이터베이스 초기화 중...
echo - 설정 파일에서 API 키 로드 중...
%PYTHON_CMD% backend\core\init_db.py

if errorlevel 1 (
    echo 데이터베이스 초기화 실패!
    echo 오류 메시지를 확인해주세요.
    pause
    exit /b 1
)

echo.
echo 데이터베이스 초기화가 완료되었습니다!
echo.

REM 데이터베이스 상태 확인
echo 데이터베이스 파일 상태:
if exist data\djs.db (
    echo ✓ data\djs.db 파일이 생성되었습니다.
    dir data\djs.db
) else (
    echo ✗ 데이터베이스 파일이 생성되지 않았습니다.
)

echo.
pause
