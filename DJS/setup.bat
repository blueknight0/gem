@echo off
chcp 65001 >nul
echo ============================================
echo       DJS System Setup Script
echo ============================================
echo.

REM Python 설치 확인 (여러 가지 방법으로 시도)
set PYTHON_FOUND=0

REM 1. python 명령어 확인
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=1
    goto :python_found
)

REM 2. python3 명령어 확인
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=1
    goto :python_found
)

REM 3. py 명령어 확인 (Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=1
    goto :python_found
)

REM 4. 일반적인 설치 경로 확인
if exist "C:\Python*\python.exe" (
    for /d %%i in ("C:\Python*") do (
        set PYTHON_CMD="%%i\python.exe"
        set PYTHON_FOUND=1
        goto :python_found
    )
)

REM 5. Program Files 경로 확인
if exist "C:\Program Files\Python*\python.exe" (
    for /d %%i in ("C:\Program Files\Python*") do (
        set PYTHON_CMD="%%i\python.exe"
        set PYTHON_FOUND=1
        goto :python_found
    )
)

REM 6. Program Files (x86) 경로 확인
if exist "C:\Program Files (x86)\Python*\python.exe" (
    for /d %%i in ("C:\Program Files (x86)\Python*") do (
        set PYTHON_CMD="%%i\python.exe"
        set PYTHON_FOUND=1
        goto :python_found
    )
)

REM 7. 사용자 경로 확인
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python*\python.exe" (
    for /d %%i in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
        set PYTHON_CMD="%%i\python.exe"
        set PYTHON_FOUND=1
        goto :python_found
    )
)

if %PYTHON_FOUND% equ 0 (
    echo Python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다!
    echo.
    echo 해결 방법:
    echo 1. Python 공식 사이트에서 재설치: https://www.python.org/downloads/
    echo    - 설치 시 "Add Python to PATH" 옵션 반드시 선택
    echo.
    echo 2. 이미 설치된 경우:
    echo    - 시스템 환경변수 PATH에 Python 경로 추가
    echo    - 또는 명령 프롬프트에서 python이 실행되는지 확인
    echo.
    echo 3. Python 버전 확인: python --version
    pause
    exit /b 1
)

:python_found
echo Python이 발견되었습니다!
echo Python 버전 확인 중...
%PYTHON_CMD% --version

REM pip 업그레이드
echo.
echo pip 업그레이드 중...
%PYTHON_CMD% -m pip install --upgrade pip

REM 가상환경 생성
if not exist venv (
    echo.
    echo 가상환경 생성 중...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo 가상환경 생성 실패!
        pause
        exit /b 1
    )
) else (
    echo 가상환경이 이미 존재합니다.
)

REM 가상환경 활성화
echo.
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

REM 의존성 설치
echo.
echo Python 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo 패키지 설치 실패!
    pause
    exit /b 1
)

REM data 디렉토리 생성
if not exist data (
    echo.
    echo 데이터 디렉토리 생성 중...
    mkdir data
    mkdir data\exports
)

REM 설정 파일 복사
if not exist config.yaml (
    if exist config.example.yaml (
        echo.
        echo 설정 파일 복사 중...
        copy config.example.yaml config.yaml
    )
)

echo.
echo ============================================
echo          설치 완료!
echo ============================================
echo.
echo 다음 단계를 따라주세요:
echo.
echo 1. config.yaml 파일을 열어서 API 키를 설정해주세요
echo    - gemini_api_key: Gemini API 키
echo    - naver_api_client_id: 네이버 검색 API Client ID
echo    - naver_api_client_secret: 네이버 검색 API Client Secret
echo.
echo 2. run_server.bat를 실행해서 서버를 시작하세요
echo.
echo 3. 웹 브라우저에서 http://localhost:8000 으로 접속
echo.

pause
