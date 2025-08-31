"""
네트워크 시각화 서비스 모듈
기업 간 협력 관계 네트워크를 시각화하는 기능 제공
"""

import json
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import logging
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.models import Relation, Company, University, Professor, RelationType

logger = logging.getLogger(__name__)


class NetworkVisualizer:
    """네트워크 시각화 서비스 클래스"""

    def __init__(self):
        self.node_colors = {
            "company": "#4CAF50",  # 초록색
            "university": "#2196F3",  # 파란색
            "professor": "#FF9800",  # 주황색
        }

        self.relation_colors = {
            "MOU": "#4CAF50",  # 초록색
            "JOINT_RESEARCH": "#2196F3",  # 파란색
            "INVESTMENT": "#FF9800",  # 주황색
            "MERGER": "#F44336",  # 빨간색
            "TECHNOLOGY_TRANSFER": "#9C27B0",  # 보라색
            "PARTNERSHIP": "#00BCD4",  # 청록색
            "COLLABORATION": "#607D8B",  # 회색
            "FUNDING": "#4CAF50",  # 초록색
        }

    def generate_network_data(
        self,
        target_company: Optional[str] = None,
        max_depth: int = 3,
        relation_types: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        기업 관계 네트워크 데이터를 생성

        Args:
            target_company: 중심 기업명 (None이면 전체 네트워크)
            max_depth: 네트워크 깊이 제한
            relation_types: 포함할 관계 유형들
            start_date: 시작 날짜 필터
            end_date: 종료 날짜 필터
            db: 데이터베이스 세션

        Returns:
            네트워크 데이터 (nodes, edges, metadata)
        """
        if db is None:
            db = next(get_db())

        try:
            # 관계 데이터 조회
            relations = self._get_filtered_relations(
                db, target_company, relation_types, start_date, end_date
            )

            if not relations:
                return {"nodes": [], "edges": [], "metadata": {}}

            # 네트워크 그래프 생성
            G = nx.Graph()

            # 노드와 엣지 추가
            for relation in relations:
                self._add_relation_to_graph(G, relation, max_depth)

            # 중심 기업이 지정된 경우 해당 기업을 중심으로 한 서브그래프 생성
            if target_company:
                G = self._extract_subgraph(G, target_company, max_depth)

            # 노드와 엣지 데이터 추출
            nodes_data = self._extract_nodes_data(G)
            edges_data = self._extract_edges_data(G, relations)

            # 메타데이터 생성
            metadata = {
                "total_nodes": len(nodes_data),
                "total_edges": len(edges_data),
                "node_types": self._count_node_types(nodes_data),
                "edge_types": self._count_edge_types(edges_data),
                "generated_at": datetime.now().isoformat(),
                "target_company": target_company,
                "max_depth": max_depth,
            }

            result = {"nodes": nodes_data, "edges": edges_data, "metadata": metadata}

            logger.info(
                f"네트워크 데이터 생성 완료: {len(nodes_data)}개 노드, {len(edges_data)}개 엣지"
            )
            return result

        except Exception as e:
            logger.error(f"네트워크 데이터 생성 실패: {e}")
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}

    def _get_filtered_relations(
        self,
        db: Session,
        target_company: Optional[str],
        relation_types: Optional[List[str]],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[Relation]:
        """필터링된 관계 데이터 조회"""
        query = db.query(Relation).filter(
            Relation.status.in_(["approved", "extracted"])  # 승인된 관계만 포함
        )

        # 기업 필터
        if target_company:
            query = query.filter(
                (Relation.company_a.has(Company.name == target_company))
                | (Relation.company_b.has(Company.name == target_company))
            )

        # 관계 유형 필터
        if relation_types:
            query = query.filter(Relation.relation_type.in_(relation_types))

        # 날짜 필터
        if start_date:
            query = query.filter(Relation.created_at >= start_date)
        if end_date:
            query = query.filter(Relation.created_at <= end_date)

        return query.all()

    def _add_relation_to_graph(self, G: nx.Graph, relation: Relation, max_depth: int):
        """관계 데이터를 그래프에 추가"""
        # 기업 노드들 추가
        if relation.company_a:
            G.add_node(
                f"company_{relation.company_a.id}",
                id=relation.company_a.id,
                name=relation.company_a.name,
                type="company",
                industry=relation.company_a.industry,
                size=1,
            )

        if relation.company_b:
            G.add_node(
                f"company_{relation.company_b.id}",
                id=relation.company_b.id,
                name=relation.company_b.name,
                type="company",
                industry=relation.company_b.industry,
                size=1,
            )

        # 대학 노드 추가
        if relation.university:
            G.add_node(
                f"university_{relation.university.id}",
                id=relation.university.id,
                name=relation.university.name,
                type="university",
                location=relation.university.location,
                size=1,
            )

        # 교수 노드 추가
        if relation.professor:
            G.add_node(
                f"professor_{relation.professor.id}",
                id=relation.professor.id,
                name=relation.professor.name,
                type="professor",
                department=relation.professor.department,
                size=1,
            )

        # 엣지 추가
        if relation.company_a and relation.company_b:
            # 기업 간 관계
            G.add_edge(
                f"company_{relation.company_a.id}",
                f"company_{relation.company_b.id}",
                relation_id=relation.id,
                type=relation.relation_type,
                content=relation.relation_content,
                confidence=relation.confidence_score,
                start_date=str(relation.start_date) if relation.start_date else None,
                end_date=str(relation.end_date) if relation.end_date else None,
            )

        if relation.company_a and relation.university:
            # 기업-대학 관계
            G.add_edge(
                f"company_{relation.company_a.id}",
                f"university_{relation.university.id}",
                relation_id=relation.id,
                type=relation.relation_type,
                content=relation.relation_content,
                confidence=relation.confidence_score,
            )

        if relation.company_a and relation.professor:
            # 기업-교수 관계
            G.add_edge(
                f"company_{relation.company_a.id}",
                f"professor_{relation.professor.id}",
                relation_id=relation.id,
                type=relation.relation_type,
                content=relation.relation_content,
                confidence=relation.confidence_score,
            )

    def _extract_subgraph(
        self, G: nx.Graph, target_company: str, max_depth: int
    ) -> nx.Graph:
        """중심 기업을 기준으로 서브그래프 추출"""
        # 중심 기업 노드 찾기
        center_nodes = [
            node
            for node, data in G.nodes(data=True)
            if data.get("name") == target_company and data.get("type") == "company"
        ]

        if not center_nodes:
            return G

        center_node = center_nodes[0]

        # BFS로 서브그래프 생성
        subgraph_nodes = set()
        visited = set()
        queue = [(center_node, 0)]

        while queue:
            current_node, depth = queue.pop(0)

            if current_node in visited or depth > max_depth:
                continue

            visited.add(current_node)
            subgraph_nodes.add(current_node)

            # 연결된 노드들 추가
            for neighbor in G.neighbors(current_node):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return G.subgraph(subgraph_nodes)

    def _extract_nodes_data(self, G: nx.Graph) -> List[Dict]:
        """그래프에서 노드 데이터 추출"""
        nodes = []
        for node_id, node_data in G.nodes(data=True):
            node_info = {
                "id": node_id,
                "name": node_data.get("name", ""),
                "type": node_data.get("type", ""),
                "group": node_data.get("type", ""),
                "size": max(
                    1, len(list(G.neighbors(node_id)))
                ),  # 연결된 노드 수에 비례
                "color": self.node_colors.get(node_data.get("type", ""), "#666"),
                "data": node_data,
            }
            nodes.append(node_info)

        return nodes

    def _extract_edges_data(self, G: nx.Graph, relations: List[Relation]) -> List[Dict]:
        """그래프에서 엣지 데이터 추출"""
        edges = []
        for source, target, edge_data in G.edges(data=True):
            edge_info = {
                "source": source,
                "target": target,
                "type": edge_data.get("type", ""),
                "value": 1,  # 엣지 굵기 (기본값 1)
                "color": self.relation_colors.get(edge_data.get("type", ""), "#666"),
                "data": edge_data,
            }
            edges.append(edge_info)

        return edges

    def _count_node_types(self, nodes: List[Dict]) -> Dict[str, int]:
        """노드 타입별 개수 계산"""
        counts = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_edge_types(self, edges: List[Dict]) -> Dict[str, int]:
        """엣지 타입별 개수 계산"""
        counts = {}
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts

    def generate_network_statistics(self, network_data: Dict) -> Dict:
        """
        네트워크 통계 정보 생성

        Args:
            network_data: 네트워크 데이터

        Returns:
            통계 정보
        """
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        # 기본 통계
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": self._count_node_types(nodes),
            "edge_types": self._count_edge_types(edges),
        }

        # 네트워크 밀도 계산
        if len(nodes) > 1:
            max_possible_edges = len(nodes) * (len(nodes) - 1) / 2
            stats["density"] = (
                len(edges) / max_possible_edges if max_possible_edges > 0 else 0
            )
        else:
            stats["density"] = 0

        # 노드별 연결도 분석
        node_degrees = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            node_degrees[source] = node_degrees.get(source, 0) + 1
            node_degrees[target] = node_degrees.get(target, 0) + 1

        if node_degrees:
            stats["avg_degree"] = sum(node_degrees.values()) / len(node_degrees)
            stats["max_degree"] = max(node_degrees.values())
            stats["min_degree"] = min(node_degrees.values())
        else:
            stats["avg_degree"] = 0
            stats["max_degree"] = 0
            stats["min_degree"] = 0

        # 가장 연결도가 높은 노드들 (Top 5)
        top_connected = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]
        stats["top_connected_nodes"] = [
            {"node_id": node_id, "degree": degree} for node_id, degree in top_connected
        ]

        return stats

    def export_network_to_json(self, network_data: Dict, filename: str):
        """
        네트워크 데이터를 JSON 파일로 내보내기

        Args:
            network_data: 네트워크 데이터
            filename: 파일명
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(network_data, f, ensure_ascii=False, indent=2)
            logger.info(f"네트워크 데이터가 {filename}으로 내보내졌습니다.")
        except Exception as e:
            logger.error(f"네트워크 데이터 내보내기 실패: {e}")
            raise

    def get_network_evolution(
        self,
        target_company: str,
        time_periods: List[Tuple[date, date]],
        db: Optional[Session] = None,
    ) -> List[Dict]:
        """
        시간에 따른 네트워크 진화 추이 분석

        Args:
            target_company: 대상 기업
            time_periods: 분석할 기간들 [(start_date, end_date), ...]
            db: 데이터베이스 세션

        Returns:
            각 기간별 네트워크 데이터
        """
        if db is None:
            db = next(get_db())

        evolution_data = []

        for start_date, end_date in time_periods:
            network_data = self.generate_network_data(
                target_company=target_company,
                start_date=start_date,
                end_date=end_date,
                db=db,
            )

            period_data = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "network": network_data,
                "statistics": self.generate_network_statistics(network_data),
            }

            evolution_data.append(period_data)

        logger.info(f"네트워크 진화 데이터 생성 완료: {len(evolution_data)}개 기간")
        return evolution_data


# 싱글톤 인스턴스
network_visualizer = NetworkVisualizer()
