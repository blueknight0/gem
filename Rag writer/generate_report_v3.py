import sys
import subprocess
import os
import re
from datetime import datetime
import hashlib  # 플레이스홀더 생성을 위해 추가
from typing import TypedDict, List, Dict
import io
from contextlib import redirect_stdout, redirect_stderr

# 필수 라이브러리 확인 및 설치
required_packages = {
    "google.generativeai": "google-generativeai",
    "faiss": "faiss-cpu",
    "numpy": "numpy",
    "dotenv": "python-dotenv",
    "sklearn": "scikit-learn",
    "langgraph": "langgraph",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "pandas": "pandas",
    "PIL": "Pillow",
}

for lib, package in required_packages.items():
    try:
        __import__(lib.split(".")[0])
    except ImportError:
        print(f"{package} 라이브러리가 설치되어 있지 않습니다. 설치를 시작합니다.")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(
                f"오류: {package} 설치에 실패했습니다. 수동으로 설치해주세요: pip install {package}"
            )
            sys.exit(1)

import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import json
import numpy as np
import faiss
import google.generativeai
from google import genai
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from google.genai import types
from langgraph.graph import StateGraph, END
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm

import threading
import queue


# 콘솔 로그 수집을 위한 클래스
class ConsoleLogger:
    def __init__(self):
        self.logs = []
        self.current_node = None
        self.node_logs = {}
        self.start_time = None
        self.node_start_times = {}

    def start_logging(self, session_id):
        """로깅 세션 시작"""
        self.session_id = session_id
        self.start_time = datetime.now()
        self.logs = []
        self.node_logs = {}
        self.add_log("SYSTEM", f"=== 보고서 생성 세션 시작 (ID: {session_id}) ===")

    def set_current_node(self, node_name):
        """현재 실행 중인 노드 설정"""
        if self.current_node and self.current_node in self.node_start_times:
            # 이전 노드 종료 시간 기록
            duration = (
                datetime.now() - self.node_start_times[self.current_node]
            ).total_seconds()
            self.add_log(
                "SYSTEM",
                f"노드 '{self.current_node}' 완료 (소요시간: {duration:.2f}초)",
            )

        self.current_node = node_name
        self.node_start_times[node_name] = datetime.now()
        self.add_log("SYSTEM", f">>> 노드 '{node_name}' 시작")

    def add_log(self, level, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "node": self.current_node,
            "message": message,
        }
        self.logs.append(log_entry)

        # 노드별 로그 분류
        if self.current_node:
            if self.current_node not in self.node_logs:
                self.node_logs[self.current_node] = []
            self.node_logs[self.current_node].append(log_entry)

        # 콘솔에도 출력
        print(f"[{timestamp}] {level}: {message}")

    def save_logs(self, output_dir="."):
        """로그를 파일로 저장"""
        if not self.logs:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 전체 로그 저장
        full_log_path = os.path.join(output_dir, f"pipeline_log_{timestamp}.md")
        with open(full_log_path, "w", encoding="utf-8") as f:
            f.write(f"# 보고서 생성 파이프라인 로그\n\n")
            f.write(f"**세션 ID**: {self.session_id}\n")
            f.write(f"**시작 시간**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**종료 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"**총 소요 시간**: {(datetime.now() - self.start_time).total_seconds():.2f}초\n\n"
            )

            f.write("## 전체 실행 로그\n\n")
            for log in self.logs:
                node_info = f"[{log['node']}] " if log["node"] else ""
                f.write(
                    f"`{log['timestamp']}` **{log['level']}**: {node_info}{log['message']}\n\n"
                )

        # 노드별 로그 저장
        for node_name, node_logs in self.node_logs.items():
            node_log_path = os.path.join(
                output_dir, f"node_{node_name}_log_{timestamp}.md"
            )
            with open(node_log_path, "w", encoding="utf-8") as f:
                f.write(f"# 노드 '{node_name}' 실행 로그\n\n")
                f.write(f"**세션 ID**: {self.session_id}\n")
                if node_name in self.node_start_times:
                    start_time = self.node_start_times[node_name]
                    f.write(
                        f"**시작 시간**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                f.write(f"**로그 수**: {len(node_logs)}개\n\n")

                for log in node_logs:
                    f.write(
                        f"`{log['timestamp']}` **{log['level']}**: {log['message']}\n\n"
                    )

        self.add_log("SYSTEM", f"로그 파일 저장 완료: {full_log_path}")
        return full_log_path, [
            os.path.join(output_dir, f"node_{node}_log_{timestamp}.md")
            for node in self.node_logs.keys()
        ]


# 결과 시각화 클래스
class ReportAnalyzer:
    def __init__(self):
        # matplotlib 백엔드를 Agg로 설정 (GUI 없이 이미지만 생성)
        import matplotlib

        matplotlib.use("Agg")

        # seaborn 스타일을 먼저 설정 (이후 폰트 설정이 덮어쓰지 않도록)
        sns.set_style("whitegrid")

        # 한글 폰트 설정 (Windows 환경)
        self._setup_korean_font()
        # unicode_minus는 폰트 설정 후 다시 한번 확인해주는 것이 안전
        plt.rcParams["axes.unicode_minus"] = False

    def _setup_korean_font(self):
        """한글 폰트를 설정하고, 실패 시 영어로 대체합니다."""
        import platform
        import warnings

        if platform.system() != "Windows":
            print("⚠️ Windows 환경이 아니므로 영어 레이블로 대체합니다.")
            self._fallback_to_english()
            return

        font_name = "Malgun Gothic"
        try:
            # 전역 폰트 설정
            plt.rc("font", family=font_name)
            plt.rcParams["axes.unicode_minus"] = False
            print(f"✅ 한글 폰트 '{font_name}' 설정 완료.")
            self.use_english_labels = False
        except Exception as e:
            print(f"❌ '{font_name}' 폰트 설정 실패: {e}. 영어 레이블로 대체합니다.")
            self._fallback_to_english()

        # 경고 메시지 관리
        if not self.use_english_labels:
            warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    def _fallback_to_english(self):
        """영어 레이블로 폴백"""
        plt.rcParams["font.family"] = ["DejaVu Sans", "Arial", "sans-serif"]
        print("⚠️ 영어 레이블을 사용합니다.")
        self.use_english_labels = True

    def _verify_font_before_plotting(self):
        """시각화 생성 전 폰트 설정 재검증"""
        import matplotlib.font_manager as fm

        current_font = plt.rcParams["font.family"]
        print(f"📊 시각화 생성 전 폰트 검증: {current_font}")

        # 한글 폰트가 설정되어 있지만 실제로 사용 가능한지 재확인
        if not self.use_english_labels:
            try:
                # 간단한 한글 텍스트 렌더링 테스트
                fig, ax = plt.subplots(figsize=(1, 1))
                text = ax.text(0.5, 0.5, "테스트", fontsize=10)

                # 텍스트 렌더링 후 폰트 확인
                renderer = fig.canvas.get_renderer()
                if hasattr(text, "_get_layout"):
                    layout = text._get_layout(renderer)

                plt.close(fig)
                print("   ✅ 한글 폰트 검증 통과")

            except Exception as e:
                print(f"   ❌ 한글 폰트 검증 실패: {e}")
                print("   🔄 영어 레이블로 전환합니다.")
                self._fallback_to_english()
        else:
            print("   ℹ️ 영어 레이블 모드 사용 중")

    def create_visualization_dashboard(self, logger, final_state, output_dir="."):
        """종합 시각화 대시보드 생성"""
        try:
            # 시각화 생성 전 폰트 재검증
            self._verify_font_before_plotting()

            # 데이터 수집
            analytics_data = self._collect_analytics_data(logger, final_state)

            # 대시보드 생성
            fig = plt.figure(figsize=(20, 15))

            if self.use_english_labels:
                dashboard_title = "RAG Report Generation Pipeline Analysis Dashboard"
            else:
                dashboard_title = "RAG 리포트 생성 파이프라인 분석 대시보드"

            fig.suptitle(
                dashboard_title,
                fontsize=20,
                fontweight="bold",
            )

            # 1. 워크플로우 진행 상황 (2x3 그리드의 첫 번째)
            ax1 = plt.subplot(2, 3, 1)
            self._plot_workflow_progress(ax1, analytics_data)

            # 2. 작업별 소요시간 (2x3 그리드의 두 번째)
            ax2 = plt.subplot(2, 3, 2)
            self._plot_execution_times(ax2, analytics_data)

            # 3. 참고문헌 통계 (2x3 그리드의 세 번째)
            ax3 = plt.subplot(2, 3, 3)
            self._plot_reference_stats(ax3, analytics_data)

            # 4. 편집장 검토 결과 (2x3 그리드의 네 번째)
            ax4 = plt.subplot(2, 3, 4)
            self._plot_editorial_review(ax4, analytics_data)

            # 5. 보고서 품질 지표 (2x3 그리드의 다섯 번째)
            ax5 = plt.subplot(2, 3, 5)
            self._plot_quality_metrics(ax5, analytics_data)

            # 6. 로그 레벨 분포 (2x3 그리드의 여섯 번째)
            ax6 = plt.subplot(2, 3, 6)
            self._plot_log_distribution(ax6, analytics_data)

            plt.tight_layout()

            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_path = os.path.join(output_dir, f"dashboard_{timestamp}.png")
            plt.savefig(dashboard_path, dpi=300, bbox_inches="tight")

            # 개별 시각화도 저장
            self._save_individual_plots(analytics_data, output_dir, timestamp)

            print(f"📊 시각화 대시보드 저장 완료: {dashboard_path}")
            return dashboard_path

        except Exception as e:
            print(f"❌ 시각화 생성 중 오류: {e}")
            return None

    def _collect_analytics_data(self, logger, final_state):
        """분석용 데이터 수집"""
        data = {
            "total_duration": 0,
            "node_durations": {},
            "log_counts": {},
            "reference_stats": {},
            "editorial_reviews": [],
            "quality_metrics": {},
            "workflow_progress": [],
        }

        # 총 소요시간 계산
        if logger.start_time:
            data["total_duration"] = (
                datetime.now() - logger.start_time
            ).total_seconds()

        # 노드별 소요시간 계산
        for node_name, start_time in logger.node_start_times.items():
            # 각 노드의 완료 시간을 로그에서 찾기
            node_logs = logger.node_logs.get(node_name, [])
            if node_logs:
                # 마지막 로그 시간을 완료 시간으로 사용
                last_log = node_logs[-1]
                last_time = datetime.strptime(last_log["timestamp"], "%H:%M:%S")
                start_time_only = start_time.replace(
                    year=last_time.year, month=last_time.month, day=last_time.day
                )
                duration = (last_time - start_time_only).total_seconds()
                data["node_durations"][node_name] = max(duration, 0)

        # 로그 레벨별 카운트
        for log in logger.logs:
            level = log["level"]
            data["log_counts"][level] = data["log_counts"].get(level, 0) + 1

        # 참고문헌 통계 (final_state에서 추출)
        if final_state:
            final_report = final_state.get("final_report_with_refs", "")
            data["reference_stats"] = {
                "total_references": final_report.count("[^") if final_report else 0,
                "total_words": len(final_report.split()) if final_report else 0,
                "total_chars": len(final_report) if final_report else 0,
            }

            # 편집장 검토 결과
            review_history = final_state.get("review_history", [])
            for review in review_history:
                result = review.get("result", {})
                data["editorial_reviews"].append(
                    {
                        "attempt": review.get("attempt", 0),
                        "passed": result.get("review_passed", True),
                        "sections_to_improve": len(
                            result.get("sections_to_improve", [])
                        ),
                    }
                )

        # 워크플로우 진행상황
        workflow_nodes = [
            "generate_outline",
            "generate_draft",
            "editorial_review",
            "regenerate_sections",
            "final_formatting",
            "finalize_and_save",
        ]
        for i, node in enumerate(workflow_nodes):
            completed = node in logger.node_logs
            data["workflow_progress"].append(
                {
                    "node": node,
                    "step": i + 1,
                    "completed": completed,
                    "duration": data["node_durations"].get(node, 0),
                }
            )

        return data

    def _plot_workflow_progress(self, ax, data):
        """워크플로우 진행상황 시각화"""
        progress_data = data["workflow_progress"]
        nodes = [p["node"] for p in progress_data]
        completed = [p["completed"] for p in progress_data]

        # 노드 이름 한글화/영어화
        if self.use_english_labels:
            node_names = {
                "generate_outline": "Generate Outline",
                "generate_draft": "Generate Draft",
                "editorial_review": "Editorial Review",
                "regenerate_sections": "Regenerate Sections",
                "final_formatting": "Final Formatting",
                "finalize_and_save": "Finalize & Save",
            }
            xlabel = "Completion Status"
            title = "Workflow Progress"
            complete_label = "Done"
            waiting_label = "Waiting"
        else:
            node_names = {
                "generate_outline": "개요생성",
                "generate_draft": "초안생성",
                "editorial_review": "편집검토",
                "regenerate_sections": "섹션재작성",
                "final_formatting": "서식정리",
                "finalize_and_save": "최종저장",
            }
            xlabel = "완료 상태"
            title = "워크플로우 진행 상황"
            complete_label = "완료"
            waiting_label = "대기"

        display_nodes = [node_names.get(node, node) for node in nodes]
        colors = ["#4CAF50" if c else "#FFC107" for c in completed]

        bars = ax.barh(display_nodes, [1] * len(display_nodes), color=colors, alpha=0.8)
        ax.set_xlabel(xlabel)
        ax.set_title(title, fontweight="bold")
        ax.set_xlim(0, 1)

        # 완료/미완료 레이블 추가
        for i, (bar, comp) in enumerate(zip(bars, completed)):
            label = complete_label if comp else waiting_label
            ax.text(0.5, i, label, ha="center", va="center", fontweight="bold")

    def _plot_execution_times(self, ax, data):
        """작업별 소요시간 시각화"""
        node_durations = data["node_durations"]

        if self.use_english_labels:
            no_data_text = "No execution time data"
            title = "Execution Times by Task"
            ylabel = "Duration (seconds)"
            node_names = {
                "generate_outline": "Generate Outline",
                "generate_draft": "Generate Draft",
                "editorial_review": "Editorial Review",
                "regenerate_sections": "Regenerate Sections",
                "final_formatting": "Final Formatting",
                "finalize_and_save": "Finalize & Save",
            }
        else:
            no_data_text = "소요시간 데이터 없음"
            title = "작업별 소요시간"
            ylabel = "소요시간 (초)"
            node_names = {
                "generate_outline": "개요생성",
                "generate_draft": "초안생성",
                "editorial_review": "편집검토",
                "regenerate_sections": "섹션재작성",
                "final_formatting": "서식정리",
                "finalize_and_save": "최종저장",
            }

        if not node_durations:
            ax.text(
                0.5,
                0.5,
                no_data_text,
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title, fontweight="bold")
            return

        display_nodes = [node_names.get(node, node) for node in node_durations.keys()]
        times = list(node_durations.values())

        bars = ax.bar(display_nodes, times, color="#2196F3", alpha=0.8)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="bold")
        ax.tick_params(axis="x", rotation=45)

        # 시간 레이블 추가
        for bar, time in zip(bars, times):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{time:.1f}s",
                ha="center",
                va="bottom",
            )

    def _plot_reference_stats(self, ax, data):
        """참고문헌 통계 시각화"""
        ref_stats = data["reference_stats"]

        if self.use_english_labels:
            metrics = ["References", "Total Words", "Total Characters"]
            title = "Report Statistics"
            ylabel = "Quantity"
        else:
            metrics = ["참고문헌 수", "총 단어 수", "총 문자 수"]
            title = "보고서 통계"
            ylabel = "수량"

        values = [
            ref_stats.get("total_references", 0),
            ref_stats.get("total_words", 0) // 100,  # 100으로 나누어 스케일 조정
            ref_stats.get("total_chars", 0) // 1000,  # 1000으로 나누어 스케일 조정
        ]

        bars = ax.bar(
            metrics, values, color=["#FF9800", "#4CAF50", "#9C27B0"], alpha=0.8
        )
        ax.set_title(title, fontweight="bold")
        ax.set_ylabel(ylabel)

        # 값 레이블 추가
        for bar, value, original in zip(
            bars,
            values,
            [
                ref_stats.get("total_references", 0),
                ref_stats.get("total_words", 0),
                ref_stats.get("total_chars", 0),
            ],
        ):
            height = bar.get_height()
            if bar.get_x() == 0:  # 참고문헌 수
                label = f"{original}"
            elif bar.get_x() == bars[1].get_x():  # 단어 수
                label = f"{original:,}"
            else:  # 문자 수
                label = f"{original:,}"
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                label,
                ha="center",
                va="bottom",
            )

    def _plot_editorial_review(self, ax, data):
        """편집장 검토 결과 시각화"""
        reviews = data["editorial_reviews"]

        if self.use_english_labels:
            no_data_text = "No editorial review data"
            title = "Editorial Review Results"
            ylabel = "Review Result"
            attempt_prefix = "Attempt"
            pass_label = "Passed"
            fail_label = "Needs Improvement"
        else:
            no_data_text = "편집장 검토 데이터 없음"
            title = "편집장 검토 결과"
            ylabel = "검토 결과"
            attempt_prefix = "시도"
            pass_label = "통과"
            fail_label = "개선필요"

        if not reviews:
            ax.text(
                0.5,
                0.5,
                no_data_text,
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title, fontweight="bold")
            return

        attempts = [r["attempt"] for r in reviews]
        passed = [r["passed"] for r in reviews]
        colors = ["#4CAF50" if p else "#F44336" for p in passed]

        bars = ax.bar(
            [f"{attempt_prefix} {a}" for a in attempts],
            [1] * len(attempts),
            color=colors,
            alpha=0.8,
        )
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="bold")
        ax.set_ylim(0, 1.2)

        # 결과 레이블 추가
        for bar, p in zip(bars, passed):
            label = pass_label if p else fail_label
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                0.5,
                label,
                ha="center",
                va="center",
                fontweight="bold",
            )

    def _plot_quality_metrics(self, ax, data):
        """보고서 품질 지표 시각화"""
        ref_stats = data["reference_stats"]

        # 품질 지표 계산 (임의의 기준)
        total_words = ref_stats.get("total_words", 0)
        total_refs = ref_stats.get("total_references", 0)

        # 품질 점수 계산 (0-100 스케일)
        word_score = min(total_words / 3000 * 100, 100)  # 3000단어 기준
        ref_score = min(total_refs / 50 * 100, 100)  # 50개 참고문헌 기준
        overall_score = (word_score + ref_score) / 2

        if self.use_english_labels:
            metrics = ["Content Richness", "Reference Completeness", "Overall Quality"]
            title = "Report Quality Metrics"
            ylabel = "Quality Score"
        else:
            metrics = ["내용 풍부도", "참고문헌 충실도", "전체 품질"]
            title = "보고서 품질 지표"
            ylabel = "품질 점수"

        scores = [word_score, ref_score, overall_score]
        colors = [
            "#4CAF50" if s >= 80 else "#FF9800" if s >= 60 else "#F44336"
            for s in scores
        ]

        bars = ax.bar(metrics, scores, color=colors, alpha=0.8)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="bold")
        ax.set_ylim(0, 100)

        # 점수 레이블 추가
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{score:.1f}",
                ha="center",
                va="bottom",
            )

    def _plot_log_distribution(self, ax, data):
        """로그 레벨 분포 시각화"""
        log_counts = data["log_counts"]

        if self.use_english_labels:
            no_data_text = "No log data"
            title = "Log Level Distribution"
        else:
            no_data_text = "로그 데이터 없음"
            title = "로그 레벨 분포"

        if not log_counts:
            ax.text(
                0.5,
                0.5,
                no_data_text,
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title(title, fontweight="bold")
            return

        levels = list(log_counts.keys())
        counts = list(log_counts.values())
        colors = {
            "INFO": "#2196F3",
            "SUCCESS": "#4CAF50",
            "WARNING": "#FF9800",
            "ERROR": "#F44336",
            "DEBUG": "#9E9E9E",
            "SYSTEM": "#9C27B0",
        }

        pie_colors = [colors.get(level, "#9E9E9E") for level in levels]

        wedges, texts, autotexts = ax.pie(
            counts, labels=levels, colors=pie_colors, autopct="%1.1f%%", startangle=90
        )
        ax.set_title(title, fontweight="bold")

        # 텍스트 스타일 개선
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")

    def _save_individual_plots(self, data, output_dir, timestamp):
        """개별 시각화 저장"""
        try:
            # 각 시각화를 개별 파일로 저장
            if self.use_english_labels:
                plot_configs = [
                    (
                        "workflow_progress",
                        self._plot_workflow_progress,
                        "workflow_progress",
                    ),
                    ("execution_times", self._plot_execution_times, "execution_times"),
                    ("reference_stats", self._plot_reference_stats, "reference_stats"),
                    (
                        "editorial_review",
                        self._plot_editorial_review,
                        "editorial_review",
                    ),
                    ("quality_metrics", self._plot_quality_metrics, "quality_metrics"),
                    (
                        "log_distribution",
                        self._plot_log_distribution,
                        "log_distribution",
                    ),
                ]
            else:
                plot_configs = [
                    (
                        "workflow_progress",
                        self._plot_workflow_progress,
                        "워크플로우_진행상황",
                    ),
                    ("execution_times", self._plot_execution_times, "작업별_소요시간"),
                    ("reference_stats", self._plot_reference_stats, "참고문헌_통계"),
                    (
                        "editorial_review",
                        self._plot_editorial_review,
                        "편집장_검토결과",
                    ),
                    ("quality_metrics", self._plot_quality_metrics, "보고서_품질지표"),
                    ("log_distribution", self._plot_log_distribution, "로그_레벨분포"),
                ]

            for plot_id, plot_func, title in plot_configs:
                fig, ax = plt.subplots(figsize=(10, 6))
                plot_func(ax, data)
                plt.tight_layout()

                filename = f"{title}_{timestamp}.png"
                filepath = os.path.join(output_dir, filename)
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                plt.close()

            if self.use_english_labels:
                print(f"📈 Individual visualizations saved: {len(plot_configs)} files")
            else:
                print(f"📈 개별 시각화 {len(plot_configs)}개 저장 완료")

        except Exception as e:
            error_msg = (
                f"Error saving individual plots: {e}"
                if self.use_english_labels
                else f"개별 시각화 저장 중 오류: {e}"
            )
            print(f"❌ {error_msg}")


# LangGraph 상태 정의
class ReportState(TypedDict):
    topic: str
    outline: str
    report_content: Dict[str, str]
    current_report_text: str
    review_result: dict
    review_history: List[dict]
    review_attempts: int
    formatted_report: str
    final_report_with_refs: str
    progress_message: str


# =============================================================================
# 모델 및 Thinking Budget 설정 (generate_report.py 참조)
# =============================================================================
# USE_PRODUCTION_MODELS = True # GUI에서 선택하도록 변경

# 테스트용 모델 및 예산
TEST_MODELS = {
    "outline_generation": "gemini-2.5-flash-lite-preview-06-17",
    "draft_generation": "gemini-2.5-flash-lite-preview-06-17",
    "editorial_review": "gemini-2.5-flash-lite-preview-06-17",
    "final_formatting": "gemini-2.5-flash-lite-preview-06-17",
}
TEST_THINKING_BUDGETS = {
    "outline_generation": 0,
    "draft_generation": 0,
    "editorial_review": 8192,
    "final_formatting": 0,
}

# 프로덕션용 모델 및 예산
PRODUCTION_MODELS = {
    "outline_generation": "gemini-2.5-pro",
    "draft_generation": "gemini-2.5-pro",
    "editorial_review": "gemini-2.5-pro",  # 중요 작업은 Pro 유지
    "final_formatting": "gemini-2.5-pro",
}
PRODUCTION_THINKING_BUDGETS = {
    "outline_generation": 128,
    "draft_generation": 128,
    "editorial_review": 8192,
    "final_formatting": 128,
}

# # 현재 사용할 모델 및 예산 설정 -> 동적으로 변경
# MODELS = PRODUCTION_MODELS if USE_PRODUCTION_MODELS else TEST_MODELS
# THINKING_BUDGETS = (
#     PRODUCTION_THINKING_BUDGETS if USE_PRODUCTION_MODELS else TEST_THINKING_BUDGETS
# )

DB_INDEX_PATH = "vector_db.faiss"
DB_DATA_PATH = "vector_db_data.json"
EMBEDDING_MODEL = "models/text-embedding-004"
MAX_REVIEW_ATTEMPTS = 3  # 편집장 검토 최대 시도 횟수 (2 -> 3으로 증가)
# =============================================================================

NUM_CLUSTERS_FOR_OUTLINE = 15
K_FOR_TOPIC_SEARCH = 15
K_FOR_SECTION_DRAFT = 25  # 10 -> 25로 증가 (더 많은 컨텍스트 검색)


class RAGReportGeneratorAppV3:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("RAG 리포트 생성기 v4 (지능형)")
        self.root.geometry("500x350")  # 창 크기 확대

        self.index = None
        self.db_data = None
        self.all_vectors = None
        self.client = None  # API 클라이언트 인스턴스
        self.chunk_id_map = {}  # chunk_id를 키로 하는 데이터 맵
        self.graph = None  # LangGraph 인스턴스
        self.logger = ConsoleLogger()  # 콘솔 로거 추가
        self.analyzer = ReportAnalyzer()  # 시각화 분석기 추가

        # 실행 모드 선택용 변수
        self.mode_var = tk.StringVar(value="Production")
        self.models = {}
        self.thinking_budgets = {}

        # 각주/참고문헌 추적용 -> 플레이스홀더 매핑용으로 변경
        self.ref_placeholder_map = {}
        self.progress_queue = queue.Queue()

        # 결과 폴더 경로들 초기화
        self.results_folder = None
        self.logs_folder = None
        self.viz_folder = None

        self._configure_api()
        if self._load_vector_db():
            self._setup_gui()
            self._print_model_configuration()
            self.graph = self._build_graph()  # 앱 시작 시 그래프 빌드
            self.process_queue()  # 큐 처리 시작

    def _print_model_configuration(self):
        """현재 모델 설정을 콘솔에 출력합니다."""
        mode = self.mode_var.get()
        models_to_print = PRODUCTION_MODELS if mode == "Production" else TEST_MODELS
        budgets_to_print = (
            PRODUCTION_THINKING_BUDGETS if mode == "Production" else TEST_THINKING_BUDGETS
        )

        print(f"\n=== 모델 설정 ({mode} 모드) ===")
        for task, model in models_to_print.items():
            budget = budgets_to_print.get(task)
            budget_str = f" (Thinking Budget: {budget})" if budget is not None else ""
            print(f"  - {task}: {model}{budget_str}")
        print("=" * 40)

    def _setup_gui(self):
        self.label = tk.Label(
            self.root, text="생성할 보고서의 주제를 입력하세요:", wraplength=380
        )
        self.label.pack(pady=10)
        self.topic_entry = tk.Entry(self.root, width=50)
        self.topic_entry.pack(pady=5, padx=10, fill=tk.X)

        # 실행 모드 선택 GUI
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(pady=5)
        tk.Label(mode_frame, text="실행 모드:").pack(side=tk.LEFT, padx=5)
        prod_radio = tk.Radiobutton(
            mode_frame,
            text="Production",
            variable=self.mode_var,
            value="Production",
            command=self._print_model_configuration,
        )
        prod_radio.pack(side=tk.LEFT)
        test_radio = tk.Radiobutton(
            mode_frame,
            text="Test",
            variable=self.mode_var,
            value="Test",
            command=self._print_model_configuration,
        )
        test_radio.pack(side=tk.LEFT)

        self.generate_button = tk.Button(
            self.root, text="리포트 생성 시작", command=self.run_generation_pipeline
        )
        self.generate_button.pack(pady=10)

        # 시각화 버튼 추가
        self.visualization_button = tk.Button(
            self.root,
            text="최근 시각화 보기",
            command=self.show_latest_visualization,
            state="disabled",
        )
        self.visualization_button.pack(pady=5)

        # 로그 파일 보기 버튼 추가
        self.log_button = tk.Button(
            self.root,
            text="로그 파일 보기",
            command=self.show_log_files,
            state="disabled",
        )
        self.log_button.pack(pady=5)

        # 상태 표시 라벨
        self.status_label = tk.Label(self.root, text="준비됨", fg="green")
        self.status_label.pack(pady=5)

        # 최근 생성된 파일 경로들을 저장할 변수
        self.latest_dashboard_path = None
        self.latest_log_path = None

    def _configure_api(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            messagebox.showerror(
                "오류", "GEMINI_API_KEY를 .env 파일에서 찾을 수 없습니다."
            )
            self.root.destroy()
            sys.exit(1)
        google.generativeai.configure(api_key=api_key)
        self.client = genai.Client(api_key=api_key)
        # self.embedding_model_instance = genai.GenerativeModel(
        #     EMBEDDING_MODEL, client=self.client
        # )  # 인스턴스 생성

    def _load_vector_db(self):
        try:
            if not os.path.exists(DB_INDEX_PATH) or not os.path.exists(DB_DATA_PATH):
                messagebox.showerror(
                    "오류",
                    f"'{DB_INDEX_PATH}' 또는 '{DB_DATA_PATH}' 파일을 찾을 수 없습니다.",
                )
                self.root.destroy()
                return False
            self.index = faiss.read_index(DB_INDEX_PATH)
            with open(DB_DATA_PATH, "r", encoding="utf-8") as f:
                self.db_data = json.load(f)

            # DB의 모든 벡터를 메모리에 로드
            self.all_vectors = np.array(
                [self.index.reconstruct(i) for i in range(self.index.ntotal)]
            ).astype("float32")

            # chunk_id를 키로 하는 맵을 생성 (reference_text가 있는 것만)
            self.chunk_id_map = {
                item["chunk_id"]: item
                for item in self.db_data
                if "chunk_id" in item and item.get("reference_text")
            }

            # 통계 출력
            total_chunks = len(self.db_data)
            with_references = len(self.chunk_id_map)

            print(f"\n=== Vector DB 로드 완료 ===")
            print(f"  - 전체 청크: {total_chunks}")
            print(f"  - 참고문헌 있는 청크: {with_references}")
            print(f"  - 참고문헌 비율: {with_references/total_chunks*100:.1f}%")
            print("=" * 40)

            messagebox.showinfo(
                "DB 로드 완료",
                f"총 {self.index.ntotal}개의 벡터가 포함된 DB를 성공적으로 로드했습니다.\n참고문헌 있는 청크: {with_references}개 ({with_references/total_chunks*100:.1f}%)",
            )
            return True
        except Exception as e:
            messagebox.showerror("DB 로드 실패", f"DB 파일 로드 중 오류 발생: {e}")
            self.root.destroy()
            return False

    def _search_similar_documents(self, query, k=10):
        query_embedding = google.generativeai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="RETRIEVAL_QUERY",
        )["embedding"]

        # 더 많은 후보를 검색해서 참고문헌 있는 것을 우선 선택
        candidate_k = min(k * 3, len(self.db_data))  # 3배 더 검색
        distances, indices = self.index.search(
            np.array([query_embedding], dtype="float32"), candidate_k
        )

        candidates = [self.db_data[i] for i in indices[0]]

        # 참고문헌 있는 것을 우선 선택
        with_refs = [c for c in candidates if c.get("reference_text")]
        without_refs = [c for c in candidates if not c.get("reference_text")]

        # 참고문헌 있는 것을 우선하되, 총 k개가 되도록 조정
        result = with_refs[:k] + without_refs[: max(0, k - len(with_refs))]

        return result[:k]

    def _get_model_for_task(self, task_name):
        model_name = self.models.get(task_name, "gemini-1.5-flash-latest")
        # print(f"[{task_name}] 모델: {model_name}") # 개별 로깅은 _print_model_configuration으로 대체
        return model_name

    def _get_generation_config(self, task_name):
        """작업에 맞는 GenerateContentConfig를 반환합니다 (thinking_budget 포함)."""
        budget = self.thinking_budgets.get(task_name)

        # budget=0도 유효한 값이므로 is not None으로 확인합니다.
        if budget is not None:
            # 공식 문서에 따라 types.GenerateContentConfig와 types.ThinkingConfig를 사용합니다.
            return types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=budget)
            )

        # 예산이 설정되지 않은 경우, 기본값으로 동작하도록 None을 반환합니다.
        return None

    def _extract_key_themes(self):
        """K-Means 클러스터링으로 DB의 핵심 주제를 추출합니다."""
        if self.index.ntotal < NUM_CLUSTERS_FOR_OUTLINE:
            num_clusters = self.index.ntotal
        else:
            num_clusters = NUM_CLUSTERS_FOR_OUTLINE

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(self.all_vectors)

        representative_indices = []
        for i in range(num_clusters):
            cluster_indices = np.where(kmeans.labels_ == i)[0]
            if len(cluster_indices) > 0:
                # 각 클러스터의 중심에 가장 가까운 샘플(벡터) 찾기
                cluster_center = kmeans.cluster_centers_[i]
                distances = faiss.pairwise_distances(
                    cluster_center.reshape(1, -1), self.all_vectors[cluster_indices]
                )
                closest_in_cluster = np.argmin(distances)
                representative_indices.append(cluster_indices[closest_in_cluster])

        return [self.db_data[i] for i in representative_indices]

    def _generate_outline_logic(self, topic):
        """개요 생성 로직 (기존 _generate_outline)"""
        # 1. Vector DB 전체에서 핵심 주제 추출 (Broad View)
        key_theme_contexts = self._extract_key_themes()

        # 2. 사용자 주제와 직접 관련된 문서 검색 (Focused View)
        topic_specific_contexts = self._search_similar_documents(
            topic, k=K_FOR_TOPIC_SEARCH
        )

        # 3. 두 컨텍스트를 합치고 중복 제거
        combined_contexts = {
            item["sentence"]: item
            for item in key_theme_contexts + topic_specific_contexts
        }.values()

        context_str = "\n\n---\n\n".join(
            [
                f"문서: {c['file_path']}\n목차: {' > '.join(c['headers'])}\n문장: {c['sentence']}"
                for c in combined_contexts
            ]
        )

        prompt = f"""
        당신은 법률 정책 연구소의 수석 연구원입니다. 방대한 양의 리서치 자료를 분석하여 깊이 있는 보고서의 개요를 설계하는 임무를 맡았습니다.

        **분석된 자료:**
        - **핵심 주제 그룹:** 전체 데이터베이스를 분석하여 추출한 핵심 주제들입니다. 데이터의 전체적인 그림을 보여줍니다.
        - **요청 주제 관련 자료:** 사용자가 요청한 특정 주제와 직접적으로 관련된 자료들입니다.

        **핵심 보고서 주제:** "{topic}"

        **지시사항:**
        1.  **종합적 분석:** '핵심 주제 그룹'과 '요청 주제 관련 자료'를 모두 활용하여, 두 관점을 통합하는 종합적인 보고서 목차를 만드세요. 어느 한쪽의 정보도 누락해서는 안 됩니다.
        2.  **논리적 구조 설계:** 서론-본론-결론의 명확한 구조를 따르세요. 본론은 여러 개의 장(Chapter)으로 나누고, 각 장은 다시 여러 절(Section)으로 세분화하여 매우 상세하고 체계적인 구조를 갖춰야 합니다.
        3.  **최종 목표 지향:** 보고서의 최종 목표는 '한국의 사내 변호사 ACP 도입을 위한 법적, 정책적 시사점 도출'입니다. 모든 목차 구성은 이 목표를 달성하는 과정이 되도록 설계하세요. 유럽 사례 분석, 이론적 배경, 각국 비교 등을 논리적으로 배치하여 최종 결론으로 연결되게 하세요.
        4.  **출력 형식:** 다른 설명 없이, 오직 마크다운 형식의 목차만 출력하세요.

        --- 분석된 참고 자료 (핵심 주제 및 요청 주제 관련) ---
        {context_str}
        --- 끝 ---

        위 지시사항과 목표에 따라, 데이터베이스의 전체적인 내용과 사용자의 특정 요구를 모두 반영하는, 매우 완성도 높은 보고서 목차를 작성해주십시오.
        """
        model_name = self._get_model_for_task("outline_generation")
        config = self._get_generation_config("outline_generation")
        response = self.client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )
        return response.text

    def _generate_single_section(self, header, topic, improvement_instructions=""):
        """하나의 섹션 본문을 생성하는 함수 (개선 지침 추가)"""
        # 다양한 검색 키워드로 더 많은 참고문헌 찾기
        queries = [
            f"{topic} - {header}",
            f"{header}",
            f"{topic} {header}",
            f"{header} 사례 판례",
            f"{header} 법률 제도",
        ]

        all_contexts = []
        seen_sentences = set()

        for query in queries:
            contexts = self._search_similar_documents(
                query, k=K_FOR_SECTION_DRAFT // len(queries) + 2
            )
            for c in contexts:
                if c["sentence"] not in seen_sentences:
                    all_contexts.append(c)
                    seen_sentences.add(c["sentence"])

        # 상위 K_FOR_SECTION_DRAFT개만 선택
        contexts = all_contexts[:K_FOR_SECTION_DRAFT]

        context_str = ""
        valid_citations = []  # 유효한 인용만 저장
        context_without_refs = []  # 참고문헌 없는 컨텍스트

        for i, c in enumerate(contexts):
            context_str += f"--- 컨텍스트 {i+1} ---\n"
            context_str += f"참고 문장: {c['sentence']}\n"

            # reference_text와 chunk_id가 모두 있는 경우에만 CITATION 태그 제공
            if c.get("reference_text") and c.get("chunk_id"):
                citation_tag = f"[CITATION:{c['chunk_id']}]"
                context_str += f"🔖 필수 참고문헌 태그: {citation_tag}\n"
                valid_citations.append(c["chunk_id"])
            else:
                context_str += f"⚠️ 참고문헌 태그 없음 (내용만 참고)\n"
                context_without_refs.append(c)

        # 참고문헌 비율 계산
        ref_ratio = len(valid_citations) / len(contexts) * 100 if contexts else 0
        print(
            f"  - 섹션 '{header}': 총 {len(contexts)}개 컨텍스트 중 {len(valid_citations)}개 참고문헌 ({ref_ratio:.1f}%)"
        )

        # 유효한 citation 강조
        if valid_citations:
            citation_list = "\n".join(
                [
                    f"  🔖 {i+1}. [CITATION:{cid}]"
                    for i, cid in enumerate(valid_citations)
                ]
            )
            citation_instruction = f"""
🚨 **반드시 사용해야 하는 참고문헌 태그 목록** 🚨
{citation_list}

⚠️ **필수 준수 사항:**
- 위 태그들을 최대한 많이 사용하세요 (목표: 80% 이상)
- 태그는 정확히 복사하여 문장 끝에 붙이세요
- 절대 임의로 [^1] 같은 각주 번호를 만들지 마세요
"""
        else:
            citation_instruction = """
⚠️ **주의:** 이 섹션에는 참고문헌 태그가 없습니다.
- 모든 내용은 참고하되 인용 태그는 사용하지 마세요
- 절대 임의로 [^1] 같은 각주 번호를 만들지 마세요
"""

        # 개선 지침이 있다면 프롬프트에 추가
        improvement_prompt_part = ""
        if improvement_instructions:
            improvement_prompt_part = f"""
🔧 **편집장 개선 지시사항:**
{improvement_instructions}
"""

        prompt = f"""
🎯 **임무:** 법률 보고서 '{header}' 섹션의 전문적인 본문 작성

**보고서 주제:** {topic}
**현재 섹션:** {header}
{improvement_prompt_part}

{citation_instruction}

🎯 **핵심 지시사항:**
1. **참고문헌 태그 우선 사용**: 🔖 표시된 태그를 최대한 많이 사용하세요
2. **정확한 복사**: 태그는 정확히 복사하여 관련 문장 끝에 붙이세요
3. **임의 생성 금지**: [^1], [1] 같은 각주 번호는 절대 만들지 마세요
4. **참고자료 기반**: 주어진 참고 문장만 사용하세요 (외부 지식 금지)
5. **자연스러운 연결**: 문단을 논리적으로 연결하고 깊이 있게 분석하세요

--- 📚 참고자료 ---
{context_str}
--- 끝 ---

위 지시사항을 준수하여 전문적인 본문을 작성하세요.
"""
        model_name = self._get_model_for_task("draft_generation")
        config = self._get_generation_config("draft_generation")
        response = self.client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )

        # AI 응답에서 실제로 태그를 사용했는지 검증
        response_text = response.text
        
        # 새로운 검증 로직
        returned_citation_ids = set(re.findall(r"\[CITATION:(.*?)\]", response_text))
        provided_citation_ids = set(valid_citations)

        correctly_used_ids = provided_citation_ids.intersection(returned_citation_ids)
        hallucinated_ids = returned_citation_ids.difference(provided_citation_ids)
        
        num_correctly_used = len(correctly_used_ids)
        num_expected = len(provided_citation_ids)
        num_hallucinated = len(hallucinated_ids)

        # 로그 메시지 생성
        if num_expected > 0:
            usage_percent = (num_correctly_used / num_expected) * 100
            log_msg = f"    📊 태그 사용 검증: {num_correctly_used}/{num_expected}개 사용 ({usage_percent:.1f}%)"
        else:
            log_msg = "    📊 태그 사용 검증: 참고문헌 없음"
        
        if num_hallucinated > 0:
            log_msg += f" | ⚠️ 생성된(hallucinated) 태그: {num_hallucinated}개"
        
        print(log_msg)


        # 태그 사용률이 낮으면 경고
        if num_expected > 0 and (num_correctly_used / num_expected) < 0.5:
            print(
                f"    ⚠️ 경고: AI가 제공된 {num_expected}개 태그 중 {num_correctly_used}개만 올바르게 사용했습니다."
            )

        return response_text

    def _editorial_review_logic(self, report_text, outline):
        """편집장 검토 로직 (기존 _editorial_review)"""
        prompt = f"""
        당신은 법률 보고서 전문 편집장입니다. 주어진 '보고서 개요'와 '작성된 초안'을 비교하여, 초안의 품질을 높이기 위한 구체적인 개선 지침을 제공해야 합니다.

        **검토 지시사항:**
        1. '작성된 초안'이 '보고서 개요'의 모든 항목을 충실하게 다루고 있는지 확인합니다.
        2. 각 섹션별로 내용이 부실하거나, 논리가 부족하거나, 분석의 깊이가 얕은 부분을 찾아냅니다.
        3. 모든 내용이 완벽하다면 "sections_to_improve"를 빈 리스트 `[]`로 반환합니다.
        4. 개선이 필요하다면, **어떤 섹션을(section_header), 왜(reason), 어떻게(how_to_improve)** 개선해야 하는지 구체적인 지침을 작성합니다. 'how_to_improve'는 실제 재작성 AI에게 전달될 명확한 지시여야 합니다.
        5. 당신의 의견이나 분석은 절대 추가하지 말고, 오직 지정된 JSON 형식으로만 응답하세요.

        --- 보고서 개요 ---
        {outline}
        --- 끝 ---

        --- 작성된 초안 ---
        {report_text}
        --- 끝 ---

        **출력 형식 (오직 JSON만):**
        ```json
        {{
          "review_passed": boolean,
          "sections_to_improve": [
            {{
              "section_header": "### 수정이 필요한 섹션 전체 제목 1",
              "reason": "현재 내용이 너무 추상적이고 구체적인 사례가 부족함.",
              "how_to_improve": "제공된 참고자료에서 독일의 판례 2가지와 프랑스의 관련 법 조항 1가지를 명시적으로 인용하여, 주장을 뒷받침하는 구체적인 근거를 2~3문단에 걸쳐 상세히 보강할 것."
            }}
          ]
        }}
        ```
        """
        model_name = self._get_model_for_task("editorial_review")
        config = self._get_generation_config("editorial_review")
        response = self.client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )

        try:
            json_text = re.search(
                r"```json\n(.*)\n```", response.text, re.DOTALL
            ).group(1)
            return json.loads(json_text)
        except Exception as e:
            print(f"편집장 응답 파싱 실패: {e}\n응답 내용: {response.text}")
            # 무조건 통과 대신, 실패로 처리하고 재시도를 유도
            return {
                "review_passed": False,
                "sections_to_improve": [
                    {
                        "section_header": "전체 보고서",
                        "reason": "편집장 검토 모델의 응답 형식 오류로 자동 재작성이 필요합니다.",
                        "how_to_improve": "보고서 개요에 맞춰 전체적인 구조와 내용을 다시 검토하고, 논리적 흐름을 보강하여 재작성해주세요.",
                    }
                ],
            }

    def _final_formatting_logic(self, report_text):
        """최종 서식 정리 로직 (기존 _final_formatting)"""
        prompt = f"""
        당신은 출판 전문가입니다. 주어진 보고서 초안의 내용을 변경하지 않고, 오직 마크다운 서식만을 사용하여 가독성을 극대화하는 임무를 맡았습니다.

        **지시사항:**
        1. **내용 절대 변경 금지:** 단어 하나, 문장 하나도 수정하거나 추가/삭제하지 마세요.
        2. **서식 최적화:** 헤더(#, ##, ###)의 계층 구조를 명확히 하고, 목록, 인용구(>), 강조(**) 등을 일관성 있게 사용하여 가독성을 높여주세요.
        3. **CITATION 태그 절대 유지:** `[CITATION:...]` 형식의 태그는 절대 변경하거나 제거하지 마세요. 이 태그는 각주 처리를 위해 필수적입니다.
        4. **불필요한 기호 제거:** 본문에 남아있는 `🔖` 기호는 모두 제거해주세요.
        5. **출력:** 다른 설명 없이, 오직 서식이 개선된 최종 마크다운 텍스트만 출력하세요.

        --- 원본 보고서 텍스트 ---
        {report_text}
        --- 끝 ---

        위 지시사항을 준수하여 최종 보고서를 보기 좋게 정리해주세요.
        """
        model_name = self._get_model_for_task("final_formatting")
        config = self._get_generation_config("final_formatting")
        response = self.client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )
        return response.text

    def _finalize_citations_logic(self, final_text):
        """각주 처리 로직 (기존 _finalize_citations)"""
        # 1. 본문에 사용된 CITATION ID를 순서대로 추출 (중복 제거)
        citation_ids_in_order = list(
            dict.fromkeys(re.findall(r"\[CITATION:(.*?)\]", final_text))
        )

        print(f"\n=== 참고문헌 처리 상세 분석 ===")
        print(f"전체 데이터 청크: {len(self.db_data)}개")
        print(
            f"참고문헌 있는 청크: {len(self.chunk_id_map)}개 ({len(self.chunk_id_map)/len(self.db_data)*100:.1f}%)"
        )
        print(f"본문에서 발견된 CITATION 태그: {len(citation_ids_in_order)}개")

        if not citation_ids_in_order:
            print("❌ 본문에서 CITATION 태그를 찾지 못했습니다.")
            print("🔍 AI가 참고문헌 태그를 사용하지 않은 것 같습니다.")
            return final_text, ""

        # 2. 유효한 chunk_id만 필터링
        valid_citation_ids = []
        invalid_citation_ids = []

        for chunk_id in citation_ids_in_order:
            if chunk_id in self.chunk_id_map:
                # chunk_id_map에는 이미 reference_text가 있는 것만 포함되어 있음
                valid_citation_ids.append(chunk_id)
                print(f"    ✅ 유효한 chunk_id: {chunk_id[:20]}...")
            else:
                invalid_citation_ids.append(chunk_id)
                print(f"    ❌ 무효한 chunk_id: '{chunk_id}'")

        if invalid_citation_ids:
            print(f"⚠️ 무효한 태그 {len(invalid_citation_ids)}개를 제거합니다.")

        if not valid_citation_ids:
            print("❌ 유효한 참고문헌 태그가 없습니다.")
            print("🔍 AI가 제공된 태그를 올바르게 사용하지 않았습니다.")
            # 무효한 태그들만 제거하고 반환
            processed_text = final_text
            for invalid_id in invalid_citation_ids:
                processed_text = processed_text.replace(f"[CITATION:{invalid_id}]", "")
            return processed_text, ""

        # 3. 무효한 태그들을 본문에서 제거
        processed_text = final_text
        for invalid_id in invalid_citation_ids:
            processed_text = processed_text.replace(f"[CITATION:{invalid_id}]", "")

        # 4. 유효한 태그만 처리 - CITATION ID와 실제 각주 번호 매핑
        ref_number_map = {
            chunk_id: i + 1 for i, chunk_id in enumerate(valid_citation_ids)
        }

        # 5. 본문의 태그를 각주 번호로 교체
        for chunk_id, number in ref_number_map.items():
            processed_text = processed_text.replace(
                f"[CITATION:{chunk_id}]", f"[^{number}]"
            )

        # 불필요한 🔖 마커를 최종적으로 제거
        processed_text = processed_text.replace("🔖", "")

        # 6. 참고문헌 목록 생성 (유효한 것만)
        references_list_str = "\n\n---\n\n## 참고문헌\n\n"
        for i, chunk_id in enumerate(valid_citation_ids):
            number = i + 1
            original_ref_item = self.chunk_id_map[chunk_id]
            ref_text = original_ref_item["reference_text"]
            references_list_str += f"[^{number}]: {ref_text}\n"

        # 성과 요약
        usage_rate = len(valid_citation_ids) / len(self.chunk_id_map) * 100
        print(f"\n🎯 참고문헌 활용 성과:")
        print(f"   - 전체 이용 가능한 참고문헌: {len(self.chunk_id_map)}개")
        print(f"   - 실제 사용된 참고문헌: {len(valid_citation_ids)}개")
        print(f"   - 활용률: {usage_rate:.1f}%")
        print(f"   - 최종 참고문헌 목록: {len(valid_citation_ids)}개")
        print("=" * 50)

        return processed_text, references_list_str

    # =============================================================================
    # LangGraph 노드 정의
    # =============================================================================
    def node_generate_outline(self, state: ReportState):
        """개요 생성 노드"""
        self.logger.set_current_node("generate_outline")
        self.logger.add_log("INFO", "[1/6] 보고서 개요 생성 시작")

        topic = state["topic"]
        self.logger.add_log("INFO", f"주제: {topic}")

        outline = self._generate_outline_logic(topic)
        self.logger.add_log("SUCCESS", f"개요 생성 완료 (길이: {len(outline)}자)")

        return {
            "outline": outline,
            "progress_message": "1/6: 개요 생성 완료. 초안 작성 시작...",
        }

    def node_generate_draft(self, state: ReportState):
        """초안 생성 노드"""
        self.logger.set_current_node("generate_draft")
        self.logger.add_log("INFO", "[2/6] 보고서 초안 생성 시작")

        topic = state["topic"]
        outline = state["outline"]
        section_headers = re.findall(r"^(#+ .*)$", outline, re.MULTILINE)
        self.logger.add_log("INFO", f"총 {len(section_headers)}개 섹션 생성 예정")

        report_content = {}
        for i, header in enumerate(section_headers):
            progress_msg = f"초안 생성 중({i+1}/{len(section_headers)}): {header}"
            self.logger.add_log("INFO", progress_msg)
            self.root.title(progress_msg)
            self.root.update_idletasks()
            report_content[header] = self._generate_single_section(header, topic)

        current_report_text = "\n\n".join(
            [f"{header}\n{text}" for header, text in report_content.items()]
        )
        self.logger.add_log(
            "SUCCESS", f"초안 생성 완료 (총 길이: {len(current_report_text)}자)"
        )

        return {
            "report_content": report_content,
            "current_report_text": current_report_text,
            "progress_message": "2/6: 초안 생성 완료. 편집장 검토 시작...",
        }

    def node_editorial_review(self, state: ReportState):
        """편집장 검토 노드"""
        self.logger.set_current_node("editorial_review")
        self.logger.add_log("INFO", "[3/6] 편집장 검토 및 개선 작업 시작")

        current_report_text = state["current_report_text"]
        outline = state["outline"]
        review_attempts = state["review_attempts"] + 1

        self.logger.add_log(
            "INFO", f"편집장 검토 시도 ({review_attempts}/{MAX_REVIEW_ATTEMPTS})"
        )
        self.root.title(
            f"편집장 검토... (시도 {review_attempts}/{MAX_REVIEW_ATTEMPTS})"
        )
        self.root.update_idletasks()

        review_result = self._editorial_review_logic(current_report_text, outline)
        review_history = state["review_history"] + [
            {"attempt": review_attempts, "result": review_result}
        ]

        # 검토 결과 로깅
        if review_result.get("review_passed", True):
            self.logger.add_log("SUCCESS", "편집장 검토 통과")
        else:
            sections_to_improve = review_result.get("sections_to_improve", [])
            self.logger.add_log(
                "WARNING",
                f"편집장 검토 결과: {len(sections_to_improve)}개 섹션 개선 필요",
            )
            for section in sections_to_improve:
                self.logger.add_log(
                    "WARNING",
                    f"  - 개선 필요: {section.get('section_header', 'Unknown')}",
                )

        return {
            "review_result": review_result,
            "review_history": review_history,
            "review_attempts": review_attempts,
            "progress_message": f"3/6: 편집장 검토 {review_attempts}차 완료.",
        }

    def node_regenerate_sections(self, state: ReportState):
        """검토 결과에 따라 섹션 재작성 노드"""
        self.logger.set_current_node("regenerate_sections")

        review_result = state["review_result"]
        sections_to_improve = review_result.get("sections_to_improve", [])
        self.logger.add_log("INFO", f"편집장 개선 요청: {len(sections_to_improve)}개 섹션 재작성 필요")

        topic = state["topic"]
        report_content = state["report_content"].copy()
        
        regenerated_count = 0
        for i, section_data in enumerate(sections_to_improve):
            header = section_data.get("section_header")
            instructions = section_data.get("how_to_improve")
            
            # 여러 형식의 헤더(###, #### 등)를 모두 처리하기 위해 정규식으로 찾기
            matching_headers = [h for h in report_content.keys() if header.strip().endswith(h.strip('# ').strip())]
            
            if matching_headers:
                actual_header = matching_headers[0]
                progress_msg = f"재작성 중({i+1}/{len(sections_to_improve)}): {actual_header}"
                self.logger.add_log("INFO", progress_msg)
                self.root.title(progress_msg)
                self.root.update_idletasks()
                
                # _generate_single_section을 호출하여 실제로 재작성 수행
                report_content[actual_header] = self._generate_single_section(
                    actual_header, topic, improvement_instructions=instructions
                )
                regenerated_count += 1
            else:
                self.logger.add_log("WARNING", f"재작성 대상 섹션을 찾지 못했습니다: '{header}'")


        current_report_text = "\n\n".join(
            [f"{h}\n{t}" for h, t in report_content.items()]
        )

        self.logger.add_log("SUCCESS", f"{regenerated_count}개 섹션 재작성 완료")

        return {
            "report_content": report_content,
            "current_report_text": current_report_text,
            "progress_message": f"개선 요청된 {len(sections_to_improve)}개 섹션 재작성 완료. 다시 편집장 검토를 받습니다.",
        }

    def node_final_formatting(self, state: ReportState):
        """최종 서식 정리 노드"""
        self.logger.set_current_node("final_formatting")
        self.logger.add_log("INFO", "[4/6] 최종 가독성 향상을 위한 서식 정리 시작")

        current_report_text = state["current_report_text"]
        self.logger.add_log(
            "INFO", f"서식 정리 전 텍스트 길이: {len(current_report_text)}자"
        )

        formatted_report = self._final_formatting_logic(current_report_text)
        self.logger.add_log(
            "SUCCESS", f"서식 정리 완료 (최종 길이: {len(formatted_report)}자)"
        )

        return {
            "formatted_report": formatted_report,
            "progress_message": "4/6: 서식 정리 완료. 각주 처리 시작...",
        }

    def node_finalize_citations_and_save_log(self, state: ReportState):
        """각주 처리 및 검토 로그 저장 노드"""
        self.logger.set_current_node("finalize_and_save")
        self.logger.add_log(
            "INFO", "[5/6] 최종 각주 번호 부여 및 참고문헌 목록 생성 시작"
        )

        formatted_report = state["formatted_report"]
        final_report_body, references_list = self._finalize_citations_logic(
            formatted_report
        )
        final_report_with_refs = final_report_body + references_list

        # 참고문헌 통계 로깅
        ref_count = references_list.count("[^") if references_list else 0
        self.logger.add_log("INFO", f"최종 참고문헌 개수: {ref_count}개")

        # 편집장 검토 기록 저장
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")
        review_log_filename = f"editorial_review_log_{date_str}.md"
        # 결과 폴더에 저장하기 위해 경로 생성 (self.results_folder는 run_generation_in_thread에서 설정됨)
        if hasattr(self, "results_folder") and self.results_folder:
            review_log_path = os.path.join(self.results_folder, review_log_filename)
        else:
            review_log_path = review_log_filename

        self.logger.add_log(
            "INFO", f"편집장 검토 기록을 '{review_log_path}' 파일로 저장 중"
        )

        with open(review_log_path, "w", encoding="utf-8") as f:
            f.write(f"# 편집장 검토 기록 ({date_str})\n\n")

            # 사용된 AI 모델 정보 추가
            f.write("## 사용된 AI 모델\n\n")
            model_names = {
                "outline_generation": "개요 생성",
                "draft_generation": "초안 생성",
                "editorial_review": "편집장 검토",
                "final_formatting": "최종 서식 정리",
            }
            for task, model in self.models.items():
                task_name = model_names.get(task, task)
                f.write(f"- **{task_name}:** `{model}`\n")
            f.write("\n")

            # 참고문헌 통계 정보 추가
            total_chunks = len(self.db_data) if self.db_data else 0
            with_references = len(self.chunk_id_map) if self.chunk_id_map else 0
            f.write(f"## 참고문헌 통계\n\n")
            f.write(f"- 전체 데이터 청크: {total_chunks}개\n")
            f.write(f"- 참고문헌 있는 청크: {with_references}개\n")
            f.write(f"- 참고문헌 비율: {with_references/total_chunks*100:.1f}%\n\n")

            # 최종 보고서의 참고문헌 개수
            f.write(f"- 최종 보고서 참고문헌 개수: {ref_count}개\n\n")

            for item in state["review_history"]:
                f.write(f"## 검토 시도 #{item['attempt']}\n\n")
                result = item["result"]
                if result.get("review_passed", True) or not result.get(
                    "sections_to_improve"
                ):
                    f.write("**결과:** 🟢 승인됨\n\n")
                else:
                    f.write("**결과:** 🔴 개선 필요\n\n")
                    f.write("### 개선 요청 사항:\n\n")
                    for i, sec in enumerate(result["sections_to_improve"]):
                        f.write(f"**{i+1}. 섹션:** `{sec.get('section_header')}`\n")
                        f.write(f"   - **문제점:** {sec.get('reason')}\n")
                        f.write(f"   - **개선 지침:** {sec.get('how_to_improve')}\n\n")

        self.logger.add_log("SUCCESS", f"편집장 검토 기록 저장 완료: {review_log_path}")

        return {
            "final_report_with_refs": final_report_with_refs,
            "progress_message": "5/6: 각주 처리 및 로그 저장 완료. 최종 파일 저장 준비...",
        }

    # =============================================================================
    # LangGraph 조건부 엣지
    # =============================================================================
    def should_continue_review(self, state: ReportState):
        """편집장 검토를 계속할지 결정하는 조건부 엣지"""
        review_result = state["review_result"]
        review_attempts = state["review_attempts"]

        if review_result.get("review_passed", True) or not review_result.get(
            "sections_to_improve"
        ):
            print("  - 편집장 검토 결과: 통과. 개선 작업을 종료합니다.")
            return "end_review"

        if review_attempts >= MAX_REVIEW_ATTEMPTS:
            print(
                f"  - 최대 검토 횟수({MAX_REVIEW_ATTEMPTS})에 도달했습니다. 개선을 중단하고 다음 단계로 진행합니다."
            )
            return "end_review"

        return "regenerate"

    # =============================================================================
    # LangGraph 빌드 및 실행
    # =============================================================================
    def _build_graph(self):
        """LangGraph 워크플로우를 구성합니다."""
        workflow = StateGraph(ReportState)

        # 노드 추가
        workflow.add_node("generate_outline", self.node_generate_outline)
        workflow.add_node("generate_draft", self.node_generate_draft)
        workflow.add_node("editorial_review", self.node_editorial_review)
        workflow.add_node("regenerate_sections", self.node_regenerate_sections)
        workflow.add_node("final_formatting", self.node_final_formatting)
        workflow.add_node(
            "finalize_and_save", self.node_finalize_citations_and_save_log
        )

        # 엣지 연결
        workflow.set_entry_point("generate_outline")
        workflow.add_edge("generate_outline", "generate_draft")
        workflow.add_edge("generate_draft", "editorial_review")

        # 조건부 엣지 (편집장 검토 루프)
        workflow.add_conditional_edges(
            "editorial_review",
            self.should_continue_review,
            {"regenerate": "regenerate_sections", "end_review": "final_formatting"},
        )
        workflow.add_edge("regenerate_sections", "editorial_review")

        workflow.add_edge("final_formatting", "finalize_and_save")
        workflow.add_edge("finalize_and_save", END)

        return workflow.compile()

    def run_generation_pipeline(self):
        """GUI에서 호출되는 시작 메서드입니다."""
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning("입력 오류", "보고서 주제를 입력해주세요.")
            return

        self.generate_button.config(state="disabled")
        self.visualization_button.config(state="disabled")
        self.log_button.config(state="disabled")
        self._update_status("보고서 생성 시작...", "blue")

        threading.Thread(
            target=self.run_generation_in_thread, args=(topic,), daemon=True
        ).start()

    def process_queue(self):
        """큐를 확인하여 GUI 업데이트를 처리합니다."""
        try:
            message = self.progress_queue.get_nowait()
            if "progress_message" in message:
                self.root.title(message["progress_message"])
                self._update_status(message["progress_message"], "blue")
            if "final_report" in message:
                # 최종 보고서 처리 로직
                self._show_report(message["final_report"])
                messagebox.showinfo("생성 완료", "리포트 생성이 완료되었습니다.")
                self._update_status("리포트 생성 완료", "green")
            if "error" in message:
                messagebox.showerror("오류", message["error"])
                self._update_status("오류 발생", "red")
            if "generation_done" in message:
                self.generate_button.config(state="normal")
                # 버튼 활성화 및 최신 파일 경로 업데이트
                self._update_buttons_after_generation()

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def _update_buttons_after_generation(self):
        """생성 완료 후 버튼 상태를 업데이트합니다."""
        try:
            # 가장 최근 생성된 결과 폴더 찾기
            result_folders = [
                f
                for f in os.listdir(".")
                if f.startswith("results_") and os.path.isdir(f)
            ]

            if result_folders:
                result_folders.sort(reverse=True)  # 최신 순으로 정렬
                latest_result_folder = result_folders[0]

                # 시각화 파일 찾기
                viz_folder = os.path.join(latest_result_folder, "visualizations")
                if os.path.exists(viz_folder):
                    dashboard_files = [
                        f
                        for f in os.listdir(viz_folder)
                        if f.startswith("dashboard_") and f.endswith(".png")
                    ]
                    if dashboard_files:
                        dashboard_files.sort(reverse=True)
                        self.latest_dashboard_path = os.path.join(
                            viz_folder, dashboard_files[0]
                        )
                        self.visualization_button.config(state="normal")

                # 로그 파일 찾기
                logs_folder = os.path.join(latest_result_folder, "logs")
                if os.path.exists(logs_folder):
                    log_files = [
                        f
                        for f in os.listdir(logs_folder)
                        if f.startswith("pipeline_log_") and f.endswith(".md")
                    ]
                    if log_files:
                        log_files.sort(reverse=True)
                        self.latest_log_path = os.path.join(logs_folder, log_files[0])
                        self.log_button.config(state="normal")

        except Exception as e:
            print(f"버튼 업데이트 중 오류: {e}")

    def run_generation_in_thread(self, topic):
        """실제 생성 로직을 별도 스레드에서 실행합니다."""
        try:
            # 실행 모드에 따라 모델 설정
            mode = self.mode_var.get()
            if mode == "Production":
                self.models = PRODUCTION_MODELS
                self.thinking_budgets = PRODUCTION_THINKING_BUDGETS
            else:
                self.models = TEST_MODELS
                self.thinking_budgets = TEST_THINKING_BUDGETS

            # 로깅 세션 시작 및 결과 폴더 생성
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.results_folder = f"results_{mode.lower()}_{session_id}"
            self.logs_folder = os.path.join(self.results_folder, "logs")
            self.viz_folder = os.path.join(self.results_folder, "visualizations")

            # 폴더 생성
            os.makedirs(self.results_folder, exist_ok=True)
            os.makedirs(self.logs_folder, exist_ok=True)
            os.makedirs(self.viz_folder, exist_ok=True)

            self.logger.start_logging(session_id)
            self.logger.add_log(
                "SYSTEM", "=" * 20 + " 보고서 생성 파이프라인 시작 " + "=" * 20
            )

            initial_state = {
                "topic": topic,
                "outline": "",
                "report_content": {},
                "current_report_text": "",
                "review_result": {},
                "review_history": [],
                "review_attempts": 0,
                "formatted_report": "",
                "final_report_with_refs": "",
                "progress_message": "0/6: 파이프라인 시작...",
            }

            final_state = None
            # 스트리밍 방식으로 그래프 실행 및 각 단계별 상태 출력
            for event in self.graph.stream(initial_state, {"recursion_limit": 15}):
                node_name = list(event.keys())[0]
                node_output = event[node_name]

                # 상태 업데이트 내용 출력 (민감 정보나 너무 긴 내용은 생략)
                for key, value in node_output.items():
                    if isinstance(value, str) and len(value) > 300:
                        self.logger.add_log("DEBUG", f"  - {key}: (내용이 길어 생략됨)")
                    elif key not in ["client", "root"]:
                        self.logger.add_log("DEBUG", f"  - {key}: {value}")

                # UI 업데이트는 큐를 통해 전달
                if (
                    "progress_message" in node_output
                    and node_output["progress_message"]
                ):
                    self.progress_queue.put(
                        {"progress_message": node_output["progress_message"]}
                    )

                # 마지막 실행된 노드의 상태를 final_state로 저장
                final_state = node_output

            self.logger.add_log(
                "SYSTEM", "=" * 20 + " 보고서 생성 파이프라인 종료 " + "=" * 20
            )

            if not final_state:
                raise Exception("그래프 실행이 정상적으로 완료되지 않았습니다.")

            final_report_with_refs = final_state.get(
                "final_report_with_refs", "오류: 최종 보고서를 찾을 수 없습니다."
            )

            # 파일 저장
            now = datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")
            report_filename = os.path.join(
                self.results_folder, f"final_report_{date_str}.md"
            )
            self.logger.add_log(
                "INFO", f"[6/6] 보고서 파일 저장 중... -> '{report_filename}'"
            )

            # 최종 통계 정보 출력
            ref_count = (
                final_report_with_refs.count("[^") if final_report_with_refs else 0
            )
            word_count = (
                len(final_report_with_refs.split()) if final_report_with_refs else 0
            )
            self.logger.add_log("INFO", f"최종 보고서 통계:")
            self.logger.add_log("INFO", f"  * 총 단어 수: {word_count}개")
            self.logger.add_log("INFO", f"  * 참고문헌 수: {ref_count}개")
            self.logger.add_log(
                "INFO",
                f"  * 파일 크기: {len(final_report_with_refs.encode('utf-8'))} bytes",
            )

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_report_with_refs)

            # 로그 파일 저장
            full_log_path, node_log_paths = self.logger.save_logs(self.logs_folder)
            self.logger.add_log("SUCCESS", f"전체 로그 파일: {full_log_path}")
            self.logger.add_log("SUCCESS", f"노드별 로그 파일: {len(node_log_paths)}개")
            self.latest_log_path = full_log_path  # 경로 저장

            # 시각화 대시보드 생성
            self.logger.add_log("INFO", "시각화 대시보드 생성 중...")
            try:
                dashboard_path = self.analyzer.create_visualization_dashboard(
                    self.logger, final_state, self.viz_folder
                )
                if dashboard_path:
                    self.logger.add_log(
                        "SUCCESS", f"시각화 대시보드 생성 완료: {dashboard_path}"
                    )
                    self.latest_dashboard_path = dashboard_path  # 경로 저장
                else:
                    self.logger.add_log("WARNING", "시각화 대시보드 생성 실패")
            except Exception as e:
                self.logger.add_log("ERROR", f"시각화 생성 중 오류: {e}")

            # 결과 폴더 정보 로그
            self.logger.add_log("SUCCESS", f"=" * 50)
            self.logger.add_log("SUCCESS", f"🎉 모든 작업이 완료되었습니다!")
            self.logger.add_log("SUCCESS", f"📁 결과 폴더: {self.results_folder}")
            self.logger.add_log(
                "SUCCESS", f"   📄 보고서: {os.path.basename(report_filename)}"
            )
            self.logger.add_log("SUCCESS", f"   📊 시각화: visualizations/")
            self.logger.add_log("SUCCESS", f"   📋 로그: logs/")
            self.logger.add_log("SUCCESS", f"=" * 50)

            # 최종 결과 전달
            self.progress_queue.put({"final_report": final_report_with_refs})

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.logger.add_log("ERROR", f"리포트 생성 중 오류 발생: {e}")
            self.progress_queue.put({"error": f"리포트 생성 중 오류 발생: {e}"})
        finally:
            self.progress_queue.put(
                {
                    "progress_message": "RAG 리포트 생성기 v4 (지능형)",
                    "generation_done": True,
                }
            )

    def _show_report(self, report_text):
        report_window = tk.Toplevel(self.root)
        report_window.title("생성된 리포트 (v4)")
        report_window.geometry("800x600")
        text_area = scrolledtext.ScrolledText(
            report_window, wrap=tk.WORD, font=("맑은 고딕", 10)
        )
        text_area.insert(tk.INSERT, report_text)
        text_area.pack(expand=True, fill="both", padx=10, pady=10)
        text_area.configure(state="disabled")

    def show_latest_visualization(self):
        """최근 생성된 시각화 대시보드를 표시합니다."""
        if not self.latest_dashboard_path or not os.path.exists(
            self.latest_dashboard_path
        ):
            messagebox.showwarning("알림", "표시할 시각화 파일이 없습니다.")
            return

        try:
            # 새 창에서 시각화 표시
            viz_window = tk.Toplevel(self.root)
            viz_window.title("시각화 대시보드")
            viz_window.geometry("1200x800")

            # 이미지 로드 및 표시
            from PIL import Image, ImageTk

            img = Image.open(self.latest_dashboard_path)

            # 창 크기에 맞게 이미지 크기 조정
            img_width, img_height = img.size
            max_width, max_height = 1150, 750

            if img_width > max_width or img_height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            # 스크롤 가능한 캔버스 생성
            canvas = tk.Canvas(viz_window, scrollregion=(0, 0, img.width, img.height))
            canvas.pack(fill=tk.BOTH, expand=True)

            # 이미지 표시
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo  # 가비지 컬렉션 방지

            # 스크롤바 추가
            scrollbar_v = tk.Scrollbar(
                viz_window, orient=tk.VERTICAL, command=canvas.yview
            )
            scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.configure(yscrollcommand=scrollbar_v.set)

            scrollbar_h = tk.Scrollbar(
                viz_window, orient=tk.HORIZONTAL, command=canvas.xview
            )
            scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
            canvas.configure(xscrollcommand=scrollbar_h.set)

        except Exception as e:
            messagebox.showerror("오류", f"시각화 표시 중 오류가 발생했습니다: {e}")
            # PIL이 없는 경우 대안
            try:
                import webbrowser

                webbrowser.open(self.latest_dashboard_path)
            except:
                messagebox.showinfo(
                    "알림",
                    f"시각화 파일을 직접 열어보세요:\n{self.latest_dashboard_path}",
                )

    def show_log_files(self):
        """로그 파일 목록을 표시합니다."""
        try:
            # 로그 파일 목록 가져오기 (새로운 폴더 구조)
            log_files = []

            # 결과 폴더들 스캔
            for folder in os.listdir("."):
                if folder.startswith("results_") and os.path.isdir(folder):
                    logs_folder = os.path.join(folder, "logs")
                    if os.path.exists(logs_folder):
                        for file in os.listdir(logs_folder):
                            if (
                                file.startswith("pipeline_log_")
                                or file.startswith("node_")
                            ) and file.endswith(".md"):
                                log_files.append(os.path.join(logs_folder, file))

            # 기존 루트 폴더의 로그 파일들도 확인 (하위 호환성)
            for file in os.listdir("."):
                if (
                    file.startswith("pipeline_log_") or file.startswith("node_")
                ) and file.endswith(".md"):
                    log_files.append(file)

            if not log_files:
                messagebox.showinfo("알림", "로그 파일이 없습니다.")
                return

            # 로그 파일 선택 창
            log_window = tk.Toplevel(self.root)
            log_window.title("로그 파일 목록")
            log_window.geometry("600x400")

            tk.Label(
                log_window, text="로그 파일을 선택하세요:", font=("Arial", 12)
            ).pack(pady=10)

            # 리스트박스 생성
            listbox = tk.Listbox(log_window, font=("Consolas", 10))
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 로그 파일 목록 추가 (최신 순)
            log_files.sort(reverse=True)
            for file in log_files:
                listbox.insert(tk.END, file)

            # 파일 열기 버튼
            def open_selected_log():
                selection = listbox.curselection()
                if selection:
                    selected_file = listbox.get(selection[0])
                    self._open_log_file(selected_file)

            tk.Button(
                log_window, text="로그 파일 열기", command=open_selected_log
            ).pack(pady=10)

        except Exception as e:
            messagebox.showerror("오류", f"로그 파일 목록 표시 중 오류: {e}")

    def _open_log_file(self, filename):
        """로그 파일을 새 창에서 표시합니다."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

            # 새 창에서 로그 내용 표시
            log_content_window = tk.Toplevel(self.root)
            log_content_window.title(f"로그 내용: {filename}")
            log_content_window.geometry("900x700")

            # 텍스트 에리어 생성
            text_area = scrolledtext.ScrolledText(
                log_content_window, wrap=tk.WORD, font=("Consolas", 9)
            )
            text_area.insert(tk.INSERT, content)
            text_area.pack(expand=True, fill="both", padx=10, pady=10)
            text_area.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("오류", f"로그 파일 열기 중 오류: {e}")

    def _update_status(self, message, color="black"):
        """상태 라벨을 업데이트합니다."""
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = RAGReportGeneratorAppV3(root)
    root.mainloop()
