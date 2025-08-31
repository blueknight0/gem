#!/usr/bin/env python3
"""API 파일 import 테스트"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(".")


def test_extractor_import():
    """extractor.py import 테스트"""
    try:
        from backend.api.extractor import router

        print("✅ extractor.py import 성공")
        return True
    except Exception as e:
        print(f"❌ extractor.py import 실패: {e}")
        return False


def test_search_import():
    """search.py import 테스트"""
    try:
        from backend.api.search import router

        print("✅ search.py import 성공")
        return True
    except Exception as e:
        print(f"❌ search.py import 실패: {e}")
        return False


def test_embedding_import():
    """embedding.py import 테스트"""
    try:
        from backend.api.embedding import router

        print("✅ embedding.py import 성공")
        return True
    except Exception as e:
        print(f"❌ embedding.py import 실패: {e}")
        return False


if __name__ == "__main__":
    print("API 파일 import 테스트")
    print("=" * 30)

    tests = [test_extractor_import, test_search_import, test_embedding_import]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print(f"\n결과: {passed}/{len(tests)} 개 파일 import 성공")
    if passed == len(tests):
        print("🎉 모든 API 파일이 정상적으로 import됩니다!")
    else:
        print("⚠️ 일부 파일에서 import 오류가 있습니다.")
