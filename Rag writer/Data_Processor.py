import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import re
import uuid

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


class DataProcessorApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("데이터 프로세서 (파서 + 빌더)")
        self.root.geometry("300x150")

        self.label = tk.Label(
            self.root, text="처리할 마크다운 파일을 선택하세요.", wraplength=280
        )
        self.label.pack(pady=20)

        self.process_button = tk.Button(
            self.root,
            text="파일 선택 및 처리 시작",
            command=self.select_files_and_process,
        )
        self.process_button.pack(pady=10)

    def select_files_and_process(self):
        file_paths = filedialog.askopenfilenames(
            title="마크다운 파일 선택",
            filetypes=(("Markdown files", "*.md"), ("All files", "*.*")),
        )

        if not file_paths:
            return

        report_lines = []
        total_files = len(file_paths)

        for i, md_path in enumerate(file_paths):
            self.root.title(f"데이터 프로세서 - 처리 중... ({i+1}/{total_files})")
            self.root.update_idletasks()

            try:
                # 파일을 한 번에 처리하여 최종 데이터를 생성
                final_data = self.process_single_file(md_path)

                # 최종 결과 저장
                output_filename = os.path.splitext(md_path)[0] + "_processed.json"
                with open(output_filename, "w", encoding="utf-8") as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=2)

                enriched_count = sum(
                    1 for item in final_data if item.get("reference_text")
                )
                report_lines.append(
                    f"✅ {os.path.basename(md_path)}:\n"
                    f"    - 총 {len(final_data)}개 문장(Chunk) 생성.\n"
                    f"    - 그 중 {enriched_count}개에 참고문헌 연결 완료.\n"
                    f"    - '{os.path.basename(output_filename)}'로 저장됨."
                )

            except Exception as e:
                report_lines.append(
                    f"❌ {os.path.basename(md_path)} 처리 실패:\n    - 오류: {e}"
                )

        self.root.title("데이터 프로세서 (파서 + 빌더)")
        messagebox.showinfo("처리 완료", "\n\n".join(report_lines))

    def _parse_references(self, lines):
        """마크다운 라인에서 '참고 자료' 섹션을 파싱하여 딕셔너리로 반환합니다."""
        references = {}
        is_ref_section = False
        for line in lines:
            if "#### **참고 자료**" in line:
                is_ref_section = True
                continue
            if not is_ref_section:
                continue

            match = re.match(r"^\s*(\d+)\s*[.)]\s*(.*)", line)
            if match:
                ref_num = match.group(1)
                ref_text = match.group(2).strip()
                references[ref_num] = ref_text
        return references

    def _is_valid_ref_num(self, s):
        """레퍼런스 번호가 유효한지(2000 미만의 숫자로 시작하는지) 확인합니다."""
        try:
            first_num = s.replace(",", " ").replace("-", " ").split()[0]
            return int(first_num) < 2000
        except (ValueError, IndexError):
            return False

    def process_single_file(self, md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 1. 참고문헌 목록을 먼저 파싱
        references_map = self._parse_references(lines)

        # 2. 본문 내용을 파싱하며 고유 ID와 함께 데이터 청크 생성
        chunks = []
        current_headers = []
        stop_parsing = False

        for line in lines:
            line = line.strip()

            if "#### **참고 자료**" in line:
                stop_parsing = True

            if stop_parsing or not line:
                continue

            header_match = re.match(r"^(#+)\s+(.*)", line)
            if header_match:
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                while len(current_headers) >= level:
                    current_headers.pop()
                current_headers.append(header_text)
                continue

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

                    # 문장에서 레퍼런스 번호 추출 시도
                    temp_ref_num = None
                    cleaned_sentence = sentence

                    match_end = re.match(r"^(.*?)[\s,.]*([\d,-]+)$", sentence)
                    if match_end:
                        potential_sent = match_end.group(1).strip()
                        potential_ref = match_end.group(2)
                        if potential_sent and self._is_valid_ref_num(potential_ref):
                            cleaned_sentence = potential_sent
                            temp_ref_num = potential_ref

                    if not temp_ref_num:
                        match_start = re.match(r"^([\d,-]+)[\s,.]*(.*)", sentence)
                        if match_start:
                            potential_ref = match_start.group(1)
                            potential_sent = match_start.group(2).strip()
                            if potential_sent and self._is_valid_ref_num(potential_ref):
                                cleaned_sentence = potential_sent
                                temp_ref_num = potential_ref

                    # 레퍼런스 텍스트 연결
                    reference_text = None
                    if temp_ref_num:
                        main_ref_num = re.split(r"[, -]", temp_ref_num)[0]
                        if main_ref_num in references_map:
                            reference_text = references_map[main_ref_num]

                    if cleaned_sentence:
                        chunk = {
                            "chunk_id": str(uuid.uuid4()),
                            "file_path": os.path.basename(md_path),
                            "headers": current_headers.copy(),
                            "sentence": cleaned_sentence,
                            "reference_text": reference_text,  # reference_text가 없으면 None
                        }
                        chunks.append(chunk)

        return chunks


if __name__ == "__main__":
    root = tk.Tk()
    app = DataProcessorApp(root)
    root.mainloop()
