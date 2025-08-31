#!/usr/bin/env python3
"""
DJS 시스템 실행 스크립트
"""

import uvicorn
import sys
import os
from pathlib import Path


def main():
    """메인 실행 함수"""
    print("🎯 DJS (Data-based Junction Search) 시스템 시작")
    print("=" * 60)

    # 현재 디렉토리를 프로젝트 루트로 설정
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # 환경변수 설정 (필요시)
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./data/djs.db"

    try:
        print("🚀 FastAPI 서버 시작 중...")
        print("📍 서버 주소: http://localhost:8000")
        print("📖 API 문서: http://localhost:8000/docs")
        print("🔄 대안 문서: http://localhost:8000/redoc")
        print("🛑 종료: Ctrl+C")
        print("=" * 60)

        uvicorn.run(
            "backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )

    except KeyboardInterrupt:
        print("\n👋 DJS 시스템이 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
