#!/usr/bin/env python3
"""간단한 데이터베이스 초기화 스크립트"""

import sys
import os

sys.path.append(".")

try:
    from backend.core.database import create_tables

    create_tables()
    print("✅ 데이터베이스 테이블 생성 완료")
except Exception as e:
    print(f"❌ 데이터베이스 생성 실패: {e}")
    sys.exit(1)
