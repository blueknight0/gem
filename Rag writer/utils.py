import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.font_manager as fm
import re  # Added for reference count calculation


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

            # 참고문헌 개수 정확하게 세기
            ref_count = 0
            if "## 참고문헌" in final_report:
                ref_section = final_report.split("## 참고문헌")[1]
                # 정규식을 사용하여 "1. ", "2. " 등과 같은 패턴을 찾음
                ref_count = len(re.findall(r"^\d+\.\s", ref_section, re.MULTILINE))

            data["reference_stats"] = {
                "total_references": ref_count,
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

        # 목표치 설정 (예시)
        TARGET_WORDS = 5000  # 목표 단어 수
        TARGET_REFS = 20  # 목표 참고문헌 수

        # 품질 점수 계산 (0-100 스케일, 목표치 대비 달성률)
        word_score = min((total_words / TARGET_WORDS) * 100, 100)
        ref_score = min((total_refs / TARGET_REFS) * 100, 100)

        # 전체 품질은 두 점수의 평균으로 계산하되, 둘 중 하나라도 0이면 전체도 0으로 처리
        overall_score = 0
        if word_score > 0 and ref_score > 0:
            overall_score = (word_score + ref_score) / 2
        elif word_score > 0:
            overall_score = word_score / 2
        elif ref_score > 0:
            overall_score = ref_score / 2

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
