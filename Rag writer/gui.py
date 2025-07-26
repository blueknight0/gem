import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext
import threading
import queue
from services import PreprocessorService, ReportGeneratorService
import os


class MainApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("통합 RAG 리포트 생성기")
        self.parent.geometry("600x500")

        self.progress_queue = queue.Queue()

        # 서비스 클래스 인스턴스화
        self.preprocessor = PreprocessorService(status_callback=self.update_status)
        self.reporter = ReportGeneratorService(progress_queue=self.progress_queue)

        # 탭 컨트롤 생성
        self.notebook = ttk.Notebook(self)

        # 탭 생성
        self.preprocess_tab = ttk.Frame(self.notebook)
        self.report_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.preprocess_tab, text=" DB 생성 ")
        self.notebook.add(self.report_tab, text=" 보고서 생성 ")
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # 각 탭의 위젯 생성
        self._create_preprocess_widgets()
        self._create_report_widgets()

        # 상태바
        self.status_bar = tk.Label(
            self, text="준비됨", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.pack(expand=True, fill="both")

        # 큐 처리 시작
        self.process_queue()

    def _create_preprocess_widgets(self):
        frame = ttk.LabelFrame(self.preprocess_tab, text="전처리기", padding=(10, 10))
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        label = ttk.Label(
            frame, text="마크다운 파일을 선택하여 벡터 DB를 생성합니다.", wraplength=400
        )
        label.pack(pady=10)

        button = ttk.Button(
            frame, text="파일 선택 및 DB 생성", command=self.run_preprocessing
        )
        button.pack(pady=20, ipadx=10, ipady=5)

    def _create_report_widgets(self):
        frame = ttk.LabelFrame(self.report_tab, text="리포트 생성기", padding=(10, 10))
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        # DB 로드
        db_frame = ttk.Frame(frame)
        db_frame.pack(fill=tk.X, pady=5)
        self.db_load_button = ttk.Button(
            db_frame, text="벡터 DB 선택", command=self.load_vector_db
        )
        self.db_load_button.pack(side=tk.LEFT, padx=(0, 5))
        self.db_status_label = ttk.Label(
            db_frame, text="DB가 로드되지 않았습니다.", foreground="red"
        )
        self.db_status_label.pack(side=tk.LEFT)

        # 작성 요청 입력
        topic_frame = ttk.Frame(frame)
        topic_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(topic_frame, text="작성 요청:").pack(side=tk.TOP, anchor=tk.W)
        self.topic_entry = scrolledtext.ScrolledText(
            topic_frame, height=5, wrap=tk.WORD, font=("맑은 고딕", 10)
        )
        self.topic_entry.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))

        # 실행 모드
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="모드:").pack(side=tk.LEFT, padx=(0, 5))
        self.mode_var = tk.StringVar(value="Production")
        prod_radio = ttk.Radiobutton(
            mode_frame, text="Production", variable=self.mode_var, value="Production"
        )
        prod_radio.pack(side=tk.LEFT)
        test_radio = ttk.Radiobutton(
            mode_frame, text="Test", variable=self.mode_var, value="Test"
        )
        test_radio.pack(side=tk.LEFT, padx=5)

        bypass_radio = ttk.Radiobutton(
            mode_frame,
            text="Extreme (익스트림)",
            variable=self.mode_var,
            value="Bypass",
        )
        bypass_radio.pack(side=tk.LEFT, padx=5)

        # 생성 버튼
        self.generate_button = ttk.Button(
            frame,
            text="리포트 생성 시작",
            command=self.run_report_generation,
            state="disabled",
        )
        self.generate_button.pack(pady=20, ipadx=10, ipady=5)

    def run_preprocessing(self):
        file_paths = filedialog.askopenfilenames(
            title="마크다운 파일 선택",
            filetypes=(("Markdown files", "*.md"), ("All files", "*.*")),
        )
        if not file_paths:
            return

        db_name = simpledialog.askstring(
            "DB 이름 설정", "DB 파일 이름을 입력하세요:", initialvalue="vector_db"
        )
        if not db_name:
            return

        def task():
            try:
                report = self.preprocessor.process_files_and_create_db(
                    file_paths, db_name
                )
                messagebox.showinfo("처리 완료", report)
            except Exception as e:
                messagebox.showerror("오류", f"전처리 중 오류 발생: {e}")
            finally:
                self.update_status("준비됨")

        threading.Thread(target=task, daemon=True).start()

    def load_vector_db(self):
        faiss_path = filedialog.askopenfilename(
            title="FAISS 인덱스 파일(.faiss) 선택",
            filetypes=(("FAISS Index Files", "*.faiss"),),
        )
        if not faiss_path:
            return

        try:
            total_vectors = self.reporter.load_vector_db(faiss_path)
            self.db_status_label.config(
                text=f"로드됨: {os.path.basename(faiss_path)} ({total_vectors} 벡터)",
                foreground="green",
            )
            self.generate_button.config(state="normal")
            messagebox.showinfo(
                "성공", f"총 {total_vectors}개의 벡터가 포함된 DB를 로드했습니다."
            )
        except Exception as e:
            self.db_status_label.config(text="DB 로드 실패", foreground="red")
            self.generate_button.config(state="disabled")
            messagebox.showerror("DB 로드 실패", str(e))

    def run_report_generation(self):
        topic = self.topic_entry.get("1.0", tk.END).strip()
        if not topic:
            messagebox.showwarning("입력 오류", "작성 요청 내용을 입력해주세요.")
            return

        self.generate_button.config(state="disabled")
        mode = self.mode_var.get()

        threading.Thread(
            target=self.reporter.run_generation_pipeline,
            args=(topic, mode),
            daemon=True,
        ).start()

    def update_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)

    def process_queue(self):
        try:
            message = self.progress_queue.get_nowait()
            if "progress_message" in message:
                self.update_status(message["progress_message"])
            if "final_report" in message:
                self._show_report(message["final_report"])
                messagebox.showinfo("생성 완료", "리포트 생성이 완료되었습니다.")
                self.update_status("리포트 생성 완료")
            if "error" in message:
                messagebox.showerror("오류", message["error"])
                self.update_status("오류 발생", "red")
            if "generation_done" in message:
                self.generate_button.config(state="normal")
                self.update_status("준비됨")

        except queue.Empty:
            pass
        finally:
            self.parent.after(100, self.process_queue)

    def _show_report(self, report_text):
        report_window = tk.Toplevel(self.parent)
        report_window.title("생성된 리포트")
        report_window.geometry("800x600")
        text_area = scrolledtext.ScrolledText(
            report_window, wrap=tk.WORD, font=("맑은 고딕", 10)
        )
        text_area.insert(tk.INSERT, report_text)
        text_area.pack(expand=True, fill="both", padx=10, pady=10)
        text_area.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    MainApp(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
