#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 폰트 테스트 스크립트
matplotlib에서 한글이 제대로 표시되는지 확인합니다.
"""

import matplotlib

matplotlib.use("Agg")  # GUI 없이 이미지만 생성
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import os
import warnings


def test_korean_fonts():
    """한글 폰트 테스트"""
    print("🔍 한글 폰트 테스트 시작...")

    # matplotlib 폰트 캐시 새로고침
    try:
        fm._rebuild()
        print("   ✅ matplotlib 폰트 캐시 새로고침 완료")
    except:
        print("   ⚠️ matplotlib 폰트 캐시 새로고침 실패")

    # 시스템 정보
    print(f"   🖥️ 운영체제: {platform.system()} {platform.release()}")

    # 사용 가능한 한글 폰트 찾기
    available_fonts = {}
    korean_fonts_found = []

    for font in fm.fontManager.ttflist:
        available_fonts[font.name] = font.fname
        # 한글 폰트 이름으로 추정되는 것들 수집
        if any(
            keyword in font.name.lower()
            for keyword in [
                "malgun",
                "dotum",
                "batang",
                "gulim",
                "nanum",
                "맑은",
                "돋움",
                "바탕",
                "굴림",
                "나눔",
            ]
        ):
            korean_fonts_found.append(font.name)

    print(f"   📊 전체 시스템 폰트: {len(available_fonts)}개")
    print(f"   🇰🇷 감지된 한글 폰트: {len(korean_fonts_found)}개")

    if korean_fonts_found:
        for font in korean_fonts_found:
            print(f"      - {font}")

    # 우선순위 한글 폰트 테스트
    test_fonts = [
        "Malgun Gothic",
        "맑은 고딕",
        "Microsoft YaHei",
        "NanumGothic",
        "나눔고딕",
        "Dotum",
        "돋움",
        "Gulim",
        "굴림",
        "Batang",
        "바탕",
        "Arial Unicode MS",
    ]

    working_fonts = []

    for font_name in test_fonts:
        if font_name in available_fonts:
            try:
                # 폰트 설정
                plt.rcParams["font.family"] = font_name

                # 한글 텍스트 테스트
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.text(
                    0.5, 0.7, "한글 폰트 테스트", fontsize=20, ha="center", va="center"
                )
                ax.text(
                    0.5,
                    0.5,
                    f"폰트: {font_name}",
                    fontsize=14,
                    ha="center",
                    va="center",
                )
                ax.text(
                    0.5,
                    0.3,
                    "가나다라마바사 아자차카타파하",
                    fontsize=12,
                    ha="center",
                    va="center",
                )
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_title("Korean Font Test", fontsize=16)

                # 파일로 저장
                output_file = f"font_test_{font_name.replace(' ', '_')}.png"
                plt.savefig(output_file, dpi=150, bbox_inches="tight")
                plt.close()

                working_fonts.append((font_name, output_file))
                print(f"   ✅ {font_name}: 테스트 성공 -> {output_file}")

            except Exception as e:
                plt.close()
                print(f"   ❌ {font_name}: 테스트 실패 ({e})")

    if not working_fonts:
        print("   ⚠️ 작동하는 한글 폰트가 없습니다. 영어로 대체 테스트를 진행합니다.")

        # 영어 폰트로 대체 테스트
        plt.rcParams["font.family"] = ["DejaVu Sans", "Arial", "sans-serif"]

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.7, "English Font Test", fontsize=20, ha="center", va="center")
        ax.text(
            0.5,
            0.5,
            "Korean fonts not available",
            fontsize=14,
            ha="center",
            va="center",
        )
        ax.text(
            0.5,
            0.3,
            "Using English labels instead",
            fontsize=12,
            ha="center",
            va="center",
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title("Font Test - English Fallback", fontsize=16)

        output_file = "font_test_english_fallback.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"   ✅ 영어 대체 폰트 테스트 완료 -> {output_file}")
        return None

    # 가장 적합한 폰트 추천
    recommended_font = working_fonts[0][0]
    print(f"\n🎯 추천 한글 폰트: {recommended_font}")
    print(f"   파일 경로: {available_fonts[recommended_font]}")

    return recommended_font


if __name__ == "__main__":
    try:
        warnings.filterwarnings("ignore")
        recommended = test_korean_fonts()

        if recommended:
            print(f"\n✅ 한글 폰트 테스트 완료! '{recommended}' 폰트를 사용하세요.")
        else:
            print(f"\n⚠️ 한글 폰트를 찾을 수 없습니다. 영어 레이블을 사용하세요.")

    except Exception as e:
        print(f"\n❌ 폰트 테스트 중 오류 발생: {e}")
