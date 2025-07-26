# Log for node: generate_bypassed_report

{'timestamp': '22:13:46', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': ">>> 노드 'generate_bypassed_report' 시작"}
{'timestamp': '22:13:46', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '[1/2] 바이패스 모드로 전체 보고서 생성 시작'}
{'timestamp': '22:13:46', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB에서 주제 관련 문서 수집 시작...'}
{'timestamp': '22:13:47', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '총 58개의 관련 문서를 수집했습니다.'}
{'timestamp': '22:13:47', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '프롬프트 길이: 32,111자 (약 8,027 토큰)'}
{'timestamp': '22:13:47', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '참고문서 58개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작'}
{'timestamp': '22:18:47', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'Grounding 검색어 수: 16'}
{'timestamp': '22:18:47', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '검색어 목록: [\'벨기에 변호사 비밀유지특권 2022년 7월 20일 법률 전문\', \'Belgian law of 20 July 2022 professional secrecy lawyer text\', \'벨기에 형법 제458조 변호사 비밀유지 의무 처벌\', \'Belgian Penal Code Article 458 penalties professional secrecy\', \'벨기에 변호사 사무실 압수수색 변호사회장 역할 절차\', "Procedure for search of a lawyer\'s office in Belgium role of the President of the Bar", \'벨기에 사내 변호사 비밀유지특권 EU 경쟁법 비교\', \'Comparison of in-house counsel privilege Belgium domestic law vs EU competition law\', \'벨기에 OVB AVOCATS.BE 윤리강령 비교 비밀유지\', \'Comparison of OVB and AVOCATS.BE codes of ethics on professional secrecy\', \'벨기에 헌법재판소 형사소송법 제39조의2 위헌 결정\', \'Belgian Constitutional Court annulment Article 39bis Code of Criminal Procedure digital evidence\', \'벨기에 ACP 제도 경제적 효과 외국인 직접 투자\', \'Economic impact of Attorney-Client Privilege in Belgium FDI\', \'프랑스 독일 변호사-의뢰인 비밀유지특권 사내변호사\', \'Attorney-client privilege for in-house counsel in France and Germany\']'}
{'timestamp': '22:18:47', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '총 44개 참고문헌 추가 (DB: 17개, 웹: 27개)'}
{'timestamp': '22:18:47', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '🎉 자료 완전 활용 바이패스 모드 보고서 생성 완료!\n   📊 통계: 37,508자 (7,163단어)\n   🎯 목표 달성률: 125.0% (목표: 30,000자)\n   💾 자료 활용률: 7.5% (58/773개 문서)'}
{'timestamp': '22:18:47', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - final_report_with_refs: (내용이 길어 생략됨)'}
{'timestamp': '22:18:47', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - progress_message: 1/2: DB 완전 활용 바이패스 보고서 생성 완료. 파일 저장 시작...'}
{'timestamp': '22:18:47', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': "노드 'generate_bypassed_report' 완료 (소요시간: 301.52초)"}