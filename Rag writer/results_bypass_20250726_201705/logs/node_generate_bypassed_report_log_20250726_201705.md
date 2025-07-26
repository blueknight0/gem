# Log for node: generate_bypassed_report

{'timestamp': '20:17:19', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': ">>> 노드 'generate_bypassed_report' 시작"}
{'timestamp': '20:17:19', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '[1/2] 바이패스 모드로 전체 보고서 생성 시작'}
{'timestamp': '20:17:19', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB에서 주제 관련 문서 수집 시작...'}
{'timestamp': '20:17:20', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '총 58개의 관련 문서를 수집했습니다.'}
{'timestamp': '20:17:20', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '프롬프트 길이: 32,181자 (약 8,045 토큰)'}
{'timestamp': '20:17:20', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB 문서 58개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작'}
{'timestamp': '20:22:00', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'Grounding 검색어 수: 10'}
{'timestamp': '20:22:00', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': "검색어 목록: ['벨기에 변호사-의뢰인 비밀유지특권 2022년 법률', 'Loi belge du 31 juillet 2022 secret professionnel avocat', '벨기에 형법 제458조 변호사 비밀유지', '벨기에 안티고네 테스트(Antigone test) 판례', '사내변호사 비밀유지특권 프랑스 독일 영국 비교', '유럽인권재판소 변호사 비밀유지특권 판례', '벨기에 국제 중재 허브 경쟁력', 'OVB OBFG 윤리강령 비밀유지 조항', '벨기에 변호사 사무실 디지털 증거 압수수색 절차', 'Belgian law on the protection of the confidentiality of lawyer-client communications 2022']"}
{'timestamp': '20:22:00', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '총 31개 참고문헌 추가 (DB: 17개, 웹: 14개)'}
{'timestamp': '20:22:00', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '🎉 DB 완전 활용 바이패스 모드 보고서 생성 완료!\n   📊 통계: 45,360자 (8,016단어)\n   🎯 목표 달성률: 151.2% (목표: 30,000자)\n   💾 DB 활용률: 7.5% (58/773개 문서)'}
{'timestamp': '20:22:00', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - final_report_with_refs: (내용이 길어 생략됨)'}
{'timestamp': '20:22:00', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - progress_message: 1/2: DB 완전 활용 바이패스 보고서 생성 완료. 파일 저장 시작...'}
{'timestamp': '20:22:00', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': "노드 'generate_bypassed_report' 완료 (소요시간: 280.97초)"}