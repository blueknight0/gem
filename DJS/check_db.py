#!/usr/bin/env python3
"""데이터베이스 확인 스크립트"""

import os
import sqlite3
from pathlib import Path


def check_database():
    """데이터베이스 파일과 테이블 확인"""
    db_path = Path("./data/djs.db")

    if not db_path.exists():
        print("❌ 데이터베이스 파일이 존재하지 않습니다.")
        return False

    print(f"✅ 데이터베이스 파일 발견: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"📋 발견된 테이블: {len(tables)}개")
        for table in tables:
            print(f"  - {table[0]}")

        # 시스템 설정 확인
        cursor.execute("SELECT COUNT(*) FROM system_config")
        config_count = cursor.fetchone()[0]
        print(f"🔧 시스템 설정: {config_count}개")

        # 관계 유형 확인
        cursor.execute("SELECT COUNT(*) FROM relation_types")
        relation_count = cursor.fetchone()[0]
        print(f"🔗 관계 유형: {relation_count}개")

        conn.close()
        print("✅ 데이터베이스 확인 완료!")
        return True

    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")
        return False


if __name__ == "__main__":
    print("🎯 DJS 데이터베이스 확인")
    print("=" * 40)
    check_database()
