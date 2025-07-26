import os
import json
import re
import uuid
import numpy as np
import faiss
from google import genai
from google.genai import types
from dotenv import load_dotenv
import warnings
import kss
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from sklearn.cluster import KMeans
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
        self.client = None
        self._configure_api()

    def _configure_api(self):
        load_dotenv()
        if config.GOOGLE_PROJECT_ID:
            # Vertex AI 사용 (공식 문서 방식)
            self.client = genai.Client(
                vertexai=True, project=config.GOOGLE_PROJECT_ID, location="us-central1"
            )
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY 또는 GOOGLE_PROJECT_ID를 .env 파일에서 찾을 수 없습니다."
                )
            # Gemini Developer API 사용 (공식 문서 방식)
            self.client = genai.Client(api_key=api_key)

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

            result = self.client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=batch_contents,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            # ContentEmbedding 객체의 values 속성으로 접근
            embeddings_values = [embedding.values for embedding in result.embeddings]
            all_embeddings.extend(embeddings_values)

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
        self.client = None
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
        if config.GOOGLE_PROJECT_ID:
            # Vertex AI 사용 (공식 문서 방식)
            self.client = genai.Client(
                vertexai=True, project=config.GOOGLE_PROJECT_ID, location="us-central1"
            )
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY 또는 GOOGLE_PROJECT_ID를 .env 파일에서 찾을 수 없습니다."
                )
            # Gemini Developer API 사용 (공식 문서 방식)
            self.client = genai.Client(api_key=api_key)

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
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.results_folder = f"results_{mode.lower()}_{session_id}"
            self.logs_folder = os.path.join(self.results_folder, "logs")
            self.viz_folder = os.path.join(self.results_folder, "visualizations")

            os.makedirs(self.results_folder, exist_ok=True)
            os.makedirs(self.logs_folder, exist_ok=True)
            os.makedirs(self.viz_folder, exist_ok=True)

            self.logger.start_logging(session_id)
            self.logger.add_log(
                "SYSTEM",
                f"========== {'Extreme' if mode == 'Bypass' else 'Standard'} Report Generation Pipeline Start ==========",
            )

            if mode == "Bypass":
                self.models = {"bypass_generation": config.BYPASS_MODEL}
                graph = self._build_bypass_graph()
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
                    progress_message="0/2: 익스트림 파이프라인 시작...",
                )
            else:
                if mode == "Production":
                    self.models = config.PRODUCTION_MODELS
                    self.thinking_budgets = config.PRODUCTION_THINKING_BUDGETS
                else:
                    self.models = config.TEST_MODELS
                    self.thinking_budgets = config.TEST_THINKING_BUDGETS

                graph = self.graph
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
            for event in graph.stream(initial_state, {"recursion_limit": 15}):
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
                "SYSTEM",
                f"========== {'Extreme' if mode == 'Bypass' else 'Standard'} Report Generation Pipeline End ==========",
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
                "INFO",
                f"[{'2/2' if mode == 'Bypass' else '6/6'}] 보고서 파일 저장 중... -> '{report_filename}'",
            )

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(final_report_with_refs)

            if mode != "Bypass":
                full_log_path, node_log_paths = self.logger.save_logs(self.logs_folder)

                dashboard_path = self.analyzer.create_visualization_dashboard(
                    self.logger, final_state, self.viz_folder
                )
            else:
                full_log_path = self.logger.save_logs(self.logs_folder, is_bypass=True)
                dashboard_path = None

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
        return self.models.get(task_name, "gemini-1.5-flash-latest")

    def _get_generation_config(self, task_name, tools=None):
        budget = self.thinking_budgets.get(task_name)
        thinking_config = (
            types.ThinkingConfig(thinking_budget=budget) if budget is not None else None
        )
        return types.GenerateContentConfig(thinking_config=thinking_config, tools=tools)

    def _search_similar_documents(self, query, k=10):
        query_embedding = (
            self.client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=[query],
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
            )
            .embeddings[0]
            .values
        )  # ContentEmbedding의 values 속성으로 접근
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
        response = self.client.models.generate_content(model=model, contents=prompt)
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
        response = self.client.models.generate_content(
            model=model, contents=prompt, config=generation_config
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
        response = self.client.models.generate_content(
            model=model, contents=prompt, config=generation_config
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
        response = self.client.models.generate_content(
            model=model, contents=prompt, config=generation_config
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
        response = self.client.models.generate_content(
            model=model, contents=prompt, config=generation_config
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

    def node_generate_bypassed_report(self, state: ReportState):
        """
        Extreme 모드: 개요를 바탕으로 Search Grounding과 참고 자료를 최대한 활용하여 한번에 보고서를 생성합니다.
        """
        self.logger.set_current_node("generate_bypassed_report")
        self.logger.add_log("INFO", "[1/2] 익스트림 모드로 전체 보고서 생성 시작")
        self._update_progress("[1/2] 익스트림 모드로 전체 보고서 생성 시작...")

        topic = state["topic"]
        outline = state["outline"]

        # 1. DB에서 주제 관련 문서들을 광범위하게 수집
        self.logger.add_log("INFO", "DB에서 주제 관련 문서 수집 시작...")

        # 주제 기반 검색으로 기본 문서들 수집
        topic_documents = self._search_similar_documents(topic, k=50)

        # 개요의 각 섹션별로도 추가 검색 수행
        outline_sections = re.findall(r"^#+\s+(.+)", outline, re.MULTILINE)
        section_documents = []
        for section in outline_sections[:10]:  # 상위 10개 섹션만
            section_docs = self._search_similar_documents(section, k=20)
            section_documents.extend(section_docs)

        # 중복 제거 및 통합
        all_documents = {}
        for doc in topic_documents + section_documents:
            doc_key = doc.get(
                "chunk_id", f"{doc.get('file_path', '')}_{doc.get('sentence', '')[:50]}"
            )
            all_documents[doc_key] = doc

        final_documents = list(all_documents.values())

        # 참고문헌이 있는 문서 우선 정렬
        final_documents.sort(
            key=lambda x: (
                1 if x.get("reference_text") else 0,  # 참고문헌 있는 것 우선
                -len(x.get("sentence", "")),  # 긴 문장 우선
            ),
            reverse=True,
        )

        self.logger.add_log(
            "INFO", f"총 {len(final_documents)}개의 관련 문서를 수집했습니다."
        )

        # 2. 문서 내용을 구조적으로 정리하여 프롬프트에 포함
        data_context = self._prepare_extensive_db_context(
            final_documents[:100]
        )  # 상위 100개 문서 사용

        # System Instruction으로 모델의 기본 동작 정의
        system_instruction = """
        당신은 법률 분야의 최고 전문가로서, 매우 상세하고 포괄적인 연구 보고서를 작성하는 전문 연구원입니다. 
        
        핵심 원칙:
        1. 제공된 참고 자료를 최대한 활용하여 구체적이고 정확한 내용을 작성하세요
        2. 웹 검색으로 최신 정보를 보완하여 종합적인 분석을 제공하세요
        3. 각 주장마다 신뢰할 수 있는 구체적 근거와 출처를 제시하세요
        4. 절대로 간략하게 작성하지 말고, 가능한 한 가장 상세하고 긴 내용을 제공하세요
        5. 모든 관련 정보를 빠짐없이 활용하여 완전한 분석을 수행하세요
        """

        prompt = f"""
        다음 주제와 개요에 따라 **극도로 상세하고 포괄적인** 법률 연구 보고서를 작성해주세요.

        ## 보고서 주제
        {topic}

        ## 보고서 개요  
        {outline}

        ## 📚 **제공된 참고 자료** 
        
        **중요: 아래 자료들은 매우 귀중한 1차 자료입니다. 이 내용들을 최대한 활용하여 보고서를 작성하세요.**
        
        {data_context}
        
        ---

        ## 🎯 **극한 상세도 요구사항**

        **목표 길이: 최소 30,000자 이상 (약 50-60페이지 분량)**

        ### 📋 **작성 방법론**
        
        **A. 참고 자료 활용 우선 원칙**:
        - 위에 제공된 참고 자료를 반드시 최우선으로 활용
        - 각 섹션마다 관련된 내용을 구체적으로 인용하고 분석
        - 구체적인 사례, 판례, 법조문을 적극 활용
        - 신뢰할 수 있는 출처가 있는 자료는 그 출처까지 명시하여 활용

        **B. 웹 검색 보완 활용**:
        - 제공된 자료로 기본 틀을 구성한 후, 웹 검색으로 최신 정보 보완
        - 최근 동향이나 해외 사례는 웹 검색으로 보강
        - 모든 자료와 웹 검색 결과를 유기적으로 연결하여 종합적 분석

        ### 📋 **섹션별 세부 요구사항**
        1. **서론 (최소 4,000자)**:
           - 제공된 배경 정보를 바탕으로 문제 상황 분석
           - 제도의 역사적 발전 과정을 상세 설명
           - 연구의 필요성을 구체적 사례로 입증
           - 방법론과 접근 방식을 명확히 기술

        2. **각 본론 섹션 (각각 최소 5,000-6,000자)**:
           - 법조문, 판례, 사례를 중심으로 설명
           - 각국 비교 자료를 원문을 인용하여 상세 분석
           - 전문가 의견이나 연구 결과를 적극 활용
           - 실무 사례와 절차를 구체적으로 설명
           - 웹 검색으로 최신 동향과 변화 사항 보완

        3. **결론 (최소 3,000자)**:
           - 분석 결과를 종합하여 핵심 발견사항 정리
           - 정책적 함의를 구체적 근거와 함께 제시
           - 향후 연구 과제와 개선 방안을 상세히 논의

        ### 🔍 **자료 활용 극대화 지침**

        **1. 인용 및 출처 표기**:
        - 신뢰할 수 있는 자료를 인용할 때는 자연스럽게 출처를 명시
        - 참고문헌이 있는 자료는 그 원출처도 함께 표기
        - 각 문단마다 관련 자료를 적극적으로 활용

        **2. 구체성과 정확성**:
        - 추상적 설명 대신 구체적 사례와 수치 데이터 활용
        - 법조문 번호, 판례 번호 등을 정확히 인용
        - 전문 용어나 개념은 정확한 정의와 설명을 활용

        **3. 완전성 추구**:
        - 모든 관련 정보를 빠짐없이 검토하고 활용
        - 여러 국가의 자료가 있다면 모두 비교 분석에 포함
        - 시계열 데이터가 있다면 변화 추이까지 분석

        ### ✅ **품질 보증 요구사항**
        1. 제공된 자료 활용률 최소 70% 이상 (전체 내용 중 자료 기반 내용 비율)
        2. 각 문단마다 최소 300-500자 이상의 실질적 내용 포함
        3. 모든 주장에 대해 신뢰할 수 있는 자료 또는 웹 검색 근거 제시
        4. 구체적 사례, 수치, 인용문을 풍부하게 활용
        5. 논리적 연결고리와 체계적 구성으로 가독성 확보

        **🔥 최종 목표: 방대한 자료를 완전히 활용하여, 해당 분야의 결정적 참고문헌이 될 수 있을 만큼 완벽하고 포괄적인 보고서를 생성하세요.**
        """

        model_name = self.models.get("bypass_generation", "gemini-2.5-pro")

        # Search Grounding 및 극한 성능 설정
        tools = [types.Tool(google_search=types.GoogleSearch())]

        config = types.GenerateContentConfig(
            # 기본 생성 설정
            system_instruction=system_instruction,
            tools=tools,
            # 토큰 및 길이 설정 (극한 최적화)
            max_output_tokens=65536,  # 최대 가능 토큰 수 (약 50,000자)
            # 창의성 및 다양성 조절
            temperature=0.8,  # 더 창의적이고 다양한 표현
            top_p=0.95,  # 다양한 단어 선택 허용
            top_k=40,  # 적절한 어휘 다양성
            # 다중 후보 생성으로 최고 품질 확보
            candidate_count=1,  # 안정성을 위해 1개로 설정
            # 깊이 있는 사고를 위한 설정
            thinking_config=types.ThinkingConfig(
                thinking_budget=32768,  # 최대 사고 예산
                include_thoughts=False,  # 사고 과정은 포함하지 않음
            ),
            # 안전 및 응답 형식 설정
            response_mime_type="text/plain",
            # 정지 조건 (더 긴 생성을 위해 제거)
            stop_sequences=[],
        )

        # 프롬프트 길이 확인 및 로깅
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4  # 대략적인 토큰 수 계산

        self.logger.add_log(
            "INFO", f"프롬프트 길이: {prompt_length:,}자 (약 {estimated_tokens:,} 토큰)"
        )
        self.logger.add_log(
            "INFO",
            f"참고문서 {len(final_documents)}개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작",
        )

        response = self.client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )

        # 참고문헌 추출 및 포매팅
        try:
            grounding_metadata = getattr(
                response.candidates[0], "grounding_metadata", None
            )
            if grounding_metadata:
                web_search_queries = grounding_metadata.web_search_queries or []
                grounding_chunks = grounding_metadata.grounding_chunks or []
            else:
                web_search_queries = []
                grounding_chunks = []

            self.logger.add_log(
                "INFO", f"Grounding 검색어 수: {len(web_search_queries)}"
            )
            self.logger.add_log("DEBUG", f"검색어 목록: {web_search_queries}")

            references_section = "\n\n---\n\n## 📚 참고문헌\n\n"

            # DB 참고문헌 추가
            db_references = set()
            for doc in final_documents:
                if doc.get("reference_text"):
                    db_references.add(doc["reference_text"])

            if db_references:
                references_section += "### 📖 DB 원문 참고자료\n\n"
                for i, ref in enumerate(sorted(db_references), 1):
                    references_section += f"{i}. {ref}\n\n"

            # 웹 검색 참고문헌 추가 (개선된 URL 추출)
            unique_refs = {}
            for chunk in grounding_chunks:
                if chunk.web:
                    # 원본 URL 추출 시도
                    uri = chunk.web.uri
                    title = chunk.web.title or "제목 없음"

                    # 리디렉션 URL인 경우 원본 URL 추출 시도
                    if "grounding-api-redirect" in uri:
                        # grounding chunk에서 추가 정보 확인
                        if (
                            hasattr(chunk, "retrieved_context")
                            and chunk.retrieved_context
                        ):
                            if hasattr(chunk.retrieved_context, "uri"):
                                original_uri = chunk.retrieved_context.uri
                                if (
                                    original_uri
                                    and not "grounding-api-redirect" in original_uri
                                ):
                                    uri = original_uri

                        # title에서 도메인 정보 추출하여 표시
                        if title != "제목 없음":
                            display_text = f"{title} (검색 결과)"
                        else:
                            display_text = "웹 검색 결과"
                    else:
                        display_text = title

                    if uri not in unique_refs:
                        unique_refs[uri] = display_text

            if unique_refs:
                start_num = len(db_references) + 1
                references_section += "### 🌐 웹 기반 참고자료\n\n"
                for i, (uri, display_text) in enumerate(unique_refs.items(), start_num):
                    if "grounding-api-redirect" in uri:
                        # 리디렉션 링크인 경우 링크와 함께 설명 추가
                        references_section += f"{i}. **{display_text}**  \n   {uri}  \n   *(Google Search Grounding을 통해 수집된 자료)*\n\n"
                    else:
                        # 직접 링크인 경우 URL 표시
                        references_section += f"{i}. **{display_text}**  \n   {uri}\n\n"

            final_report_text = response.text + references_section

            total_refs = len(db_references) + len(unique_refs)
            self.logger.add_log(
                "SUCCESS",
                f"총 {total_refs}개 참고문헌 추가 (DB: {len(db_references)}개, 웹: {len(unique_refs)}개)",
            )

        except (AttributeError, IndexError) as e:
            self.logger.add_log(
                "WARN",
                f"참고문헌 메타데이터를 추출하지 못했습니다: {e}. 모델 응답만 사용합니다.",
            )
            final_report_text = response.text

        # 생성 결과 통계
        char_count = len(final_report_text)
        word_count = len(final_report_text.split())
        data_utilization = (len(final_documents) / max(len(self.db_data), 1)) * 100

        self.logger.add_log(
            "SUCCESS",
            f"🎉 자료 완전 활용 익스트림 모드 보고서 생성 완료!\n"
            f"   📊 통계: {char_count:,}자 ({word_count:,}단어)\n"
            f"   🎯 목표 달성률: {(char_count/30000)*100:.1f}% (목표: 30,000자)\n"
            f"   💾 자료 활용률: {data_utilization:.1f}% ({len(final_documents)}/{len(self.db_data)}개 문서)",
        )

        return {
            "final_report_with_refs": final_report_text,
            "progress_message": "1/2: 자료 완전 활용 익스트림 보고서 생성 완료. 파일 저장 시작...",
        }

    def _prepare_extensive_db_context(self, documents):
        """
        참고 문서들을 구조적으로 정리하여 프롬프트에 포함할 컨텍스트를 생성합니다.
        """
        context_parts = []

        # 파일별로 그룹화
        file_groups = {}
        for doc in documents:
            file_path = doc.get("file_path", "미상")
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(doc)

        context_parts.append("### 📋 문서별 정리된 원문 자료\n")

        for file_path, file_docs in file_groups.items():
            context_parts.append(f"\n#### 📄 {file_path}\n")

            # 헤더별로 그룹화
            header_groups = {}
            for doc in file_docs:
                headers_key = " > ".join(doc.get("headers", ["기타"]))
                if headers_key not in header_groups:
                    header_groups[headers_key] = []
                header_groups[headers_key].append(doc)

            for headers_key, header_docs in header_groups.items():
                if headers_key and headers_key != "기타":
                    context_parts.append(f"\n**섹션**: {headers_key}\n")

                for i, doc in enumerate(header_docs, 1):
                    sentence = doc.get("sentence", "")
                    reference = doc.get("reference_text", "")

                    context_parts.append(f"{i}. {sentence}")
                    if reference:
                        context_parts.append(f"   📚 출처: {reference}")
                    context_parts.append("")

        # 참고문헌이 있는 중요 문서들 별도 정리
        ref_docs = [doc for doc in documents if doc.get("reference_text")]
        if ref_docs:
            context_parts.append("\n### 🎯 중요 참고문헌 포함 자료\n")
            for i, doc in enumerate(ref_docs[:20], 1):  # 상위 20개만
                context_parts.append(f"{i}. **내용**: {doc.get('sentence', '')}")
                context_parts.append(f"   **출처**: {doc.get('reference_text', '')}")
                context_parts.append(f"   **파일**: {doc.get('file_path', '')}")
                if doc.get("headers"):
                    context_parts.append(f"   **섹션**: {' > '.join(doc['headers'])}")
                context_parts.append("")

        return "\n".join(context_parts)

    def node_save_bypassed_report(self, state: ReportState):
        """
        Extreme 모드: 생성된 보고서를 저장하고 주요 로그를 기록합니다.
        """
        self.logger.set_current_node("save_bypassed_report")
        self.logger.add_log("INFO", "[2/2] 익스트림 보고서 저장 및 로그 기록 시작")
        self._update_progress("[2/2] 익스트림 보고서 저장 및 로그 기록 시작...")

        # Save node-specific logs
        for node_name, history in self.logger.node_logs.items():
            log_path = os.path.join(
                self.logs_folder, f"node_{node_name}_log_{self.logger.session_id}.md"
            )
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# Log for node: {node_name}\n\n")
                f.write("\n".join(map(str, history)))

        self.logger.add_log("SUCCESS", "익스트림 모드 로그 저장 완료.")

        return {
            "final_report_with_refs": state[
                "final_report_with_refs"
            ],  # 이전 상태에서 전달
            "progress_message": "2/2: 익스트림 보고서 저장 완료.",
        }

    def node_generate_outline(self, state: ReportState):
        self.logger.set_current_node("generate_outline")

        # Determine current step based on the graph being run
        total_steps = 2 if "bypass" in self.logger.session_id else 6
        progress_message_start = f"[1/{total_steps}] 보고서 개요 생성 시작..."
        progress_message_end = f"1/{total_steps}: 개요 생성 완료. {'익스트림 보고서 생성' if total_steps == 2 else '초안 작성'} 시작..."

        self.logger.add_log("INFO", progress_message_start)
        self._update_progress(progress_message_start)

        outline = self._generate_outline_logic(state["topic"])
        self.logger.add_log("SUCCESS", f"개요 생성 완료 (길이: {len(outline)}자)")

        return {
            "outline": outline,
            "progress_message": progress_message_end,
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

    def _build_bypass_graph(self):
        workflow = StateGraph(ReportState)
        workflow.add_node("generate_outline", self.node_generate_outline)
        workflow.add_node(
            "generate_bypassed_report", self.node_generate_bypassed_report
        )
        workflow.add_node("save_bypassed_report", self.node_save_bypassed_report)

        workflow.set_entry_point("generate_outline")
        workflow.add_edge("generate_outline", "generate_bypassed_report")
        workflow.add_edge("generate_bypassed_report", "save_bypassed_report")
        workflow.add_edge("save_bypassed_report", END)

        return workflow.compile()
