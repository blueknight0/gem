import os
import json
import re
import uuid
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv
import warnings
import kss
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from sklearn.cluster import KMeans
from google.genai import types
from datetime import datetime

import config
from utils import ConsoleLogger, ReportAnalyzer

# pecab 라이브러리에서 발생하는 특정 런타임 경고를 무시합니다.
warnings.filterwarnings(
    "ignore", category=RuntimeWarning, message="overflow encountered in scalar add"
)


class PreprocessorService:
    def __init__(self, status_callback=None):
        """
        초기화 메서드.
        status_callback: GUI의 상태를 업데이트하기 위한 콜백 함수.
        """
        self.status_callback = status_callback
        self._configure_api()

    def _configure_api(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY를 .env 파일에서 찾을 수 없습니다.")
        genai.configure(api_key=api_key)

    def _update_status(self, message):
        """상태 업데이트 콜백을 호출합니다."""
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

    def process_files_and_create_db(self, file_paths, db_name):
        """
        여러 마크다운 파일을 처리하여 벡터 DB를 생성하는 메인 메서드.
        """
        # 1. 마크다운 파일 파싱 및 데이터 청크 생성
        all_chunks, report_lines = self._process_markdown_files(file_paths)

        if not all_chunks:
            raise ValueError("선택한 파일에서 처리할 데이터를 찾지 못했습니다.")

        # 2. 벡터 DB 생성
        num_vectors, faiss_path, json_path = self._create_vector_db(all_chunks, db_name)

        # 3. 최종 보고
        report_lines.append("\n--- 벡터 DB 생성 결과 ---")
        report_lines.append(f"✅ 총 {num_vectors}개의 벡터를 생성하여 DB 구축 완료.")
        report_lines.append(
            f"✅ '{os.path.basename(faiss_path)}' 와 '{os.path.basename(json_path)}' 파일 저장 완료."
        )

        return "\n".join(report_lines)

    def _process_markdown_files(self, file_paths):
        all_chunks = []
        report_lines = ["--- 마크다운 파싱 결과 ---"]
        total_files = len(file_paths)

        for i, md_path in enumerate(file_paths):
            self._update_status(f"파싱 중... ({i+1}/{total_files})")
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

            self._update_status(f"임베딩 중... ({i+len(batch_contents)}/{total_count})")

            result = genai.embed_content(
                model=config.EMBEDDING_MODEL,
                content=batch_contents,
                task_type="RETRIEVAL_DOCUMENT",
            )
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


class ReportGeneratorService:
    def __init__(self, progress_queue=None):
        self.progress_queue = progress_queue
        self.index = None
        self.db_data = None
        self.all_vectors = None
        # self.client는 더 이상 사용하지 않음
        self.generative_model = None
        self.embedding_model = None
        self.chunk_id_map = {}
        self.logger = ConsoleLogger()
        self.analyzer = ReportAnalyzer()
        self.models = {}
        self.thinking_budgets = {}
        self.results_folder = None
        self.logs_folder = None
        self.viz_folder = None
        self.graph = self._build_graph()
        self._configure_api()

    def _configure_api(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY를 .env 파일에서 찾을 수 없습니다.")
        genai.configure(api_key=api_key)
        # 모델 인스턴스 생성
        self.embedding_model = genai.GenerativeModel(config.EMBEDDING_MODEL)

    def _update_progress(self, message):
        if self.progress_queue:
            self.progress_queue.put({"progress_message": message})
        else:
            print(message)

    def load_vector_db(self, faiss_path):
        db_name = os.path.basename(faiss_path).replace(".faiss", "")
        data_path = os.path.join(os.path.dirname(faiss_path), f"{db_name}_data.json")

        if not os.path.exists(data_path):
            raise FileNotFoundError(
                f"매칭되는 데이터 파일(.json)을 찾을 수 없습니다.\n경로: {data_path}"
            )

        self.index = faiss.read_index(faiss_path)
        with open(data_path, "r", encoding="utf-8") as f:
            self.db_data = json.load(f)

        self.all_vectors = np.array(
            [self.index.reconstruct(i) for i in range(self.index.ntotal)]
        ).astype("float32")
        self.chunk_id_map = {
            item["chunk_id"]: item
            for item in self.db_data
            if "chunk_id" in item and item.get("reference_text")
        }

        total_chunks = len(self.db_data)
        with_references = len(self.chunk_id_map)

        print(f"\n=== Vector DB 로드 완료: {os.path.basename(faiss_path)} ===")
        print(f"  - 전체 청크: {total_chunks}")
        print(f"  - 참고문헌 있는 청크: {with_references}")
        print(f"  - 참고문헌 비율: {with_references/total_chunks*100:.1f}%")
        print("=" * 40)

        return self.index.ntotal

    def run_generation_pipeline(self, topic, mode):
        try:
            if mode == "Production":
                self.models = config.PRODUCTION_MODELS
                self.thinking_budgets = config.PRODUCTION_THINKING_BUDGETS
            else:
                self.models = config.TEST_MODELS
                self.thinking_budgets = config.TEST_THINKING_BUDGETS

            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.results_folder = f"results_{mode.lower()}_{session_id}"
            self.logs_folder = os.path.join(self.results_folder, "logs")
            self.viz_folder = os.path.join(self.results_folder, "visualizations")

            os.makedirs(self.results_folder, exist_ok=True)
            os.makedirs(self.logs_folder, exist_ok=True)
            os.makedirs(self.viz_folder, exist_ok=True)

            self.logger.start_logging(session_id)
            self.logger.add_log(
                "SYSTEM", "=" * 20 + " 보고서 생성 파이프라인 시작 " + "=" * 20
            )

            initial_state = ReportState(
                topic=topic,
                outline="",
                report_content={},
                current_report_text="",
                review_result={},
                review_history=[],
                review_attempts=0,
                formatted_report="",
                final_report_with_refs="",
                progress_message="0/6: 파이프라인 시작...",
            )

            final_state = None
            for event in self.graph.stream(initial_state, {"recursion_limit": 15}):
                node_name = list(event.keys())[0]
                node_output = event[node_name]

                for key, value in node_output.items():
                    if isinstance(value, str) and len(value) > 300:
                        self.logger.add_log("DEBUG", f"  - {key}: (내용이 길어 생략됨)")
                    elif key not in ["client", "root"]:
                        self.logger.add_log("DEBUG", f"  - {key}: {value}")

                if (
                    "progress_message" in node_output
                    and node_output["progress_message"]
                ):
                    self._update_progress(node_output["progress_message"])

                final_state = node_output

            self.logger.add_log(
                "SYSTEM", "=" * 20 + " 보고서 생성 파이프라인 종료 " + "=" * 20
            )

            if not final_state:
                raise Exception("그래프 실행이 정상적으로 완료되지 않았습니다.")

            final_report_with_refs = final_state.get(
                "final_report_with_refs", "오류: 최종 보고서를 찾을 수 없습니다."
            )

            now = datetime.now()
            date_str = now.strftime("%Y%m%d_%H%M%S")
            report_filename = os.path.join(
                self.results_folder, f"final_report_{date_str}.md"
            )
            self.logger.add_log(
                "INFO", f"[6/6] 보고서 파일 저장 중... -> '{report_filename}'"
            )

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_report_with_refs)

            full_log_path, node_log_paths = self.logger.save_logs(self.logs_folder)

            dashboard_path = self.analyzer.create_visualization_dashboard(
                self.logger, final_state, self.viz_folder
            )

            self.logger.add_log(
                "SUCCESS",
                f"🎉 모든 작업이 완료되었습니다! 결과 폴더: {self.results_folder}",
            )

            if self.progress_queue:
                self.progress_queue.put(
                    {
                        "final_report": final_report_with_refs,
                        "dashboard_path": dashboard_path,
                        "log_path": full_log_path,
                    }
                )

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.logger.add_log("ERROR", f"리포트 생성 중 오류 발생: {e}")
            if self.progress_queue:
                self.progress_queue.put({"error": f"리포트 생성 중 오류 발생: {e}"})
        finally:
            if self.progress_queue:
                self.progress_queue.put({"generation_done": True})

    def _get_model_for_task(self, task_name):
        model_name = self.models.get(task_name, "gemini-1.5-flash-latest")
        return genai.GenerativeModel(model_name)

    def _get_generation_config(self, task_name):
        budget = self.thinking_budgets.get(task_name)
        if budget is not None:
            return {"thinking_config": {"thinking_budget": budget}}
        return None

    def _search_similar_documents(self, query, k=10):
        query_embedding = genai.embed_content(
            model=config.EMBEDDING_MODEL,  # embed_content는 모델 이름을 직접 받음
            content=query,
            task_type="RETRIEVAL_QUERY",
        )["embedding"]
        candidate_k = min(k * 3, len(self.db_data))
        distances, indices = self.index.search(
            np.array([query_embedding], dtype="float32"), candidate_k
        )
        candidates = [self.db_data[i] for i in indices[0]]
        with_refs = [c for c in candidates if c.get("reference_text")]
        without_refs = [c for c in candidates if not c.get("reference_text")]
        result = with_refs[:k] + without_refs[: max(0, k - len(with_refs))]
        return result[:k]

    def _extract_key_themes(self):
        num_clusters = min(config.NUM_CLUSTERS_FOR_OUTLINE, self.index.ntotal)
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(self.all_vectors)
        representative_indices = []
        for i in range(num_clusters):
            cluster_indices = np.where(kmeans.labels_ == i)[0]
            if len(cluster_indices) > 0:
                cluster_center = kmeans.cluster_centers_[i]
                distances = faiss.pairwise_distances(
                    cluster_center.reshape(1, -1), self.all_vectors[cluster_indices]
                )
                closest_in_cluster = np.argmin(distances)
                representative_indices.append(cluster_indices[closest_in_cluster])
        return [self.db_data[i] for i in representative_indices]

    def _create_search_queries_for_section(self, header, topic, outline):
        """LLM을 사용하여 특정 섹션에 대한 다양하고 구체적인 검색어를 생성합니다."""
        self.logger.add_log("DEBUG", f"'{header}' 섹션에 대한 검색어 생성 중...")

        prompt = f"""
        당신은 특정 주제에 대한 깊이 있는 정보 수집을 위해, 벡터 데이터베이스에서 사용할 검색어를 만드는 전문 연구원입니다.
        아래 정보를 바탕으로, '{header}' 섹션을 작성하는 데 필요한 가장 효과적인 검색어 {config.NUM_SEARCH_QUERIES}개를 생성해주세요.

        --- 전체 보고서 주제 ---
        {topic}

        --- 전체 보고서 개요 ---
        {outline}
        --- 끝 ---

        **지시사항:**
        1. **다양성:** 생성되는 검색어들은 서로 다른 관점과 키워드를 포함해야 합니다. 동일한 검색어를 반복하지 마세요.
        2. **구체성:** "ACP의 역사"와 같은 포괄적인 검색어 대신, "벨기에 ACP 제도의 초기 판례" 또는 "2022년 ACP 법제화의 주요 동인"과 같이 구체적이고 상세한 검색어를 만드세요.
        3. **출력 형식:** 각 검색어를 줄바꿈으로 구분하여, 오직 검색어 목록만 출력해주세요. 다른 설명은 포함하지 마세요.
        """
        model = self._get_model_for_task("query_generation")
        response = model.generate_content(prompt)
        queries = [q.strip() for q in response.text.split("\n") if q.strip()]

        self.logger.add_log("DEBUG", f"생성된 검색어: {queries}")
        return queries

    def _generate_outline_logic(self, topic):
        key_theme_contexts = self._extract_key_themes()
        topic_specific_contexts = self._search_similar_documents(
            topic, k=config.K_FOR_TOPIC_SEARCH
        )
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
        prompt = config.OUTLINE_PROMPT_TEMPLATE.format(
            report_purpose=config.REPORT_PURPOSE,
            topic=topic,
            guideline=config.EDITORIAL_GUIDELINE,
            context_str=context_str,
        )
        model = self._get_model_for_task("outline_generation")
        generation_config = self._get_generation_config("outline_generation")
        response = model.generate_content(
            contents=prompt, generation_config=generation_config
        )
        return response.text

    def _generate_single_section(
        self, header, topic, outline, improvement_instructions=""
    ):
        # 이 함수는 `node_generate_draft`와 `node_regenerate_sections`에서 호출됩니다.
        self.logger.add_log("DEBUG", f"'{header}' 섹션 생성 시작...")

        # 1. LLM을 사용하여 다양하고 구체적인 검색어 생성
        search_queries = self._create_search_queries_for_section(header, topic, outline)

        # 2. 생성된 각 검색어로 문서를 검색하고 결과를 통합
        all_contexts = {}
        for query in search_queries:
            contexts = self._search_similar_documents(
                query, k=config.K_FOR_SECTION_DRAFT
            )
            for c in contexts:
                all_contexts[c["chunk_id"]] = c  # chunk_id를 키로 사용하여 중복 제거

        final_contexts = list(all_contexts.values())
        self.logger.add_log(
            "INFO",
            f"'{header}' 섹션 위해 총 {len(final_contexts)}개의 고유한 참고자료 검색 완료.",
        )

        context_str = "\n\n---\n\n".join(
            [
                f"chunk_id: {c['chunk_id']}\n문서: {c['file_path']}\n목차: {' > '.join(c['headers'])}\n문장: {c['sentence']}\n참고문헌: {c.get('reference_text', 'N/A')}"
                for c in final_contexts
            ]
        )

        improvement_prompt = ""
        if improvement_instructions:
            improvement_prompt = f"""
            --- 개선 지시사항 ---
            이전 버전에 대한 편집팀의 검토 결과, 다음과 같은 개선이 필요합니다. 이 지시사항을 반드시 반영하여 내용을 다시 작성해주세요.
            - {improvement_instructions}
            --- 끝 ---
            """

        prompt = config.DRAFT_SECTION_PROMPT_TEMPLATE.format(
            report_purpose=config.REPORT_PURPOSE,
            topic=topic,
            improvement_prompt=improvement_prompt,
            guideline=config.EDITORIAL_GUIDELINE,
            context_str=context_str,
            header=header,
        )
        model = self._get_model_for_task("draft_generation")
        generation_config = self._get_generation_config("draft_generation")
        response = model.generate_content(
            contents=prompt, generation_config=generation_config
        )
        self.logger.add_log(
            "DEBUG", f"'{header}' 섹션 생성 완료 (길이: {len(response.text)}자)"
        )
        return response.text

    def _editorial_review_logic(self, report_text, outline):
        self.logger.add_log("INFO", "편집장 검토 로직 시작...")
        prompt = config.EDITORIAL_REVIEW_PROMPT_TEMPLATE.format(
            report_purpose=config.REPORT_PURPOSE,
            outline=outline,
            guideline=config.EDITORIAL_GUIDELINE,
            report_text=report_text,
        )
        model = self._get_model_for_task("editorial_review")
        generation_config = self._get_generation_config("editorial_review")
        response = model.generate_content(
            contents=prompt, generation_config=generation_config
        )

        try:
            json_text = re.search(
                r"```json\n(.*?)\n```", response.text, re.DOTALL
            ).group(1)
            result = json.loads(json_text)
            self.logger.add_log(
                "SUCCESS",
                "편집장 검토 완료. 개선 필요 섹션: "
                + str(len(result.get("sections_to_improve", []))),
            )
            return result
        except (AttributeError, json.JSONDecodeError) as e:
            self.logger.add_log("ERROR", f"편집장 검토 결과 파싱 실패: {e}")
            return {
                "overall_comment": f"AI 응답 파싱 실패. 모델이 유효한 JSON을 반환하지 않았습니다.\n오류: {e}",
                "review_passed": False,
                "sections_to_improve": [],
                "raw_response": response.text,  # 원본 응답 추가
            }

    def _final_formatting_logic(self, report_text):
        self.logger.add_log("INFO", "최종 서식 정리 로직 시작...")
        prompt = config.FINAL_FORMATTING_PROMPT_TEMPLATE.format(
            report_text=report_text, guideline=config.EDITORIAL_GUIDELINE
        )
        model = self._get_model_for_task("final_formatting")
        generation_config = self._get_generation_config("final_formatting")
        response = model.generate_content(
            contents=prompt, generation_config=generation_config
        )
        self.logger.add_log("SUCCESS", "최종 서식 정리 완료.")
        return response.text

    def _finalize_citations_logic(self, final_text):
        self.logger.add_log("INFO", "최종 각주 처리 로직 시작...")

        # 1. 본문에서 모든 각주 ID를 *순서대로* 찾습니다. (set 사용 안 함, ^는 선택사항)
        ordered_footnote_ids = re.findall(r"\[\^?([\w-]+)\]", final_text)

        if not ordered_footnote_ids:
            self.logger.add_log("INFO", "본문에 처리할 유효한 각주가 없습니다.")
            return re.sub(r"\[\^?([\w-]+)\]", "", final_text)

        # 2. 각주가 처음 등장하는 순서대로 고유한 참고문헌 목록을 만듭니다.
        unique_references_in_order = []
        seen_refs = set()
        for chunk_id in ordered_footnote_ids:
            chunk_data = self.chunk_id_map.get(chunk_id)
            if chunk_data:
                ref_text = chunk_data.get("reference_text")
                if ref_text and ref_text not in seen_refs:
                    unique_references_in_order.append(ref_text)
                    seen_refs.add(ref_text)

        if not unique_references_in_order:
            self.logger.add_log(
                "INFO", "본문에 유효한 참고문헌이 연결된 각주가 없습니다."
            )
            return re.sub(r"\[\^?([\w-]+)\]", "", final_text)

        # 3. 등장 순서에 따라 참고문헌에 번호를 매깁니다.
        ref_to_num_map = {
            ref: i + 1 for i, ref in enumerate(unique_references_in_order)
        }

        # 4. 본문의 각주 ID를 순서에 맞는 번호로 교체합니다.
        def replace_footnote(match):
            chunk_id = match.group(1)
            chunk_data = self.chunk_id_map.get(chunk_id)
            if chunk_data:
                ref_text = chunk_data.get("reference_text")
                if ref_text and ref_text in ref_to_num_map:
                    return f"[{ref_to_num_map[ref_text]}]"
            return ""  # 유효하지 않은 각주는 제거

        final_text_with_numbered_refs = re.sub(
            r"\[\^?([\w-]+)\]", replace_footnote, final_text
        )

        # 5. 보고서 끝에 순서대로 정렬된 참고문헌 목록을 추가합니다.
        references_section = "\n\n---\n\n## 참고문헌\n\n"
        for i, ref in enumerate(unique_references_in_order):
            references_section += f"{i+1}. {ref}\n"

        self.logger.add_log(
            "SUCCESS",
            f"{len(unique_references_in_order)}개의 고유 참고문헌을 순서에 맞게 처리했습니다.",
        )
        return final_text_with_numbered_refs + references_section

    def node_generate_outline(self, state: ReportState):
        self.logger.set_current_node("generate_outline")
        self.logger.add_log("INFO", "[1/6] 보고서 개요 생성 시작")
        self._update_progress("[1/6] 보고서 개요 생성 시작...")
        outline = self._generate_outline_logic(state["topic"])
        self.logger.add_log("SUCCESS", f"개요 생성 완료 (길이: {len(outline)}자)")
        return {
            "outline": outline,
            "progress_message": "1/6: 개요 생성 완료. 초안 작성 시작...",
        }

    def node_generate_draft(self, state: ReportState):
        self.logger.set_current_node("generate_draft")
        self.logger.add_log("INFO", "[2/6] 보고서 초안 생성 시작")
        self._update_progress("[2/6] 보고서 초안 생성 시작...")

        outline = state["outline"]
        topic = state["topic"]

        headers = re.findall(r"^(##+)\s+(.*)", outline, re.MULTILINE)

        report_content = {}
        full_draft_parts = []
        total_headers = len(headers)

        for i, (level, header) in enumerate(headers):
            # 목차의 레벨에 따라 헤더 추가
            full_draft_parts.append(f"\n{level} {header}\n")

            progress_msg = f"[2/6] 초안 작성 중... ({i+1}/{total_headers}): {header}"
            self._update_progress(progress_msg)
            self.logger.add_log("INFO", progress_msg)

            section_content = self._generate_single_section(header, topic, outline)
            report_content[header] = section_content
            full_draft_parts.append(section_content)

        full_draft = "\n\n".join(full_draft_parts)

        self.logger.add_log(
            "SUCCESS", f"보고서 초안 생성 완료 (총 길이: {len(full_draft)}자)"
        )
        return {
            "report_content": report_content,
            "current_report_text": full_draft,
            "progress_message": "2/6: 초안 생성 완료. 편집장 검토 시작...",
        }

    def node_editorial_review(self, state: ReportState):
        self.logger.set_current_node("editorial_review")
        self.logger.add_log("INFO", "[3/6] 편집장 검토 및 개선 작업 시작")
        review_attempts = state["review_attempts"] + 1
        self._update_progress(
            f"편집장 검토... (시도 {review_attempts}/{config.MAX_REVIEW_ATTEMPTS})"
        )

        report_text = state["current_report_text"]

        # 1. 메타데이터 수집
        char_count = len(report_text)
        word_count = len(report_text.split())
        # 각주 개수 계산 (유연한 정규식 사용)
        ref_count = len(re.findall(r"[(\[]\^?([\w-]+)[)\]]", report_text))
        model_name = self.models.get("editorial_review", "N/A")

        # 2. 검토 로직 실행
        review_result = self._editorial_review_logic(report_text, state["outline"])

        # 3. 메타데이터를 검토 결과에 추가
        review_result["metadata"] = {
            "model_used": model_name,
            "char_count": char_count,
            "word_count": word_count,
            "reference_count": ref_count,
        }

        self.logger.add_log(
            "INFO",
            f"검토 결과: 통과={review_result.get('review_passed')}, 개선 필요={len(review_result.get('sections_to_improve', []))}개",
        )
        self.logger.add_log(
            "DEBUG", f"검토 총평: {review_result.get('overall_comment')}"
        )

        return {
            "review_result": review_result,
            "review_attempts": review_attempts,
            "review_history": state["review_history"] + [review_result],
            "progress_message": "3/6: 편집장 검토 완료. 필요시 재작성합니다.",
        }

    def node_regenerate_sections(self, state: ReportState):
        self.logger.set_current_node("regenerate_sections")
        sections_to_improve = state["review_result"].get("sections_to_improve", [])
        self.logger.add_log(
            "INFO", f"보고서 일부 재작성 시작 ({len(sections_to_improve)}개 섹션)"
        )
        self._update_progress(
            f"보고서 일부 재작성 중... ({len(sections_to_improve)}개 섹션)"
        )

        updated_content = state["report_content"].copy()

        for i, section in enumerate(sections_to_improve):
            header = section["section_header"]
            instructions = section["improvement_instruction"]

            progress_msg = f"재작성 중... ({i+1}/{len(sections_to_improve)}): {header}"
            self._update_progress(progress_msg)
            self.logger.add_log("INFO", progress_msg)
            self.logger.add_log("DEBUG", f"개선 지시사항: {instructions}")

            if header in updated_content:
                regenerated_content = self._generate_single_section(
                    header, state["topic"], state["outline"], instructions
                )
                updated_content[header] = regenerated_content
            else:
                self.logger.add_log(
                    "WARN", f"재작성할 섹션을 찾지 못했습니다: {header}"
                )

        # 재작성된 내용으로 전체 보고서 텍스트 재구성
        outline = state["outline"]
        headers_in_outline = re.findall(r"^(##+)\s+(.*)", outline, re.MULTILINE)
        new_report_parts = []
        for level, h in headers_in_outline:
            new_report_parts.append(f"\n{level} {h}\n")
            new_report_parts.append(updated_content.get(h, ""))

        new_report_text = "\n\n".join(new_report_parts)

        self.logger.add_log("SUCCESS", "보고서 일부 재작성 완료.")
        return {
            "report_content": updated_content,
            "current_report_text": new_report_text,
            "progress_message": "일부 재작성 완료. 다시 편집장 검토를 진행합니다.",
        }

    def node_final_formatting(self, state: ReportState):
        self.logger.set_current_node("final_formatting")
        self.logger.add_log("INFO", "[4/6] 최종 서식 정리 시작")
        self._update_progress("[4/6] 최종 서식 정리 시작...")

        original_text = state["current_report_text"]

        # 1. (보호) 가능한 모든 형태의 각주를 '순서대로' 리스트에 저장합니다.
        # 정규식은 [^uuid], [uuid], (uuid), (^uuid) 등을 모두 포괄합니다.
        original_citations_matches = list(
            re.finditer(r"[(\[]\^?([\w-]+)[)\]]", original_text)
        )

        if not original_citations_matches:
            self.logger.add_log(
                "WARN", "보호할 각주를 찾지 못했습니다. 서식 정리만 진행합니다."
            )
            formatted_report = self._final_formatting_logic(original_text)
            return {
                "formatted_report": formatted_report,
                "progress_message": "4/6: 서식 정리 완료. 최종 각주 처리 시작...",
            }

        # 2. 본문의 각주를 [참고문헌:인덱스] 형태로 순서대로 바꿉니다.
        citation_counter = 0

        def protect_placeholder(match):
            nonlocal citation_counter
            placeholder = f"[참고문헌:{citation_counter}]"
            citation_counter += 1
            return placeholder

        protected_text = re.sub(
            r"[(\[]\^?([\w-]+)[)\]]", protect_placeholder, original_text
        )
        self.logger.add_log(
            "DEBUG",
            f"{len(original_citations_matches)}개의 각주를 찾아 임시 플레이스홀더로 교체했습니다.",
        )

        # 3. 보호된 텍스트로 서식 정리 로직(LLM 호출)을 수행합니다.
        formatted_protected_text = self._final_formatting_logic(protected_text)

        # 4. (복원) [참고문헌:인덱스]를 원래의 표준 형식 [^uuid]로 되돌립니다.
        restored_text = formatted_protected_text

        # 복원을 위해 임시 플레이스홀더를 다시 찾습니다.
        temp_placeholders_in_formatted_text = re.findall(
            r"\[참고문헌:(\d+)\]", restored_text
        )

        num_restored = 0
        for index_str in temp_placeholders_in_formatted_text:
            index = int(index_str)
            if index < len(original_citations_matches):
                placeholder_to_replace = f"[참고문헌:{index}]"
                # 원본 uuid를 가져와 표준 형식으로 복원
                original_uuid = original_citations_matches[index].group(1)
                standard_citation = f"[^{original_uuid}]"

                # 중복 교체를 방지하기 위해 1번만 교체
                if placeholder_to_replace in restored_text:
                    restored_text = restored_text.replace(
                        placeholder_to_replace, standard_citation, 1
                    )
                    num_restored += 1

        self.logger.add_log(
            "DEBUG",
            f"{num_restored}/{len(original_citations_matches)}개의 각주를 성공적으로 복원했습니다.",
        )

        self.logger.add_log(
            "SUCCESS", f"최종 서식 정리 완료 (길이: {len(restored_text)}자)"
        )
        return {
            "formatted_report": restored_text,
            "progress_message": "4/6: 서식 정리 완료. 최종 각주 처리 시작...",
        }

    def node_finalize_citations_and_save_log(self, state: ReportState):
        self.logger.set_current_node("finalize_and_save")
        self.logger.add_log("INFO", "[5/6] 최종 각주 처리 및 로그 저장 시작")
        self._update_progress("[5/6] 최종 각주 처리 및 로그 저장 시작...")
        final_report_with_refs = self._finalize_citations_logic(
            state["formatted_report"]
        )
        self.logger.add_log(
            "SUCCESS",
            f"최종 보고서 생성 완료 (참고문헌 포함, 길이: {len(final_report_with_refs)}자)",
        )

        # Save node-specific logs
        for node_name, history in self.logger.node_logs.items():
            log_path = os.path.join(
                self.logs_folder, f"node_{node_name}_log_{self.logger.session_id}.md"
            )
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# Log for node: {node_name}\n\n")
                # history의 각 아이템을 문자열로 변환하여 join
                f.write("\n".join(map(str, history)))

        # Save editorial review history
        review_log_path = os.path.join(
            self.results_folder, f"editorial_review_log_{self.logger.session_id}.md"
        )
        with open(review_log_path, "w", encoding="utf-8") as f:
            f.write("# Editorial Review History\n\n")
            for i, review in enumerate(state["review_history"]):
                f.write(f"## Attempt {i+1}\n\n")

                # 메타데이터 기록
                metadata = review.get("metadata", {})
                if metadata:
                    f.write("### Review Metadata\n\n")
                    f.write(
                        f"- **Model Used:** `{metadata.get('model_used', 'N/A')}`\n"
                    )
                    f.write(
                        f"- **Character Count:** {metadata.get('char_count', 0):,}\n"
                    )
                    f.write(f"- **Word Count:** {metadata.get('word_count', 0):,}\n")
                    f.write(
                        f"- **Reference Count:** {metadata.get('reference_count', 0)}\n\n"
                    )

                f.write("### Review Result\n\n")
                f.write(f"**Passed:** {review.get('review_passed')}\n\n")
                f.write(
                    f"**Overall Comment:**\n\n```\n{review.get('overall_comment')}\n```\n\n"
                )

                if review.get("sections_to_improve"):
                    f.write("### Sections to Improve\n\n")
                    for section in review.get("sections_to_improve"):
                        f.write(
                            f"- **{section['section_header']}**: {section['improvement_instruction']}\n"
                        )

                # 파싱 실패 시 원본 응답 기록
                if "raw_response" in review:
                    f.write("\n### Raw Model Response (on parsing failure)\n\n")
                    f.write(f"```\n{review['raw_response']}\n```\n\n")

                f.write("\n---\n\n")

        return {
            "final_report_with_refs": final_report_with_refs,
            "progress_message": "5/6: 각주 처리 및 로그 저장 완료.",
        }

    def should_continue_review(self, state: ReportState):
        review_result = state["review_result"]
        review_attempts = state["review_attempts"]

        if review_result.get("review_passed"):
            return "end_review"

        if review_attempts >= config.MAX_REVIEW_ATTEMPTS:
            self.logger.add_log(
                "WARN",
                f"최대 검토 횟수({config.MAX_REVIEW_ATTEMPTS})에 도달하여, 개선 없이 다음 단계로 진행합니다.",
            )
            return "end_review"

        if not review_result.get("sections_to_improve"):
            self.logger.add_log(
                "WARN",
                "검토에 실패했지만 개선할 섹션이 없습니다. 재검토를 다시 시도합니다.",
            )

        return "regenerate"

    def _build_graph(self):
        workflow = StateGraph(ReportState)
        workflow.add_node("generate_outline", self.node_generate_outline)
        workflow.add_node("generate_draft", self.node_generate_draft)
        workflow.add_node("editorial_review", self.node_editorial_review)
        workflow.add_node("regenerate_sections", self.node_regenerate_sections)
        workflow.add_node("final_formatting", self.node_final_formatting)
        workflow.add_node(
            "finalize_and_save", self.node_finalize_citations_and_save_log
        )
        workflow.set_entry_point("generate_outline")
        workflow.add_edge("generate_outline", "generate_draft")
        workflow.add_edge("generate_draft", "editorial_review")
        workflow.add_conditional_edges(
            "editorial_review",
            self.should_continue_review,
            {"regenerate": "regenerate_sections", "end_review": "final_formatting"},
        )
        workflow.add_edge("regenerate_sections", "editorial_review")
        workflow.add_edge("final_formatting", "finalize_and_save")
        workflow.add_edge("finalize_and_save", END)
        return workflow.compile()
