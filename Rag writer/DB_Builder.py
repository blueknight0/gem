import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import re


class DBBuilderApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("DB 빌더")
        self.root.geometry("300x150")

        self.label = tk.Label(
            self.root, text="처리할 JSON 파일을 선택하세요.", wraplength=280
        )
        self.label.pack(pady=20)

        self.build_button = tk.Button(
            self.root,
            text="파일 선택 및 DB 빌드 시작",
            command=self.select_files_and_build,
        )
        self.build_button.pack(pady=10)

    def select_files_and_build(self):
        """JSON 파일 선택 대화상자를 열고 빌드 프로세스를 시작합니다."""
        json_paths = filedialog.askopenfilenames(
            title="JSON 파일 선택",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )

        if not json_paths:
            return

        report_lines = []
        total_files = len(json_paths)

        for i, json_path in enumerate(json_paths):
            self.root.title(f"DB 빌더 - 처리 중... ({i+1}/{total_files})")
            self.root.update_idletasks()

            try:
                # 1. 원본 MD 파일 경로 찾기
                base_name = os.path.splitext(json_path)[0]
                md_path = base_name + ".md"

                if not os.path.exists(md_path):
                    report_lines.append(
                        f"⚠️ {os.path.basename(json_path)}: 원본 MD 파일({os.path.basename(md_path)})을 찾을 수 없습니다. 건너뜁니다."
                    )
                    continue

                # 2. 참고 자료 파싱
                references = self.parse_references(md_path)

                # 3. JSON 데이터와 참고자료 결합
                final_data = self.enrich_data(json_path, references)

                # 4. 최종 파일 저장
                final_json_path = base_name + "_final.json"
                with open(final_json_path, "w", encoding="utf-8") as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=2)

                enriched_count = sum(
                    1
                    for item in final_data
                    if "reference_text" in item and item["reference_text"]
                )
                report_lines.append(
                    f"✅ {os.path.basename(json_path)}:\n    - {enriched_count}개 문장에 레퍼런스 정보 추가 완료.\n    - '{os.path.basename(final_json_path)}' 로 저장됨."
                )

            except Exception as e:
                report_lines.append(
                    f"❌ {os.path.basename(json_path)} 처리 실패:\n    - 오류: {e}"
                )

        self.root.title("DB 빌더")
        messagebox.showinfo("빌드 완료", "\n\n".join(report_lines))

    def parse_references(self, md_path):
        """마크다운 파일에서 '참고 자료' 섹션을 파싱하여 딕셔너리로 반환합니다."""
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        references = {}
        is_ref_section = False
        for line in lines:
            if "#### **참고 자료**" in line:
                is_ref_section = True
                continue

            if not is_ref_section:
                continue

            # 레퍼런스 형식: "1. 내용..." 또는 "1) 내용..."
            match = re.match(r"^\s*(\d+)\s*[.)]\s*(.*)", line)
            if match:
                ref_num = match.group(1)
                ref_text = match.group(2).strip()
                references[ref_num] = ref_text

        return references

    def enrich_data(self, json_path, references):
        """JSON 데이터를 로드하고, 레퍼런스 정보를 추가(enrich)합니다."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            ref_num_str = item.get("reference")
            if ref_num_str:
                # 레퍼런스가 "31, 32" 처럼 복합적인 경우 첫 번째 숫자만 사용
                main_ref_num = re.split(r"[, -]", ref_num_str)[0]

                if main_ref_num in references:
                    item["reference_text"] = references[main_ref_num]

        return data


if __name__ == "__main__":
    root = tk.Tk()
    app = DBBuilderApp(root)
    root.mainloop()
