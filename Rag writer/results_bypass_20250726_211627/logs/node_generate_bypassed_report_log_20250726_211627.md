# Log for node: generate_bypassed_report

{'timestamp': '21:16:44', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': ">>> 노드 'generate_bypassed_report' 시작"}
{'timestamp': '21:16:44', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '[1/2] 바이패스 모드로 전체 보고서 생성 시작'}
{'timestamp': '21:16:44', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB에서 주제 관련 문서 수집 시작...'}
{'timestamp': '21:16:45', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '총 60개의 관련 문서를 수집했습니다.'}
{'timestamp': '21:16:45', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '프롬프트 길이: 33,046자 (약 8,261 토큰)'}
{'timestamp': '21:16:45', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB 문서 60개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작'}
{'timestamp': '21:22:02', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'Grounding 검색어 수: 10'}
{'timestamp': '21:22:02', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': "검색어 목록: ['네덜란드 변호사비닉특권 위반 효과', '네덜란드 변호사법 징계 절차', '네덜란드 변호사 비밀유지 의무 위반 처벌', 'Dutch Attorney-Client Privilege violation penalty', 'Netherlands Bar Association disciplinary procedure for breach of confidentiality', '네덜란드 자금세탁방지법 변호사 의무 최신 동향', '네덜란드 형사소송법 현대화 프로젝트 ACP 조항', 'Recent developments Dutch Criminal Procedure Code modernization legal privilege', 'Comparative analysis of attorney-client privilege Germany UK Netherlands', '네덜란드 ACP 제도와 영국 미국 독일 비교 분석']"}
{'timestamp': '21:22:02', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '총 39개 참고문헌 추가 (DB: 21개, 웹: 18개)'}
{'timestamp': '21:22:02', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '🎉 DB 완전 활용 바이패스 모드 보고서 생성 완료!\n   📊 통계: 47,359자 (8,061단어)\n   🎯 목표 달성률: 157.9% (목표: 30,000자)\n   💾 DB 활용률: 7.2% (60/839개 문서)'}
{'timestamp': '21:22:02', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - final_report_with_refs: (내용이 길어 생략됨)'}
{'timestamp': '21:22:02', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - progress_message: 1/2: DB 완전 활용 바이패스 보고서 생성 완료. 파일 저장 시작...'}
{'timestamp': '21:22:02', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': "노드 'generate_bypassed_report' 완료 (소요시간: 317.23초)"}