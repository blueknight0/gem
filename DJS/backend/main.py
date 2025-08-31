"""
DJS (Data-based Junction Search) 메인 애플리케이션
FastAPI 기반 오픈이노베이션 연구협력 네트워크 분석 시스템
"""

from fastapi import FastAPI, Request, Depends, Response, BackgroundTasks
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import os
import uvicorn
import logging
from pathlib import Path
from sqlalchemy.orm import Session
import logging.config

# API 라우터 임포트
from backend.api.search import router as search_router
from backend.api.embedding import router as embedding_router
from backend.api.extractor import router as extractor_router
from backend.api.rounds import router as rounds_router
from backend.api.review import router as review_router
from backend.api.visualization import router as visualization_router
from backend.api.scheduler import router as scheduler_router
from backend.api.auth import router as auth_router, get_jwt_settings
from backend.core.database import SessionLocal
from backend.utils.security import (
    decode_token,
    DEFAULT_JWT_SECRET,
    DEFAULT_JWT_ALGORITHM,
)

# 데이터베이스 초기화 및 세션
from backend.core.database import create_tables, get_db

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Data-based Junction Search (DJS)",
    description="오픈이노베이션 연구협력 네트워크 분석 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (프론트엔드 연결용)
origins = [
    "http://localhost:3000",  # React 개발 서버
    "http://localhost:5173",  # Vite 개발 서버
    # 프로덕션 환경의 프론트엔드 주소도 추가할 수 있습니다.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(search_router)
app.include_router(embedding_router)
app.include_router(extractor_router)
app.include_router(rounds_router)
app.include_router(review_router)
app.include_router(visualization_router)
app.include_router(scheduler_router)
app.include_router(auth_router)

# 정적 파일 서빙 (프론트엔드)
frontend_path = Path(__file__).parent / "static"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DJS - Data-based Junction Search</title>
        <link rel="icon" href="/favicon.ico">
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            .api-links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .api-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .api-card h3 {
                margin-top: 0;
                color: #333;
            }
            .api-card a {
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 5px;
            }
            .api-card a:hover {
                background: #5a6fd8;
            }

            /* 워크플로우 스타일 */
            .workflow-section {
                margin: 40px 0;
                padding: 30px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }

            .workflow-section h2 {
                text-align: center;
                color: #333;
                margin-bottom: 10px;
                font-size: 2.2em;
            }

            .workflow-description {
                text-align: center;
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }

            .workflow-steps {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
                margin-bottom: 30px;
            }

            .step-card {
                background: linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%);
                border: 2px solid #e1e8ed;
                border-radius: 15px;
                padding: 25px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .step-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                border-color: #667eea;
            }

            .step-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }

            .step-number {
                position: absolute;
                top: -15px;
                left: 20px;
                width: 35px;
                height: 35px;
                background: #667eea;
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 1.2em;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            }

            .step-content h3 {
                margin-top: 15px;
                margin-bottom: 10px;
                color: #333;
                font-size: 1.3em;
            }

            .step-content p {
                color: #666;
                line-height: 1.5;
                margin-bottom: 15px;
            }

            .step-actions {
                margin-top: 15px;
            }

            .btn-primary, .btn-secondary {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.9em;
            }

            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }

            .btn-secondary {
                background: #f8f9fa;
                color: #495057;
                border: 1px solid #dee2e6;
            }

            .btn-secondary:hover {
                background: #e9ecef;
                border-color: #adb5bd;
            }

            /* 빠른 실행 섹션 */
            .quick-actions {
                margin: 40px 0;
                padding: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                color: white;
                text-align: center;
            }

            .quick-actions h2 {
                margin-bottom: 20px;
                font-size: 1.8em;
            }

            .quick-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }

            .quick-btn {
                padding: 15px 30px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                font-size: 1em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .quick-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }

            /* 반응형 디자인 */
            @media (max-width: 768px) {
                .workflow-steps {
                    grid-template-columns: 1fr;
                }

                .quick-buttons {
                    flex-direction: column;
                    align-items: center;
                }

                .quick-btn {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 DJS (Data-based Junction Search)</h1>
            <p>오픈이노베이션 연구협력 네트워크 분석 시스템</p>
            <div class="debug-info" style="margin-top: 10px; font-size: 12px; color: #666;">
                <span id="connection-status">🔄 연결 확인 중...</span> |
                <span id="api-status">🔄 API 상태 확인 중...</span> |
                <span id="config-status">🔄 설정 확인 중...</span> |
                <span id="investigation-status" style="display:none; color:#0069d9; font-weight:bold;">진행중</span>
                <div style="margin-top: 5px;">
                    <button onclick="testAPIConnection()" style="background: none; border: 1px solid #667eea; color: #667eea; padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 11px;">테스트</button>
                    <button onclick="checkConfigStatus()" style="background: none; border: 1px solid #28a745; color: #28a745; padding: 2px 8px; border-radius: 4px; cursor: pointer; font-size: 11px; margin-left: 5px;">설정확인</button>
                </div>
            </div>
        </div>

        <!-- 워크플로우 섹션 -->
        <div class="workflow-section">
            <h2>🚀 DJS 워크플로우</h2>
            <p class="workflow-description">기본은 자동 워크플로우입니다. 수동 워크플로우는 별도 버튼으로 열 수 있습니다.</p>

            <div class="workflow-steps">
                <div class="step-card" onclick="quickStartInvestigation()">
                    <div class="step-number">1</div>
                    <div class="step-content">
                        <h3>🏢 기업 조사 시작</h3>
                        <p>대상 기업을 지정하여 전체 자동 워크플로우를 실행합니다.</p>
                        <div class="step-actions">
                            <button class="btn-primary">자동 실행</button>
                        </div>
                    </div>
                </div>

                <div class="step-card" onclick="openManualWorkflow()">
                    <div class="step-number">2</div>
                    <div class="step-content">
                        <h3>🧩 수동 워크플로우</h3>
                        <p>뉴스 검색·중복 제거·관계 추출을 단계별로 실행합니다.</p>
                        <div class="step-actions">
                            <button class="btn-secondary">열기</button>
                        </div>
                    </div>
                </div>

                <div class="step-card" onclick="openReviewModal()">
                    <div class="step-number">3</div>
                    <div class="step-content">
                        <h3>✅ 검토 및 승인</h3>
                        <p>추출된 관계를 확인하고 승인/거부/삭제를 수행합니다.</p>
                        <div class="step-actions">
                            <button class="btn-secondary">열기</button>
                        </div>
                    </div>
                </div>

                <div class="step-card" onclick="openVisualizationModal()">
                    <div class="step-number">4</div>
                    <div class="step-content">
                        <h3>📊 네트워크 시각화</h3>
                        <p>관계 네트워크를 미리보기 또는 새 탭으로 확인합니다.</p>
                        <div class="step-actions">
                            <button class="btn-secondary">열기</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 빠른 실행 섹션 -->
        <div class="quick-actions">
            <h2>⚡ 빠른 실행</h2>
            <div class="quick-buttons">
                <button class="quick-btn" onclick="quickStartInvestigation()">🚀 자동 워크플로우 실행</button>
                <button class="quick-btn" onclick="openManualWorkflow()">🧩 수동 워크플로우 열기</button>
                <button class="quick-btn" onclick="openReviewModal()">✅ 검토 및 승인</button>
                <button class="quick-btn" onclick="openVisualizationModal()">📊 네트워크 시각화</button>
                <button class="quick-btn" onclick="showSchedulerModal()">⏰ 스케줄러 설정</button>
                <button class="quick-btn" onclick="showSettingsModal()">⚙️ 시스템 설정</button>
                <button class="quick-btn" onclick="openAuthModal()">🔐 로그인</button>
                <button class="quick-btn" onclick="testAPIConnection()">🧪 API 연결 테스트</button>
                <button class="quick-btn" onclick="demoProgress()">🎬 진행 상황 데모</button>
            </div>
        </div>

        <!-- 기존 API 카드들 -->
        <div class="api-links">

            <div class="api-card">
                <h3>🧠 임베딩 분석</h3>
                <p>텍스트 임베딩을 활용한 중복 제거</p>
                <a href="/docs#/embedding">API 문서</a>
                <a href="/api/embedding/stats">통계</a>
            </div>

            <div class="api-card">
                <h3>🤖 관계 추출</h3>
                <p>Gemini-2.5-flash-lite 기반 협력 관계 추출</p>
                <a href="/docs#/extractor">API 문서</a>
                <a href="/api/extractor/stats">통계</a>
            </div>

            <div class="api-card">
                <h3>🔄 라운드 조사</h3>
                <p>기업 조사 라운드 관리</p>
                <a href="/api/rounds/pending">대기중</a>
                <a href="/docs#/rounds">API 문서</a>
            </div>

            <div class="api-card">
                <h3>✅ 관계 검토</h3>
                <p>추출된 관계 검토 및 수정</p>
                <a href="/api/review/relations">검토하기</a>
                <a href="/docs#/review">API 문서</a>
            </div>

            <div class="api-card">
                <h3>📊 네트워크 시각화</h3>
                <p>기업 관계 네트워크 시각화</p>
                <a href="/api/visualization/network">네트워크 보기</a>
                <a href="/docs#/visualization">API 문서</a>
            </div>

            <div class="api-card">
                <h3>⏰ 스케줄러</h3>
                <p>자동화 작업 스케줄링</p>
                <a href="/api/scheduler/jobs">작업 관리</a>
                <a href="/docs#/scheduler">API 문서</a>
            </div>

            <div class="api-card">
                <h3>📊 시스템 상태</h3>
                <p>API 키 및 시스템 설정 상태</p>
                <a href="/api/search/credentials/status">검색 API</a>
                <a href="/api/extractor/api-key/status">LLM API</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>© 2024 DJS - Data-based Junction Search System</p>
        </div>

        <!-- 모달 컨테이너 -->
        <div id="workflowModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <div id="modalContent"></div>
            </div>
        </div>

        <script>
            // 전역 fetch 인터셉트: 저장된 토큰이 있으면 Authorization 헤더 자동 추가
            (function(){
                const originalFetch = window.fetch;
                window.fetch = function(input, init){
                    const token = localStorage.getItem('djs_token');
                    if (token) {
                        init = init || {};
                        init.headers = { ...(init?.headers||{}), 'Authorization': `Bearer ${token}` };
                    }
                    return originalFetch(input, init);
                }
            })();
            // 워크플로우 모달 관련 함수들
            function showWorkflowModal(step) {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                let content = '';

                switch(step) {
                    case 'company_investigation':
                        content = `
                            <h2>🏢 기업 조사 시작</h2>
                            <p>조사할 기업명을 입력하세요.</p>
                            <form onsubmit="startInvestigation(event)">
                                <div class="form-group">
                                    <label for="companyName">기업명:</label>
                                    <input type="text" id="companyName" placeholder="예: 삼성전자" required>
                                </div>
                                <div class="form-group">
                                    <label for="maxRounds">최대 라운드 수:</label>
                                    <input type="number" id="maxRounds" value="3" min="1" max="10">
                                </div>
                                <button type="submit" class="btn-primary">조사 시작</button>
                            </form>
                        `;
                        break;

                    case 'news_search':
                        content = `
                            <h2>🔍 뉴스 검색</h2>
                            <p>기업명을 입력하여 관련 뉴스를 검색합니다.</p>
                            <form onsubmit="searchNews(event)">
                                <div class="form-group">
                                    <label for="searchCompany">기업명:</label>
                                    <input type="text" id="searchCompany" placeholder="예: 삼성전자" required>
                                </div>
                                <div class="form-group">
                                    <label for="maxResults">최대 결과 수:</label>
                                    <input type="number" id="maxResults" value="50" min="1" max="100">
                                </div>
                                <button type="submit" class="btn-secondary">검색 실행</button>
                            </form>
                        `;
                        break;

                    case 'deduplication':
                        content = `
                            <h2>🧠 중복 제거</h2>
                            <p>저장된 뉴스에서 중복 기사를 제거합니다.</p>
                            <form onsubmit="runDeduplication(event)">
                                <div class="form-group">
                                    <label for="similarityThreshold">유사도 임계값:</label>
                                    <input type="number" id="similarityThreshold" value="0.85" min="0.1" max="1.0" step="0.05">
                                </div>
                                <button type="submit" class="btn-secondary">중복 제거 실행</button>
                            </form>
                        `;
                        break;

                    case 'relation_extraction':
                        content = `
                            <h2>🤖 관계 추출</h2>
                            <p>뉴스에서 기업 관계를 자동으로 추출합니다.</p>
                            <form onsubmit="extractRelations(event)">
                                <div class="form-group">
                                    <label for="batchSize">배치 크기:</label>
                                    <input type="number" id="batchSize" value="10" min="1" max="50">
                                </div>
                                <button type="submit" class="btn-secondary">관계 추출 실행</button>
                            </form>
                        `;
                        break;

                    case 'review_approval':
                        content = `
                            <h2>✅ 관계 검토</h2>
                            <p>추출된 관계를 검토하고 승인합니다.</p>
                            <div class="review-actions">
                                <button onclick="openReviewPage()" class="btn-primary">관계 검토하기</button>
                                <button onclick="viewPendingRounds()" class="btn-secondary">라운드 현황</button>
                            </div>
                        `;
                        break;

                    case 'visualization':
                        content = `
                            <h2>📊 네트워크 시각화</h2>
                            <p>기업 간 협력 관계 네트워크를 시각화합니다.</p>
                            <form onsubmit="generateNetwork(event)">
                                <div class="form-group">
                                    <label for="networkCompany">중심 기업 (선택사항):</label>
                                    <input type="text" id="networkCompany" placeholder="예: 삼성전자">
                                </div>
                                <div class="form-group">
                                    <label for="maxDepth">네트워크 깊이:</label>
                                    <input type="number" id="maxDepth" value="3" min="1" max="5">
                                </div>
                                <button type="submit" class="btn-secondary">네트워크 생성</button>
                            </form>
                        `;
                        break;
                }

                modalContent.innerHTML = content;
                modal.style.display = 'block';
            }

            // 수동 워크플로우 모달
            function openManualWorkflow() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');
                modalContent.innerHTML = `
                    <h2>🧩 수동 워크플로우</h2>
                    <p>원하는 단계를 선택해 개별 실행할 수 있습니다.</p>
                    <div style="display:grid; gap:10px;">
                        <button class="btn-secondary" onclick="showNewsSearchModal()">🔍 뉴스 검색</button>
                        <button class="btn-secondary" onclick="showDeduplicationModal()">🧠 중복 제거</button>
                        <button class="btn-secondary" onclick="showRelationExtractionModal()">🤖 관계 추출</button>
                    </div>
                `;
                modal.style.display = 'block';
            }

            // 검토 및 승인 모달
            async function openReviewModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');
                modalContent.innerHTML = `
                    <h2>✅ 검토 및 승인</h2>
                    <div style="margin-bottom:10px; display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                        <input id="relSearchInput" placeholder="기업/내용 검색" style="flex:1; padding:6px 10px; border:1px solid #ddd; border-radius:8px;"/>
                        <button class="btn-secondary" onclick="filterReviewList()">검색</button>
                        <button class="btn-secondary" onclick="loadExistingRelations()">기존 관계 불러오기</button>
                        <button class="btn-secondary" style="background:#f8d7da; color:#721c24; border-color:#f5c6cb;" onclick="deleteAllFromCurrentList()">현재 목록 전체 삭제</button>
                    </div>
                    <div id="existing-relations" style="display:none; background:#f8f9fa; border:1px solid #eee; border-radius:8px; padding:10px; margin-bottom:10px; max-height:180px; overflow:auto;"></div>
                    <div id="review-list">불러오는 중...</div>
                `;
                modal.style.display = 'block';
                try {
                    const origin = window.location.origin || '';
                    const res = await fetch(new URL('/api/review/relations?limit=20', origin));
                    const data = await res.json();
                    window.__reviewItems = (data.data?.relations || []);
                    const items = window.__reviewItems.map(r => {
                        const companyA = r.company_a?.name || r.company_a || '-';
                        const companyB = r.company_b?.name || r.company_b || '-';
                        const newsUrl = r.news_url || r.news?.url || null;
                        return `
                        <div style="border:1px solid #eee; border-radius:8px; padding:12px; margin:8px 0;">
                            <div style="display:flex; justify-content:space-between; gap:8px;">
                                <div><b>조사기업</b>: ${companyA}</div>
                                <div><b>대상기업</b>: ${companyB}</div>
                            </div>
                            <div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
                                <label>유형:</label>
                                <select id="type-${r.id}" style="padding:4px 8px; border:1px solid #ddd; border-radius:6px; width:180px;">
                                  <option ${r.relation_type==='MOU'?'selected':''}>MOU</option>
                                  <option ${r.relation_type==='JOINT_RESEARCH'?'selected':''}>JOINT_RESEARCH</option>
                                  <option ${r.relation_type==='INVESTMENT'?'selected':''}>INVESTMENT</option>
                                  <option ${r.relation_type==='MERGER'?'selected':''}>MERGER</option>
                                  <option ${r.relation_type==='TECHNOLOGY_TRANSFER'?'selected':''}>TECHNOLOGY_TRANSFER</option>
                                  <option ${r.relation_type==='PARTNERSHIP'?'selected':''}>PARTNERSHIP</option>
                                  <option ${r.relation_type==='COLLABORATION'?'selected':''}>COLLABORATION</option>
                                  <option ${r.relation_type==='FUNDING'?'selected':''}>FUNDING</option>
                                </select>
                                <span style="margin-left:8px;">신뢰도: ${r.confidence_score}</span>
                            </div>
                            <div style="margin-top:6px;">
                                <label>내용:</label>
                                <textarea id="content-${r.id}" style="width:100%; padding:6px 8px; border:1px solid #ddd; border-radius:6px;" rows="3">${r.relation_content}</textarea>
                            </div>
                            ${newsUrl ? `<div style=\"margin-top:6px;\"><a href=\"${newsUrl}\" target=\"_blank\">📰 기사 보기</a></div>` : ''}
                            <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
                                <button class="btn-primary" onclick="approveRelation(${r.id})">승인</button>
                                <button class="btn-secondary" onclick="saveEditedRelation(${r.id})">수정 저장</button>
                                <button class="btn-secondary" style="background:#f8d7da; color:#721c24; border-color:#f5c6cb;" onclick="deleteRelation(${r.id})">삭제</button>
                            </div>
                        </div>`;
                    }).join('');
                    document.getElementById('review-list').innerHTML = items || '대상 없음';
                } catch (e) {
                    document.getElementById('review-list').textContent = '불러오기 실패';
                }
            }

            function filterReviewList() {
                const q = (document.getElementById('relSearchInput').value || '').toLowerCase();
                const list = window.__reviewItems || [];
                const filtered = list.filter(r => {
                    const a = (r.company_a?.name || r.company_a || '').toLowerCase();
                    const b = (r.company_b?.name || r.company_b || '').toLowerCase();
                    const c = (r.relation_content || '').toLowerCase();
                    return a.includes(q) || b.includes(q) || c.includes(q);
                });
                window.__filteredIds = filtered.map(r => r.id);
                document.getElementById('review-list').innerHTML = filtered.map(r => `
                    <div style="border:1px solid #eee; border-radius:8px; padding:12px; margin:8px 0;">
                        <div style="display:flex; justify-content:space-between; gap:8px;">
                            <div><b>조사기업</b>: ${r.company_a?.name || r.company_a || '-'}</div>
                            <div><b>대상기업</b>: ${r.company_b?.name || r.company_b || '-'}</div>
                        </div>
                        <div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
                            <label>유형:</label>
                            <input id="type-${r.id}" value="${r.relation_type}" style="padding:4px 8px; border:1px solid #ddd; border-radius:6px; width:160px;"/>
                            <span style="margin-left:8px;">신뢰도: ${r.confidence_score}</span>
                        </div>
                        <div style="margin-top:6px;">
                            <label>내용:</label>
                            <textarea id="content-${r.id}" style="width:100%; padding:6px 8px; border:1px solid #ddd; border-radius:6px;" rows="3">${r.relation_content}</textarea>
                        </div>
                        <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
                            <button class="btn-primary" onclick="approveRelation(${r.id})">승인</button>
                            <button class="btn-secondary" onclick="saveEditedRelation(${r.id})">수정 저장</button>
                        </div>
                    </div>
                `).join('');
            }

            async function loadExistingRelations() {
                try {
                    const origin = window.location.origin || '';
                    const res = await fetch(new URL('/api/review/relations?limit=50', origin));
                    const data = await res.json();
                    const items = data.data?.relations || [];
                    const html = items.map(r => `<div>- [${r.relation_type}] ${(r.company_a?.name||'')} - ${(r.company_b?.name||'')} : ${(r.relation_content||'')}</div>`).join('');
                    const box = document.getElementById('existing-relations');
                    box.innerHTML = html || '기존 관계가 없습니다.';
                    box.style.display = 'block';
                } catch (e) {
                    alert('기존 관계 로드 실패');
                }
            }

            async function saveEditedRelation(id) {
                const type = (document.getElementById(`type-${id}`) || {}).value;
                const content = (document.getElementById(`content-${id}`) || {}).value;
                const body = { relation_type: type, relation_content: content };
                const origin = window.location.origin || '';
                const res = await fetch(new URL(`/api/review/relation/${id}?modified_by=system`, origin), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
                const data = await res.json();
                alert(data.message || '저장 완료');
                openReviewModal();
            }

            async function deleteRelation(id) {
                if (!confirm('이 관계를 삭제하시겠습니까?')) return;
                const origin = window.location.origin || '';
                const res = await fetch(new URL(`/api/review/relation/${id}`, origin), { method: 'DELETE' });
                const data = await res.json();
                alert(data.message || '삭제 완료');
                openReviewModal();
            }

            async function deleteAllFromCurrentList() {
                const ids = window.__filteredIds || (window.__reviewItems||[]).map(r => r.id);
                if (!ids.length) { alert('삭제할 항목이 없습니다.'); return; }
                if (!confirm(`현재 목록 ${ids.length}건을 삭제하시겠습니까?`)) return;
                const origin = window.location.origin || '';
                const res = await fetch(new URL('/api/review/relations/bulk-delete', origin), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ relation_ids: ids })
                });
                const data = await res.json();
                alert(data.message || '삭제 완료');
                openReviewModal();
            }

            async function approveRelation(id) {
                if (!confirm('이 관계를 승인하시겠습니까?')) return;
                const origin = window.location.origin || '';
                const res = await fetch(new URL(`/api/review/relation/${id}/approve?approved_by=system`, origin), { method: 'PUT' });
                const data = await res.json();
                alert(data.message || '승인 완료');
                openReviewModal();
            }

            async function rejectRelation(id) {
                if (!confirm('이 관계를 거부하시겠습니까?')) return;
                const origin = window.location.origin || '';
                const url = new URL(`/api/review/relation/${id}/reject?rejected_by=system&reason=reject`, origin);
                const res = await fetch(url, { method: 'PUT' });
                const data = await res.json();
                alert(data.message || '거부 완료');
                openReviewModal();
            }

            // 네트워크 시각화 모달
            async function openVisualizationModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');
                modalContent.innerHTML = `
                    <h2>📊 네트워크 시각화</h2>
                    <div class="form-group">
                        <label for="vizCompany">중심 기업</label>
                        <input list="companyList" id="vizCompany" placeholder="기업 검색 또는 선택" />
                        <datalist id="companyList"></datalist>
                        <button class="btn-secondary" onclick="loadCompanies()">기업 목록 불러오기</button>
                    </div>
                    <div class="form-group">
                        <label for="vizDepth">깊이</label>
                        <input type="number" id="vizDepth" value="3" min="1" max="5" />
                    </div>
                    <div class="review-actions">
                        <button class="btn-primary" onclick="previewNetwork()">미리보기</button>
                        <button class="btn-secondary" onclick="openNetworkPage()">새 탭에서 열기</button>
                    </div>
                    <canvas id="vizCanvas" width="480" height="360" style="background:#fafafa; border:1px solid #eee; border-radius:8px;"></canvas>
                `;
                modal.style.display = 'block';
            }

            async function loadCompanies() {
                try {
                    const origin = window.location.origin || '';
                    const res = await fetch(new URL('/api/visualization/network/companies', origin));
                    const data = await res.json();
                    const list = data.data?.companies || [];
                    const dl = document.getElementById('companyList');
                    dl.innerHTML = list.map(c => `<option value="${c.name}"></option>`).join('');
                } catch (e) {
                    alert('기업 목록 불러오기 실패');
                }
            }

            async function previewNetwork() {
                const company = document.getElementById('vizCompany').value;
                const depth = document.getElementById('vizDepth').value;
                const url = company ? `/api/visualization/network?target_company=${encodeURIComponent(company)}&max_depth=${depth}` : `/api/visualization/network?max_depth=${depth}`;
                const res = await fetch(url);
                const data = await res.json();
                drawSimpleNetwork(data);
            }

            function openNetworkPage() {
                const company = document.getElementById('vizCompany').value;
                const depth = document.getElementById('vizDepth').value;
                const url = company ? `/visualize?target_company=${encodeURIComponent(company)}&max_depth=${depth}` : `/visualize?max_depth=${depth}`;
                window.open(url, '_blank');
            }

            // 간단 원형 네트워크 렌더링
            function drawSimpleNetwork(data) {
                const canvas = document.getElementById('vizCanvas');
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const nodes = data.nodes || [];
                const edges = data.edges || [];
                const cx = canvas.width / 2;
                const cy = canvas.height / 2;
                const r = Math.min(cx, cy) - 30;

                // 노드 위치 계산 (원형 배치)
                const positions = {};
                nodes.forEach((n, i) => {
                    const angle = (2 * Math.PI * i) / Math.max(1, nodes.length);
                    positions[n.id] = {
                        x: cx + r * Math.cos(angle),
                        y: cy + r * Math.sin(angle),
                        color: n.color || '#667eea',
                        name: n.name || n.id
                    };
                });

                // 엣지 그리기
                ctx.strokeStyle = '#bbb';
                edges.forEach(e => {
                    const s = positions[e.source];
                    const t = positions[e.target];
                    if (!s || !t) return;
                    ctx.beginPath();
                    ctx.moveTo(s.x, s.y);
                    ctx.lineTo(t.x, t.y);
                    ctx.stroke();
                });

                // 노드 그리기
                nodes.forEach(n => {
                    const p = positions[n.id];
                    if (!p) return;
                    ctx.beginPath();
                    ctx.fillStyle = p.color;
                    ctx.arc(p.x, p.y, 8, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.fillStyle = '#333';
                    ctx.font = '12px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText(p.name, p.x, p.y - 12);
                });
            }
            function closeModal() {
                document.getElementById('workflowModal').style.display = 'none';
            }

            // 진행 상황을 표시하는 모달
            function showProgressModal(title, steps) {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                let progressHTML = `
                    <h2>${title}</h2>
                    <div class="progress-container">
                `;

                steps.forEach((step, index) => {
                    progressHTML += `
                        <div class="progress-step" id="step-${index}">
                            <div class="step-icon" id="step-icon-${index}">⏳</div>
                            <div class="step-content">
                                <div class="step-title">${step.title}</div>
                                <div class="step-description" id="step-desc-${index}">${step.description}</div>
                            </div>
                        </div>
                    `;
                });

                progressHTML += `
                    </div>
                    <div class="progress-actions">
                        <button onclick="closeModal()" class="btn-secondary">닫기</button>
                    </div>
                `;

                modalContent.innerHTML = progressHTML;
                modal.style.display = 'block';

                return steps.map((_, index) => `step-${index}`);
            }

            // 진행 단계 업데이트 함수
            function updateProgressStep(stepId, status, message = '') {
                const stepElement = document.getElementById(stepId);
                const iconElement = document.getElementById(`step-icon-${stepId.split('-')[1]}`);
                const descElement = document.getElementById(`step-desc-${stepId.split('-')[1]}`);

                if (status === 'loading') {
                    iconElement.textContent = '🔄';
                    iconElement.style.animation = 'spin 1s linear infinite';
                    stepElement.classList.add('loading');
                } else if (status === 'success') {
                    iconElement.textContent = '✅';
                    iconElement.style.animation = 'none';
                    stepElement.classList.remove('loading');
                    stepElement.classList.add('completed');
                } else if (status === 'error') {
                    iconElement.textContent = '❌';
                    iconElement.style.animation = 'none';
                    stepElement.classList.remove('loading');
                    stepElement.classList.add('error');
                }

                if (message) {
                    descElement.textContent = message;
                }
            }

            // 빠른 실행 함수들
            async function quickStartInvestigation() {
                const company = prompt('조사할 기업명을 입력하세요:', '삼성전자');
                if (company) {
                    console.log('기업 조사 시작:', company);
                    const inv = document.getElementById('investigation-status');
                    if (inv) { inv.style.display = 'inline'; inv.textContent = '🟡 조사 진행중...'; }

                    // 진행 상황 모달 표시
                    const steps = [
                        { title: '기업 조사 준비', description: '조사 설정을 확인하는 중...' },
                        { title: '데이터베이스 연결', description: '데이터베이스에 연결하는 중...' },
                        { title: '조사 라운드 생성', description: '조사 라운드를 생성하는 중...' },
                        { title: '완료', description: '조사가 성공적으로 시작되었습니다.' }
                    ];

                    const stepIds = showProgressModal(`🏢 ${company} 기업 조사`, steps);

                    try {
                        // 1단계: 준비
                        updateProgressStep(stepIds[0], 'loading', '조사 설정을 확인하는 중...');
                        await new Promise(resolve => setTimeout(resolve, 1000)); // 시뮬레이션

                        // 2단계: 데이터베이스 연결
                        updateProgressStep(stepIds[0], 'success', '조사 설정 확인 완료');
                        updateProgressStep(stepIds[1], 'loading', '데이터베이스에 연결하는 중...');

                        // URL 파라미터 방식으로 변경
                        const url = `/api/rounds/investigate?target_company=${encodeURIComponent(company)}&max_rounds=3`;
                        console.log('API 요청 URL:', url);

                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });

                        console.log('응답 상태:', response.status);
                        updateProgressStep(stepIds[1], 'success', '데이터베이스 연결 완료');

                        // 3단계: 라운드 생성
                        updateProgressStep(stepIds[2], 'loading', '조사 라운드를 생성하는 중...');
                        const result = await response.json();
                        console.log('응답 데이터:', result);

                        await new Promise(resolve => setTimeout(resolve, 500)); // 시뮬레이션

                        if (result.success) {
                            updateProgressStep(stepIds[2], 'success', '조사 라운드 생성 완료');
                            updateProgressStep(stepIds[3], 'success', `기업 조사 시작 성공! 라운드 ID: ${result.data?.round_id || '생성됨'}`);

                            // 2초 후 자동 닫기
                            setTimeout(() => {
                                if (inv) { inv.textContent = '🟢 조사 완료'; setTimeout(()=>{ inv.style.display='none'; },3000); }
                                alert(`🎉 기업 조사 시작 완료!\\n\\n기업: ${company}\\n결과: ${result.message}`);
                            }, 1000);
                        } else {
                            updateProgressStep(stepIds[2], 'error', '조사 라운드 생성 실패');
                            updateProgressStep(stepIds[3], 'error', result.message || '알 수 없는 오류');

                            setTimeout(() => {
                                alert('❌ 오류: ' + (result.message || '알 수 없는 오류'));
                            }, 1000);
                        }
                    } catch (error) {
                        console.error('네트워크 오류:', error);
                        updateProgressStep(stepIds[1], 'error', '네트워크 연결 실패');
                        updateProgressStep(stepIds[2], 'error', '조사 중단');
                        updateProgressStep(stepIds[3], 'error', error.message);

                        setTimeout(() => {
                            if (inv) { inv.textContent = '🔴 조사 실패'; setTimeout(()=>{ inv.style.display='none'; },3000); }
                            alert('❌ 네트워크 오류: ' + error.message);
                        }, 1000);
                    }
                }
            }

            function showSchedulerModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                modalContent.innerHTML = `
                    <h2>⏰ 스케줄러 설정</h2>
                    <p>자동화된 조사 작업을 설정합니다.</p>
                    <form onsubmit="scheduleJob(event)">
                        <div class="form-group">
                            <label for="schedCompany">기업명:</label>
                            <input type="text" id="schedCompany" placeholder="예: 삼성전자" required>
                        </div>
                        <div class="form-group">
                            <label for="cronExpression">실행 주기:</label>
                            <select id="cronExpression">
                                <option value="0 9 * * 1">매주 월요일 9시</option>
                                <option value="0 9 * * *">매일 9시</option>
                                <option value="0 */6 * * *">6시간마다</option>
                            </select>
                        </div>
                        <button type="submit" class="btn-primary">스케줄러 설정</button>
                    </form>
                `;

                modal.style.display = 'block';
            }

            function showSettingsModal() {
                window.open('/docs', '_blank');
            }

            // 인증 모달 및 핸들러
            function openAuthModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');
                const logged = !!localStorage.getItem('djs_token');
                const email = localStorage.getItem('djs_email') || '';
                modalContent.innerHTML = `
                    <h2>🔐 로그인</h2>
                    <div id="auth-status" style="margin-bottom:8px; color:${logged?'#28a745':'#dc3545'};">
                        ${logged ? `로그인됨: ${email}` : '로그아웃 상태'}
                    </div>
                    <form onsubmit="login(event)">
                        <div class="form-group">
                            <label for="authEmail">이메일</label>
                            <input type="email" id="authEmail" placeholder="you@example.com" required value="${email}">
                        </div>
                        <div class="form-group">
                            <label for="authPassword">비밀번호</label>
                            <input type="password" id="authPassword" placeholder="********" required>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button type="submit" class="btn-primary">로그인</button>
                            <button type="button" class="btn-secondary" onclick="registerAccount()">회원가입</button>
                            <button type="button" class="btn-secondary" onclick="logout()">로그아웃</button>
                        </div>
                    </form>
                `;
                modal.style.display = 'block';
            }

            async function registerAccount() {
                const email = document.getElementById('authEmail').value;
                const password = document.getElementById('authPassword').value;
                try {
                    const res = await fetch('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
                    const data = await res.json();
                    alert(data.detail || data.message || '회원가입 완료');
                } catch (e) {
                    alert('회원가입 실패');
                }
            }

            async function login(event) {
                event.preventDefault();
                const email = document.getElementById('authEmail').value;
                const password = document.getElementById('authPassword').value;
                try {
                    const body = new URLSearchParams();
                    body.set('username', email);
                    body.set('password', password);
                    const res = await fetch('/api/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
                    const data = await res.json();
                    if (data.access_token) {
                        localStorage.setItem('djs_token', data.access_token);
                        localStorage.setItem('djs_email', email);
                        alert('로그인 성공');
                        openAuthModal();
                    } else {
                        alert('로그인 실패');
                    }
                } catch (e) {
                    alert('로그인 오류');
                }
            }

            function logout() {
                localStorage.removeItem('djs_token');
                localStorage.removeItem('djs_email');
                openAuthModal();
            }

            // 워크플로우 단계별 모달 함수들
            function showNewsSearchModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                modalContent.innerHTML = `
                    <h2>🔍 뉴스 검색</h2>
                    <p>기업명을 입력하고 기간을 선택하여 관련 뉴스를 검색합니다.</p>
                    <form onsubmit="searchNews(event)">
                        <div class="form-group">
                            <label for="searchCompany">기업명:</label>
                            <input type="text" id="searchCompany" placeholder="예: 삼성전자" required>
                        </div>
                        <div class="form-group">
                            <label>검색 기간:</label>
                            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                                <label><input type="radio" name="period" value="all" checked> 전기간</label>
                                <label><input type="radio" name="period" value="since_last"> 최종 검색 이후</label>
                                <label><input type="radio" name="period" value="custom"> 사용자 지정</label>
                                <input type="date" id="startDate" disabled>
                                <span>~</span>
                                <input type="date" id="endDate" disabled>
                                <button type="button" class="btn-secondary" onclick="fillLastSearchDates()">최종 검색 불러오기</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="maxResults">최대 결과 수:</label>
                            <input type="number" id="maxResults" value="50" min="1" max="100">
                        </div>
                        <button type="submit" class="btn-secondary">검색 실행</button>
                    </form>
                `;

                modal.style.display = 'block';
            }

            // 기간 라디오 변경에 따라 date 활성화
            document.addEventListener('change', (e) => {
                if (e.target && e.target.name === 'period') {
                    const custom = e.target.value === 'custom';
                    document.getElementById('startDate').disabled = !custom;
                    document.getElementById('endDate').disabled = !custom;
                }
            });

            async function fillLastSearchDates() {
                const company = document.getElementById('searchCompany').value;
                if (!company) { alert('기업명을 먼저 입력하세요'); return; }
                try {
                    const res = await fetch(`/api/search/last-search-date?company_name=${encodeURIComponent(company)}`);
                    const data = await res.json();
                    const last = data.data?.last_published_date;
                    if (last) {
                        document.querySelector('input[name="period"][value="since_last"]').checked = true;
                        const sd = document.getElementById('startDate');
                        const ed = document.getElementById('endDate');
                        sd.disabled = true; ed.disabled = true;
                        sd.value = last;
                        ed.valueAsDate = new Date();
                    } else {
                        alert('이 기업에 대한 기존 검색 기록이 없습니다.');
                    }
                } catch (e) {
                    alert('마지막 검색일 조회 실패');
                }
            }

            function showDeduplicationModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                modalContent.innerHTML = `
                    <h2>🧠 중복 제거</h2>
                    <p>저장된 뉴스에서 중복 기사를 제거합니다.</p>
                    <form onsubmit="runDeduplication(event)">
                        <div class="form-group">
                            <label for="similarityThreshold">유사도 임계값:</label>
                            <input type="number" id="similarityThreshold" value="0.85" min="0.1" max="1.0" step="0.05">
                        </div>
                        <button type="submit" class="btn-secondary">중복 제거 실행</button>
                    </form>
                `;

                modal.style.display = 'block';
            }

            function showRelationExtractionModal() {
                const modal = document.getElementById('workflowModal');
                const modalContent = document.getElementById('modalContent');

                modalContent.innerHTML = `
                    <h2>🤖 관계 추출</h2>
                    <p>뉴스에서 기업 관계를 자동으로 추출합니다.</p>
                    <form onsubmit="extractRelations(event)">
                        <div class="form-group">
                            <label for="batchSize">배치 크기:</label>
                            <input type="number" id="batchSize" value="10" min="1" max="50">
                        </div>
                        <button type="submit" class="btn-secondary">관계 추출 실행</button>
                    </form>
                `;

                modal.style.display = 'block';
            }

            // API 연결 테스트 함수
            async function testAPIConnection() {
                console.log('API 연결 테스트 시작...');

                try {
                    // 기본 헬스체크
                    console.log('1. 헬스체크 테스트...');
                    const healthResponse = await fetch('/health');
                    const healthData = await healthResponse.json();
                    console.log('헬스체크 결과:', healthData);

                    // 간단한 테스트 엔드포인트
                    console.log('2. 테스트 엔드포인트...');
                    const testResponse = await fetch('/test');
                    const testData = await testResponse.json();
                    console.log('테스트 엔드포인트 결과:', testData);

                    // 조사 엔드포인트 테스트
                    console.log('3. 조사 엔드포인트 테스트...');
                    const investigationResponse = await fetch('/test-investigation?company_name=테스트기업', {
                        method: 'POST'
                    });
                    const investigationData = await investigationResponse.json();
                    console.log('조사 엔드포인트 결과:', investigationData);

                    // 성공 메시지
                    alert(`✅ API 연결 테스트 성공!\\n\\n결과:\\n- 헬스체크: ${healthData.status}\\n- 테스트: ${testData.message}\\n- 조사: ${investigationData.message}\\n\\n브라우저 콘솔(F12)에서 자세한 로그를 확인하세요.`);

                } catch (error) {
                    console.error('API 연결 테스트 실패:', error);
                    alert(`❌ API 연결 실패: ${error.message}\\n\\n브라우저 콘솔(F12)에서 자세한 오류 정보를 확인하세요.`);
                }
            }

            // 폼 제출 함수들
            async function startInvestigation(event) {
                event.preventDefault();
                const companyName = document.getElementById('companyName').value;
                const maxRounds = document.getElementById('maxRounds').value;

                console.log('모달에서 기업 조사 시작:', companyName, maxRounds);

                try {
                    // URL 파라미터 방식으로 변경
                    const url = `/api/rounds/investigate?target_company=${encodeURIComponent(companyName)}&max_rounds=${maxRounds}`;
                    console.log('API 요청 URL:', url);

                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });

                    console.log('응답 상태:', response.status);
                    const result = await response.json();
                    console.log('응답 데이터:', result);

                    if (result.success) {
                        alert(`기업 조사 시작 성공!\\n결과: ${result.message}`);
                        closeModal();
                    } else {
                        alert('오류: ' + (result.message || '알 수 없는 오류'));
                    }
                } catch (error) {
                    console.error('네트워크 오류:', error);
                    alert('네트워크 오류: ' + error.message);
                }
            }

            async function searchNews(event) {
                event.preventDefault();
                const company = document.getElementById('searchCompany').value;
                const maxResults = document.getElementById('maxResults').value;
                const period = document.querySelector('input[name="period"]:checked')?.value;
                let startDate = undefined, endDate = undefined;
                if (period === 'custom') {
                    startDate = document.getElementById('startDate').value || undefined;
                    endDate = document.getElementById('endDate').value || undefined;
                } else if (period === 'since_last') {
                    startDate = document.getElementById('startDate').value || undefined;
                    endDate = document.getElementById('endDate').value || undefined;
                }

                // 진행 상황 모달 표시
                const steps = [
                    { title: '검색 준비', description: '검색 설정을 확인하는 중...' },
                    { title: '네이버 API 연결', description: '네이버 검색 API에 연결하는 중...' },
                    { title: '뉴스 수집', description: '관련 뉴스 기사를 수집하는 중...' },
                    { title: '완료', description: '뉴스가 성공적으로 수집되었습니다.' }
                ];

                const stepIds = showProgressModal(`🔍 ${company} 뉴스 검색`, steps);

                try {
                    // 1단계: 준비
                    updateProgressStep(stepIds[0], 'loading', '검색 설정을 확인하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 500));

                    // 2단계: API 연결
                    updateProgressStep(stepIds[0], 'success', '검색 설정 확인 완료');
                    updateProgressStep(stepIds[1], 'loading', '네이버 검색 API에 연결하는 중...');

                    let url = `/api/search/news?company_name=${encodeURIComponent(company)}&max_results=${maxResults}`;
                    if (startDate) url += `&start_date=${startDate}`;
                    if (endDate) url += `&end_date=${endDate}`;
                    const response = await fetch(url);

                    // 3단계: 뉴스 수집
                    updateProgressStep(stepIds[1], 'success', '네이버 검색 API 연결 완료');
                    updateProgressStep(stepIds[2], 'loading', '관련 뉴스 기사를 수집하는 중...');

                    const result = await response.json();

                    if (result.success) {
                        updateProgressStep(stepIds[2], 'success', `총 ${result.data.length}개의 뉴스 발견`);
                        updateProgressStep(stepIds[3], 'success', '뉴스가 성공적으로 수집되었습니다.');

                        setTimeout(() => {
                            alert(`🎉 뉴스 검색 완료!\n\n기업: ${company}\n발견된 뉴스: ${result.data.length}개`);
                            closeModal();
                        }, 1000);
                    } else {
                        updateProgressStep(stepIds[2], 'error', '뉴스 수집 실패');
                        updateProgressStep(stepIds[3], 'error', result.message || '알 수 없는 오류');

                        setTimeout(() => {
                            alert('❌ 오류: ' + (result.message || '알 수 없는 오류'));
                        }, 1000);
                    }
                } catch (error) {
                    updateProgressStep(stepIds[1], 'error', 'API 연결 실패');
                    updateProgressStep(stepIds[2], 'error', '수집 중단');
                    updateProgressStep(stepIds[3], 'error', error.message);

                    setTimeout(() => {
                        alert('❌ 네트워크 오류: ' + error.message);
                    }, 1000);
                }
            }

            async function runDeduplication(event) {
                event.preventDefault();
                const threshold = document.getElementById('similarityThreshold').value;

                // 진행 상황 모달 표시
                const steps = [
                    { title: '중복 제거 준비', description: '설정을 확인하는 중...' },
                    { title: '임베딩 생성', description: '텍스트 임베딩을 생성하는 중...' },
                    { title: '유사도 분석', description: '중복 뉴스를 분석하는 중...' },
                    { title: '완료', description: '중복 제거가 성공적으로 완료되었습니다.' }
                ];

                const stepIds = showProgressModal('🧠 중복 제거', steps);

                try {
                    // 1단계: 준비
                    updateProgressStep(stepIds[0], 'loading', '중복 제거 설정을 확인하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 500));

                    // 2단계: 임베딩 생성
                    updateProgressStep(stepIds[0], 'success', '설정 확인 완료');
                    updateProgressStep(stepIds[1], 'loading', '텍스트 임베딩을 생성하는 중...');

                    const response = await fetch('/api/embedding/deduplicate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            similarity_threshold: parseFloat(threshold)
                        })
                    });

                    // 3단계: 유사도 분석
                    updateProgressStep(stepIds[1], 'success', '임베딩 생성 완료');
                    updateProgressStep(stepIds[2], 'loading', '중복 뉴스를 분석하는 중...');

                    const result = await response.json();

                    if (result.success) {
                        updateProgressStep(stepIds[2], 'success', '중복 분석 완료');
                        updateProgressStep(stepIds[3], 'success', '중복 제거가 성공적으로 완료되었습니다.');

                        setTimeout(() => {
                            alert(`🎉 중복 제거 완료!\\n\\n유사도 임계값: ${threshold}\\n처리 결과: ${result.message || '성공'}`);
                            closeModal();
                        }, 1000);
                    } else {
                        updateProgressStep(stepIds[2], 'error', '분석 실패');
                        updateProgressStep(stepIds[3], 'error', result.message || '알 수 없는 오류');

                        setTimeout(() => {
                            alert('❌ 오류: ' + (result.message || '알 수 없는 오류'));
                        }, 1000);
                    }
                } catch (error) {
                    updateProgressStep(stepIds[1], 'error', '임베딩 생성 실패');
                    updateProgressStep(stepIds[2], 'error', '분석 중단');
                    updateProgressStep(stepIds[3], 'error', error.message);

                    setTimeout(() => {
                        alert('❌ 네트워크 오류: ' + error.message);
                    }, 1000);
                }
            }

            async function extractRelations(event) {
                event.preventDefault();
                const batchSize = document.getElementById('batchSize').value;

                // 진행 상황 모달 표시
                const steps = [
                    { title: '관계 추출 준비', description: '설정을 확인하는 중...' },
                    { title: 'Gemini 모델 연결', description: 'AI 모델에 연결하는 중...' },
                    { title: '관계 분석', description: '뉴스에서 관계를 추출하는 중...' },
                    { title: '완료', description: '관계 추출이 성공적으로 완료되었습니다.' }
                ];

                const stepIds = showProgressModal('🤖 관계 추출', steps);

                try {
                    // 1단계: 준비
                    updateProgressStep(stepIds[0], 'loading', '관계 추출 설정을 확인하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 500));

                    // 2단계: 모델 연결
                    updateProgressStep(stepIds[0], 'success', '설정 확인 완료');
                    updateProgressStep(stepIds[1], 'loading', 'Gemini AI 모델에 연결하는 중...');

                    const response = await fetch('/api/extractor/extract', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            batch_size: parseInt(batchSize)
                        })
                    });

                    // 3단계: 관계 분석
                    updateProgressStep(stepIds[1], 'success', 'AI 모델 연결 완료');
                    updateProgressStep(stepIds[2], 'loading', '뉴스에서 관계를 추출하는 중...');

                    const result = await response.json();

                    if (result.success) {
                        updateProgressStep(stepIds[2], 'success', '관계 분석 완료');
                        updateProgressStep(stepIds[3], 'success', '관계 추출이 성공적으로 완료되었습니다.');

                        setTimeout(() => {
                            alert(`🎉 관계 추출 완료!\\n\\n배치 크기: ${batchSize}\\n처리 결과: ${result.message || '성공'}`);
                            closeModal();
                        }, 1000);
                    } else {
                        updateProgressStep(stepIds[2], 'error', '분석 실패');
                        updateProgressStep(stepIds[3], 'error', result.message || '알 수 없는 오류');

                        setTimeout(() => {
                            alert('❌ 오류: ' + (result.message || '알 수 없는 오류'));
                        }, 1000);
                    }
                } catch (error) {
                    updateProgressStep(stepIds[1], 'error', '모델 연결 실패');
                    updateProgressStep(stepIds[2], 'error', '분석 중단');
                    updateProgressStep(stepIds[3], 'error', error.message);

                    setTimeout(() => {
                        alert('❌ 네트워크 오류: ' + error.message);
                    }, 1000);
                }
            }

            function openReviewPage() {
                window.open('/api/review/relations', '_blank');
                closeModal();
            }

            function viewPendingRounds() {
                window.open('/api/rounds/pending', '_blank');
                closeModal();
            }

            async function generateNetwork(event) {
                event.preventDefault();
                const company = document.getElementById('networkCompany').value;
                const maxDepth = document.getElementById('maxDepth').value;

                const url = company ?
                    `/api/visualization/network?target_company=${encodeURIComponent(company)}&max_depth=${maxDepth}` :
                    `/api/visualization/network?max_depth=${maxDepth}`;

                window.open(url, '_blank');
                closeModal();
            }

            async function scheduleJob(event) {
                event.preventDefault();
                const company = document.getElementById('schedCompany').value;
                const cronExpression = document.getElementById('cronExpression').value;

                try {
                    const response = await fetch('/api/scheduler/investigation', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `company_name=${encodeURIComponent(company)}&cron_expression=${encodeURIComponent(cronExpression)}`
                    });

                    const result = await response.json();
                    if (result.success) {
                        alert(`스케줄러 설정 완료!\n작업 ID: ${result.data.job_id}`);
                        closeModal();
                    } else {
                        alert('오류: ' + result.message);
                    }
                } catch (error) {
                    alert('네트워크 오류: ' + error.message);
                }
            }

            // 모달 외부 클릭 시 닫기
            window.onclick = function(event) {
                const modal = document.getElementById('workflowModal');
                if (event.target == modal) {
                    modal.style.display = 'none';
                }
            }

            // ESC 키로 모달 닫기
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    closeModal();
                }
            });

            // 진행 상황 데모 함수
            async function demoProgress() {
                const steps = [
                    { title: '데모 준비', description: '데모 환경을 설정하는 중...' },
                    { title: '데이터 처리', description: '샘플 데이터를 처리하는 중...' },
                    { title: '분석 실행', description: 'AI 분석을 실행하는 중...' },
                    { title: '완료', description: '데모가 성공적으로 완료되었습니다!' }
                ];

                const stepIds = showProgressModal('🎬 진행 상황 데모', steps);

                try {
                    // 1단계: 준비
                    updateProgressStep(stepIds[0], 'loading', '데모 환경을 설정하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 1500));

                    // 2단계: 데이터 처리
                    updateProgressStep(stepIds[0], 'success', '환경 설정 완료');
                    updateProgressStep(stepIds[1], 'loading', '샘플 데이터를 처리하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 2000));

                    // 3단계: 분석 실행
                    updateProgressStep(stepIds[1], 'success', '데이터 처리 완료');
                    updateProgressStep(stepIds[2], 'loading', 'AI 분석을 실행하는 중...');
                    await new Promise(resolve => setTimeout(resolve, 2500));

                    // 4단계: 완료
                    updateProgressStep(stepIds[2], 'success', '분석 완료');
                    updateProgressStep(stepIds[3], 'success', '데모가 성공적으로 완료되었습니다!');

                    setTimeout(() => {
                        alert('🎉 진행 상황 데모 완료!\\n\\n이것은 실제 워크플로우의 진행 상황 표시 예시입니다.\\n실제 작업을 수행하려면 각 단계의 버튼을 클릭하세요.');
                        closeModal();
                    }, 1500);

                } catch (error) {
                    // 데모에서는 에러가 발생하지 않도록 설계
                    console.log('데모 중 예기치 않은 오류:', error);
                }
            }

            // 페이지 로드 시 API 연결 상태 확인
            window.addEventListener('load', function() {
                checkAPIStatus();
            });

            // API 상태 확인 함수
            async function checkAPIStatus() {
                const connectionStatus = document.getElementById('connection-status');
                const apiStatus = document.getElementById('api-status');
                const configStatus = document.getElementById('config-status');

                try {
                    // 기본 연결 테스트
                    connectionStatus.textContent = '🔄 연결 테스트 중...';
                    connectionStatus.style.color = '#ffa500';

                    const healthResponse = await fetch('/health');
                    if (healthResponse.ok) {
                        connectionStatus.textContent = '🟢 서버 연결됨';
                        connectionStatus.style.color = '#28a745';
                    } else {
                        throw new Error('서버 응답 오류');
                    }

                    // API 상태 테스트
                    apiStatus.textContent = '🔄 API 테스트 중...';
                    apiStatus.style.color = '#ffa500';

                    const testResponse = await fetch('/test');
                    const testData = await testResponse.json();

                    if (testData.success) {
                        apiStatus.textContent = '🟢 API 정상 작동';
                        apiStatus.style.color = '#28a745';
                    } else {
                        throw new Error('API 응답 오류');
                    }

                    // 설정 상태 확인
                    await checkConfigStatus();

                } catch (error) {
                    console.error('API 상태 확인 실패:', error);
                    connectionStatus.textContent = '🔴 서버 연결 실패';
                    connectionStatus.style.color = '#dc3545';
                    apiStatus.textContent = '🔴 API 오류';
                    apiStatus.style.color = '#dc3545';
                    configStatus.textContent = '🔴 설정 확인 실패';
                    configStatus.style.color = '#dc3545';
                }
            }

            // 설정 상태 확인 함수
            async function checkConfigStatus() {
                const configStatus = document.getElementById('config-status');

                try {
                    configStatus.textContent = '🔄 설정 확인 중...';
                    configStatus.style.color = '#ffa500';

                    // SystemConfig에서 설정 값들 확인
                    const configResponse = await fetch('/api/config/status');
                    if (configResponse.ok) {
                        const configData = await configResponse.json();

                        if (configData.success && configData.data) {
                            const configs = configData.data;
                            const geminiKey = configs.gemini_api_key;
                            const naverId = configs.naver_api_client_id;
                            const naverSecret = configs.naver_api_client_secret;

                            if (geminiKey && naverId && naverSecret) {
                                configStatus.textContent = '🟢 모든 API 키 설정됨';
                                configStatus.style.color = '#28a745';
                            } else {
                                const missing = [];
                                if (!geminiKey) missing.push('Gemini');
                                if (!naverId) missing.push('네이버 ID');
                                if (!naverSecret) missing.push('네이버 Secret');

                                configStatus.textContent = `🟡 누락: ${missing.join(', ')}`;
                                configStatus.style.color = '#ffc107';
                            }
                        } else {
                            configStatus.textContent = '🔴 설정 조회 실패';
                            configStatus.style.color = '#dc3545';
                        }
                    } else {
                        configStatus.textContent = '🔴 설정 API 오류';
                        configStatus.style.color = '#dc3545';
                    }

                } catch (error) {
                    console.error('설정 상태 확인 실패:', error);
                    configStatus.textContent = '🔴 설정 확인 실패';
                    configStatus.style.color = '#dc3545';
                }
            }
        </script>

        <style>
            /* 모달 스타일 */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                backdrop-filter: blur(5px);
            }

            .modal-content {
                background-color: white;
                margin: 10% auto;
                padding: 30px;
                border-radius: 15px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: modalSlideIn 0.3s ease-out;
                max-height: 80vh;
                overflow-y: auto;
            }

            @keyframes modalSlideIn {
                from {
                    transform: translateY(-50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                margin-top: -10px;
            }

            .close:hover {
                color: #667eea;
            }

            .form-group {
                margin-bottom: 20px;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #333;
            }

            .form-group input, .form-group select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s ease;
            }

            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
            }

            .review-actions {
                display: flex;
                gap: 10px;
                justify-content: center;
            }

            /* 진행 상황 스타일 */
            .progress-container {
                margin: 20px 0;
            }

            .progress-step {
                display: flex;
                align-items: center;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 10px;
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
            }

            .progress-step.loading {
                border-color: #ffc107;
                background: linear-gradient(90deg, #fff3cd 0%, #f8f9fa 100%);
            }

            .progress-step.completed {
                border-color: #28a745;
                background: linear-gradient(90deg, #d4edda 0%, #f8f9fa 100%);
            }

            .progress-step.error {
                border-color: #dc3545;
                background: linear-gradient(90deg, #f8d7da 0%, #f8f9fa 100%);
            }

            .step-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                margin-right: 15px;
                border-radius: 50%;
                transition: all 0.3s ease;
            }

            .progress-step.loading .step-icon {
                background: #ffc107;
                color: white;
                animation: spin 1s linear infinite;
            }

            .progress-step.completed .step-icon {
                background: #28a745;
                color: white;
            }

            .progress-step.error .step-icon {
                background: #dc3545;
                color: white;
            }

            .step-content {
                flex: 1;
            }

            .step-title {
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }

            .step-description {
                color: #666;
                font-size: 14px;
                transition: color 0.3s ease;
            }

            .progress-step.completed .step-description {
                color: #155724;
            }

            .progress-step.error .step-description {
                color: #721c24;
            }

            .progress-actions {
                margin-top: 20px;
                text-align: center;
            }

            /* 로딩 애니메이션 */
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "DJS API", "version": "1.0.0"}


@app.get("/test")
async def test_endpoint():
    """테스트용 간단한 엔드포인트"""
    return {
        "success": True,
        "message": "Test endpoint works!",
        "timestamp": "2024-01-01",
    }


@app.get("/favicon.ico")
async def favicon():
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='12' fill='#667eea'/>"
        "<text x='32' y='40' font-size='28' text-anchor='middle' fill='white' font-family='Arial'>D</text>"
        "</svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


# 인증 미들웨어: 로그인 필요 경로 보호
@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path
    # 허용 경로 (비보호)
    allow_prefixes = (
        "/api/auth",
        "/login",
        "/favicon.ico",
        "/health",
        "/openapi.json",
    )
    if (
        path == "/"
        or path.startswith("/api/")
        or path.startswith("/docs")
        or path.startswith("/redoc")
    ):
        # 대부분 보호, 단 인증/헬스만 예외
        if (
            path.startswith(allow_prefixes)
            or path in ("/health", "/openapi.json")
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return await call_next(request)

        # 토큰 확인 (Authorization 헤더 또는 쿠키)
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        if not token:
            token = request.cookies.get("djs_token")

        if token:
            # 토큰 검증
            db = SessionLocal()
            try:
                secret, algorithm, _ = get_jwt_settings(db)
            except Exception:
                secret, algorithm = DEFAULT_JWT_SECRET, DEFAULT_JWT_ALGORITHM
            finally:
                db.close()

            payload = decode_token(token, secret_key=secret, algorithms=[algorithm])
            if payload:
                return await call_next(request)

        # 인증 실패 처리: GET은 /login 리다이렉트, 그 외 401
        if request.method.upper() == "GET":
            return RedirectResponse(url="/login", status_code=302)
        return JSONResponse(
            status_code=401, content={"success": False, "message": "인증이 필요합니다."}
        )

    # 기타 경로는 그대로 진행
    return await call_next(request)


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset=\"utf-8\"/>
      <title>로그인 - DJS</title>
      <style>
        body { font-family: Arial, sans-serif; background:#f5f5f5; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
        .card { background:#fff; padding:28px; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.08); width:100%; max-width:380px; }
        h1 { margin:0 0 8px 0; font-size:22px; color:#333; }
        p { margin:0 0 16px 0; color:#666; }
        .form-group { margin-bottom:12px; }
        label { display:block; font-weight:bold; margin-bottom:6px; color:#333; }
        input { width:100%; padding:10px 12px; border:1px solid #ddd; border-radius:8px; }
        .actions { display:flex; gap:8px; margin-top:14px; }
        .btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color:#fff; padding:10px 12px; border:none; border-radius:8px; cursor:pointer; flex:1; }
        .btn-secondary { background:#f8f9fa; color:#495057; border:1px solid #dee2e6; padding:10px 12px; border-radius:8px; cursor:pointer; flex:1; }
        .hint { margin-top:10px; font-size:12px; color:#888; text-align:center; }
      </style>
    </head>
    <body>
      <div class=\"card\">
        <h1>🔐 로그인</h1>
        <p>로그인 후 시스템에 접근할 수 있습니다.</p>
        <div class=\"form-group\">
          <label for=\"email\">이메일</label>
          <input id=\"email\" type=\"email\" placeholder=\"you@example.com\" />
        </div>
        <div class=\"form-group\">
          <label for=\"password\">비밀번호</label>
          <input id=\"password\" type=\"password\" placeholder=\"********\" />
        </div>
        <div class=\"actions\">
          <button class=\"btn-primary\" onclick=\"login()\">로그인</button>
          <button class=\"btn-secondary\" onclick=\"alert('회원가입이 비활성화되었습니다.')\">회원가입</button>
        </div>
        <div class=\"hint\">계정이 없으면 회원가입으로 생성하세요.</div>
      </div>
      <script>
        async function login(){
          const email=document.getElementById('email').value; const password=document.getElementById('password').value;
          const body=new URLSearchParams(); body.set('username', email); body.set('password', password);
          const res=await fetch('/api/auth/token',{method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body});
          const data=await res.json();
          if(data.access_token){
            localStorage.setItem('djs_token', data.access_token);
            localStorage.setItem('djs_email', email);
            document.cookie = 'djs_token='+data.access_token+'; Path=/; SameSite=Lax';
            window.location.href='/';
          } else { alert('로그인 실패'); }
        }
      </script>
    </body>
    </html>
    """


@app.post("/test-investigation")
async def test_investigation(company_name: str = "테스트기업"):
    """테스트용 조사 엔드포인트"""
    return {
        "success": True,
        "message": f"'{company_name}' 기업 조사 테스트 성공",
        "data": {
            "company_name": company_name,
            "status": "test_completed",
            "timestamp": "2024-01-01",
        },
    }


@app.get("/visualize", response_class=HTMLResponse)
async def visualize_page(target_company: str | None = None, max_depth: int = 3):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset=\"utf-8\"/>
      <title>DJS Network</title>
      <script src=\"https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js\"></script>
      <link rel=\"stylesheet\" href=\"https://unpkg.com/vis-network@9.1.6/styles/vis-network.min.css\"/>
      <style>
        html, body {{ height: 100%; margin: 0; }}
        #app {{ height: 100vh; }}
      </style>
    </head>
    <body>
      <div id=\"app\"></div>
      <script>
        (async function() {{
          const company = {json.dumps(target_company)};
          const depth = {max_depth};
          const url = company ? `/api/visualization/network?target_company=${{encodeURIComponent(company)}}&max_depth=${{depth}}` : `/api/visualization/network?max_depth=${{depth}}`;
          const res = await fetch(url);
          const data = await res.json();
          const nodes = new vis.DataSet((data.nodes||[]).map(n => ({{ id: n.id, label: n.name || n.id, group: n.group||n.type }})));
          const edges = new vis.DataSet((data.edges||[]).map(e => ({{ from: e.source, to: e.target }})));
          const container = document.getElementById('app');
          const options = {{
            interaction: {{ hover: true }},
            physics: {{ stabilization: true }},
            groups: {{ company: {{ color: '#4CAF50' }}, university: {{ color: '#2196F3' }}, professor: {{ color: '#FF9800' }} }}
          }};
          new vis.Network(container, {{ nodes, edges }}, options);
        }})();
      </script>
    </body>
    </html>
    """


@app.get("/api/config/status")
async def get_config_status(db: Session = Depends(get_db)):
    """설정 상태 조회 엔드포인트"""
    try:
        from backend.models.models import SystemConfig

        # 주요 설정 값들 조회
        configs = {}
        config_keys = [
            "gemini_api_key",
            "llm_model",
            "naver_api_client_id",
            "naver_api_client_secret",
            "embedding_model",
            "similarity_threshold",
            "max_news_per_search",
        ]

        for key in config_keys:
            config_record = (
                db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            )

            if config_record:
                # API 키는 마스킹해서 표시
                if "api_key" in key or "secret" in key:
                    value = config_record.config_value
                    if value and len(value) > 10:
                        configs[key] = (
                            value[:6] + "..." + value[-4:]
                        )  # 앞 6자 + ... + 뒤 4자
                    else:
                        configs[key] = "설정됨" if value else None
                else:
                    configs[key] = config_record.config_value
            else:
                configs[key] = None

        return {"success": True, "message": "설정 상태 조회 완료", "data": configs}

    except Exception as e:
        return {
            "success": False,
            "message": f"설정 상태 조회 실패: {str(e)}",
            "data": None,
        }


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    try:
        # 데이터베이스 초기화
        from backend.core.init_db import initialize_database

        initialize_database()

        # 필요한 디렉토리 생성
        data_dirs = [
            Path(__file__).parent.parent / "data" / "embeddings",
            Path(__file__).parent.parent / "data" / "raw_news",
            Path(__file__).parent.parent / "data" / "processed_relations",
            Path(__file__).parent.parent / "logs",
        ]

        for dir_path in data_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("필요 디렉토리 생성 완료")
        logger.info("DJS 시스템 시작 완료")

    except Exception as e:
        logger.error(f"시스템 시작 실패: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("DJS 시스템 종료")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅 미들웨어"""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
