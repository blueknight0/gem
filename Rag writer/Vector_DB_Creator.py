import sys
import subprocess
import os

# 필수 라이브러리 확인 및 설치
required_packages = {
    "google.generativeai": "google-generativeai",
    "faiss": "faiss-cpu",
    "numpy": "numpy",
}

for lib, package in required_packages.items():
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

import tkinter as tk
from tkinter import filedialog, messagebox
import json
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv

# API 키 로드 (generate_report.py 참조)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    messagebox.showerror(
        "오류",
        "GEMINI_API_KEY 환경 변수를 찾을 수 없습니다.\n.env 파일에 키를 설정해주세요.",
    )
    sys.exit(1)
genai.configure(api_key=GOOGLE_API_KEY)


class VectorDBCreatorApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("벡터 DB 생성기")
        self.root.geometry("300x150")

        self.label = tk.Label(
            self.root, text="*_processed.json 파일을 선택하세요.", wraplength=280
        )
        self.label.pack(pady=20)

        self.build_button = tk.Button(
            self.root,
            text="파일 선택 및 DB 생성",
            command=self.select_files_and_create_db,
        )
        self.build_button.pack(pady=10)

    def select_files_and_create_db(self):
        processed_json_paths = filedialog.askopenfilenames(
            title="*_processed.json 파일 선택",
            filetypes=(
                ("Processed JSON files", "*_processed.json"),
                ("All files", "*.*"),
            ),
        )
        if not processed_json_paths:
            return

        try:
            self.root.title("DB 생성 중...")
            self.root.update_idletasks()

            all_data_items = []
            for file_path in processed_json_paths:
                with open(file_path, "r", encoding="utf-8") as f:
                    all_data_items.extend(json.load(f))

            if not all_data_items:
                messagebox.showwarning(
                    "경고", "선택한 파일에 처리할 데이터가 없습니다."
                )
                return

            texts_to_embed = self._prepare_texts(all_data_items)
            embeddings = self._get_embeddings(texts_to_embed)

            self._build_and_save_faiss_index(embeddings, all_data_items)

            messagebox.showinfo(
                "성공",
                f"총 {len(embeddings)}개의 벡터를 생성하여 DB를 구축했습니다.\n"
                f"vector_db.faiss 와 vector_db_data.json 파일이 저장되었습니다.",
            )

        except Exception as e:
            messagebox.showerror("DB 생성 실패", f"오류 발생: {e}")
        finally:
            self.root.title("벡터 DB 생성기")

    def _prepare_texts(self, data_items):
        """임베딩할 텍스트를 준비합니다."""
        texts = []
        for item in data_items:
            sentence = item.get("sentence", "")
            ref_text = item.get("reference_text")

            if ref_text:
                # 옵션 B: 문장과 레퍼런스를 결합하여 컨텍스트 강화
                texts.append(f"문장: {sentence}\n\n출처: {ref_text}")
            else:
                texts.append(sentence)
        return texts

    def _get_embeddings(self, texts):
        """Google API를 사용하여 텍스트 임베딩을 가져옵니다."""

        # API는 배치 당 100개까지 처리 가능
        batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            # task_type을 지정해야 성능이 향상됨
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=batch_texts,
                task_type="RETRIEVAL_DOCUMENT",
            )
            all_embeddings.extend(result["embedding"])
            # 진행 상황 표시 (선택 사항)
            self.root.title(f"DB 생성 중... ({i+batch_size}/{len(texts)})")
            self.root.update_idletasks()

        return np.array(all_embeddings, dtype="float32")

    def _build_and_save_faiss_index(self, embeddings, data_items):
        """FAISS 인덱스를 빌드하고 파일로 저장합니다."""
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        # FAISS 인덱스 저장
        faiss.write_index(index, "vector_db.faiss")

        # 원본 데이터 저장
        with open("vector_db_data.json", "w", encoding="utf-8") as f:
            json.dump(data_items, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = VectorDBCreatorApp(root)
    root.mainloop()
