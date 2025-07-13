import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import re

# kss 라이브러리 설치 확인 및 자동 설치
try:
    import kss
except ImportError:
    print("kss 라이브러리가 설치되어 있지 않습니다. 설치를 시도합니다.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kss==3.7.3"])
        print("kss 라이브러리 설치를 완료했습니다.")
        import kss
    except Exception as e:
        messagebox.showerror(
            "오류",
            f"kss 라이브러리 설치에 실패했습니다. 수동으로 설치해주세요: pip install kss==3.7.3\n\n오류: {e}",
        )
        sys.exit(1)


class MDParserApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("MD 파서")
        self.root.geometry("300x150")

        self.label = tk.Label(
            self.root, text="파싱할 마크다운 파일을 선택하세요.", wraplength=280
        )
        self.label.pack(pady=20)

        self.parse_button = tk.Button(
            self.root,
            text="파일 선택 및 파싱 시작",
            command=self.select_files_and_parse,
        )
        self.parse_button.pack(pady=10)

    def select_files_and_parse(self):
        """파일 선택 대화상자를 열고 파싱 프로세스를 시작합니다."""
        file_paths = filedialog.askopenfilenames(
            title="마크다운 파일 선택",
            filetypes=(("Markdown files", "*.md"), ("All files", "*.*")),
        )

        if not file_paths:
            return

        report_lines = []
        total_files = len(file_paths)

        for i, md_path in enumerate(file_paths):
            self.root.title(f"MD 파서 - 처리 중... ({i+1}/{total_files})")
            self.root.update_idletasks()

            try:
                parsed_data, sentence_count, ref_count = self.parse_md_file(md_path)

                # JSON 파일로 저장
                json_path = os.path.splitext(md_path)[0] + ".json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                report_lines.append(
                    f"✅ {os.path.basename(md_path)}:\n    - 문장: {sentence_count}개\n    - 레퍼런스: {ref_count}개"
                )

            except Exception as e:
                report_lines.append(
                    f"❌ {os.path.basename(md_path)} 파싱 실패:\n    - 오류: {e}"
                )

        self.root.title("MD 파서")
        messagebox.showinfo("파싱 완료", "\n\n".join(report_lines))

    def _is_valid_ref_num(self, s):
        """레퍼런스 번호가 유효한지(2000 미만의 숫자로 시작하는지) 확인하는 헬퍼 함수"""
        try:
            first_num = s.replace(",", " ").replace("-", " ").split()[0]
            return int(first_num) < 2000
        except (ValueError, IndexError):
            return False

    def parse_md_file(self, md_path):
        """마크다운 파일을 파싱하여 문장, 목차, 레퍼런스를 추출합니다."""
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        parsed_data = []
        current_headers = []
        stop_parsing = False

        for line in lines:
            line = line.strip()

            # "참고 자료" 섹션부터는 파싱 중단
            if "#### **참고 자료**" in line:
                stop_parsing = True

            if stop_parsing or not line:
                continue

            # 목차(헤더) 처리
            header_match = re.match(r"^(#+)\s+(.*)", line)
            if header_match:
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()

                while len(current_headers) >= level:
                    current_headers.pop()
                current_headers.append(header_text)
                continue

            # 구분선 등은 건너뜀
            if line.startswith(("---", ":", "`")):
                continue

            texts_to_process = []
            if line.startswith("|"):
                cells = line.strip("|").split("|")
                texts_to_process.extend(
                    [cell.strip() for cell in cells if cell.strip()]
                )
            else:
                texts_to_process.append(line)

            for text in texts_to_process:
                try:
                    sentences = kss.split_sentences(text)
                except Exception:
                    sentences = [text]

                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    # 1. 숫자만 있는 문장은 이전 문장의 레퍼런스로 처리
                    if (
                        re.fullmatch(r"[\d,-]+", sentence)
                        and parsed_data
                        and parsed_data[-1]["reference"] is None
                    ):
                        if self._is_valid_ref_num(sentence):
                            parsed_data[-1]["reference"] = sentence
                        continue

                    cleaned_sentence = sentence
                    reference = None

                    # 2. 문장 끝에서 레퍼런스 탐지
                    match_end = re.match(r"^(.*?)[\s,.]*([\d,-]+)$", sentence)
                    if match_end:
                        potential_sent = match_end.group(1).strip()
                        potential_ref = match_end.group(2)
                        if potential_sent and not re.search(r"\d$", potential_sent):
                            if self._is_valid_ref_num(potential_ref):
                                cleaned_sentence = potential_sent
                                reference = potential_ref

                    # 3. 문장 시작에서 레퍼런스 탐지 (끝에서 못 찾았을 경우)
                    if reference is None:
                        match_start = re.match(r"^([\d,-]+)[\s,.]*(.*)", sentence)
                        if match_start:
                            potential_ref = match_start.group(1)
                            potential_sent = match_start.group(2).strip()
                            if potential_sent and not re.fullmatch(
                                r"[\d,-]+", potential_sent
                            ):
                                if self._is_valid_ref_num(potential_ref):
                                    cleaned_sentence = potential_sent
                                    reference = potential_ref

                    if cleaned_sentence:
                        data_entry = {
                            "file_path": os.path.basename(md_path),
                            "headers": current_headers.copy(),
                            "sentence": cleaned_sentence,
                            "reference": reference,
                        }
                        parsed_data.append(data_entry)

        # 최종 결과에서 레퍼런스 총 개수 계산
        ref_count = sum(1 for d in parsed_data if d["reference"] is not None)
        return parsed_data, len(parsed_data), ref_count


if __name__ == "__main__":
    root = tk.Tk()
    app = MDParserApp(root)
    root.mainloop()
