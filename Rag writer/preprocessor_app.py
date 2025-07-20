import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import json
import re
import uuid
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv
import warnings

# pecab 라이브러리에서 발생하는 특정 런타임 경고를 무시합니다.
warnings.filterwarnings(
    "ignore", category=RuntimeWarning, message="overflow encountered in scalar add"
)

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

# 필수 라이브러리 확인 및 설치
required_packages = {
    "google.generativeai": "google-generativeai",
    "faiss": "faiss-cpu",
    "numpy": "numpy",
    "dotenv": "python-dotenv",
}

for lib, package in required_packages.items():
    if lib == "dotenv":
        lib = "dotenv"  # 모듈 이름이 달라서 예외처리
    try:
        __import__(lib)
    except ImportError:
        print(f"{package} 라이브러리가 설치되어 있지 않습니다. 설치를 시작합니다.")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(
                f"오류: {package} 설치에 실패했습니다. 수동으로 설치해주세요: pip install {package}"
            )
            sys.exit(1)


# API 키 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    messagebox.showerror(
        "오류",
        "GEMINI_API_KEY 환경 변수를 찾을 수 없습니다.\n.env 파일에 키를 설정해주세요.",
    )
    sys.exit(1)
genai.configure(api_key=GOOGLE_API_KEY)


class IntegratedPreprocessorApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("통합 전처리기")
        self.root.geometry("300x150")

        self.label = tk.Label(
            self.root, text="처리할 마크다운 파일을 선택하세요.", wraplength=280
        )
        self.label.pack(pady=20)

        self.process_button = tk.Button(
            self.root,
            text="파일 선택 및 DB 생성",
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

        db_name = simpledialog.askstring(
            "DB 이름 설정",
            "벡터 DB 파일의 기본 이름을 입력하세요 (예: my_db):",
            initialvalue="vector_db",
        )
        if not db_name:
            messagebox.showinfo("취소됨", "DB 이름이 입력되지 않아 작업을 취소합니다.")
            return

        try:
            self.root.title("전처리 진행 중...")
            self.root.update_idletasks()

            # 1. 마크다운 파일 파싱 및 데이터 청크 생성
            all_chunks, report_lines = self._process_markdown_files(file_paths)

            if not all_chunks:
                messagebox.showwarning(
                    "경고", "선택한 파일에서 처리할 데이터를 찾지 못했습니다."
                )
                return

            # 2. 벡터 DB 생성
            num_vectors, faiss_path, json_path = self._create_vector_db(
                all_chunks, db_name
            )

            # 최종 보고
            report_lines.append("\n--- 벡터 DB 생성 결과 ---")
            report_lines.append(
                f"✅ 총 {num_vectors}개의 벡터를 생성하여 DB 구축 완료."
            )
            report_lines.append(
                f"✅ '{os.path.basename(faiss_path)}' 와 '{os.path.basename(json_path)}' 파일 저장 완료."
            )
            messagebox.showinfo("처리 완료", "\n".join(report_lines))

        except Exception as e:
            messagebox.showerror("전체 프로세스 실패", f"오류 발생: {e}")
        finally:
            self.root.title("통합 전처리기")

    def _process_markdown_files(self, file_paths):
        all_chunks = []
        report_lines = ["--- 마크다운 파싱 결과 ---"]
        total_files = len(file_paths)

        for i, md_path in enumerate(file_paths):
            self.root.title(f"파싱 중... ({i+1}/{total_files})")
            self.root.update_idletasks()
            try:
                chunks = self._process_single_file(md_path)
                all_chunks.extend(chunks)

                enriched_count = sum(1 for item in chunks if item.get("reference_text"))
                report_lines.append(
                    f"✅ {os.path.basename(md_path)}:\n"
                    f"    - {len(chunks)}개 문장(Chunk) 생성.\n"
                    f"    - {enriched_count}개에 참고문헌 연결."
                )
            except Exception as e:
                report_lines.append(f"❌ {os.path.basename(md_path)} 처리 실패: {e}")
        return all_chunks, report_lines

    def _parse_references(self, lines):
        references = {}
        is_ref_section = False
        for line in lines:
            if "#### **참고 자료**" in line:
                is_ref_section = True
                continue
            if not is_ref_section:
                continue
            match = re.match(r"^\s*(\d+)\s*[-.)]\s*(.*)", line)
            if match:
                ref_num = match.group(1)
                ref_text = match.group(2).strip()
                references[ref_num] = ref_text
        return references

    def _is_valid_ref_num(self, s):
        try:
            first_num = s.replace(",", " ").replace("-", " ").split()[0]
            return int(first_num) < 2000
        except (ValueError, IndexError):
            return False

    def _process_single_file(self, md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        references_map = self._parse_references(lines)
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
                            "reference_text": reference_text,
                        }
                        chunks.append(chunk)
        return chunks

    def _create_vector_db(self, all_data_items, db_name):
        contents_to_embed = self._prepare_contents(all_data_items)
        embeddings = self._get_embeddings(contents_to_embed)
        faiss_path, json_path = self._build_and_save_faiss_index(
            embeddings, all_data_items, db_name
        )
        return len(embeddings), faiss_path, json_path

    def _prepare_contents(self, data_items):
        contents = []
        for item in data_items:
            sentence = item.get("sentence", "")
            ref_text = item.get("reference_text")

            # 컨텐츠 생성
            if ref_text:
                contents.append(f"문장: {sentence}\n\n출처: {ref_text}")
            else:
                contents.append(sentence)

        return contents

    def _get_embeddings(self, contents):
        batch_size = 100
        all_embeddings = []
        total_count = len(contents)

        for i in range(0, total_count, batch_size):
            batch_contents = contents[i : i + batch_size]

            self.root.title(f"임베딩 중... ({i+len(batch_contents)}/{total_count})")
            self.root.update_idletasks()

            result = genai.embed_content(
                model="models/gemini-embedding-001",  # 최신 모델 사용
                content=batch_contents,
                task_type="RETRIEVAL_DOCUMENT",
            )
            # 3072차원(기본값)은 이미 정규화되어 있으므로 별도 처리 불필요
            all_embeddings.extend(result["embedding"])

        return np.array(all_embeddings, dtype="float32")

    def _build_and_save_faiss_index(self, embeddings, data_items, db_name):
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        faiss_path = f"{db_name}.faiss"
        json_path = f"{db_name}_data.json"

        faiss.write_index(index, faiss_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_items, f, ensure_ascii=False, indent=2)

        return faiss_path, json_path


if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedPreprocessorApp(root)
    root.mainloop()
