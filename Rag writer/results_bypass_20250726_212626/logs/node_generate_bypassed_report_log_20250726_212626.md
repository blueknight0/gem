# Log for node: generate_bypassed_report

{'timestamp': '21:26:39', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': ">>> 노드 'generate_bypassed_report' 시작"}
{'timestamp': '21:26:39', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '[1/2] 바이패스 모드로 전체 보고서 생성 시작'}
{'timestamp': '21:26:39', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB에서 주제 관련 문서 수집 시작...'}
{'timestamp': '21:26:40', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '총 57개의 관련 문서를 수집했습니다.'}
{'timestamp': '21:26:40', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '프롬프트 길이: 38,438자 (약 9,609 토큰)'}
{'timestamp': '21:26:40', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB 문서 57개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작'}
{'timestamp': '21:31:10', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'Grounding 검색어 수: 11'}
{'timestamp': '21:31:10', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '검색어 목록: [\'프랑스 사내변호사 법률자문 비밀보호권 2024년 법안 최종 내용\', \'Loi n° 2024-364 du 22 avril 2024 visant à adapter le droit de la responsabilité civile aux enjeux actuels\', \'France in-house counsel legal privilege law 2024 full text\', "Rapport Darrois 2009 l\'avocat en entreprise", \'CJEU Akzo Nobel C-550/07 P ruling details\', \'German Syndikusrechtsanwalt requirements\', \'French legal professional privilege sanctions for breach in-house counsel\', \'프랑스 경쟁당국 조사 사내변호사 자문 압수\', \'프랑스 변호사법 1971년 법률 제71-1130호 원문\', \'프랑스 국가변호사위원회(CNB) 사내변호사 ACP 반대 이유\', \'프랑스 사내변호사협회(AFJE) ACP 찬성 논거\']'}
{'timestamp': '21:31:10', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '총 48개 참고문헌 추가 (DB: 26개, 웹: 22개)'}
{'timestamp': '21:31:10', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '🎉 DB 완전 활용 바이패스 모드 보고서 생성 완료!\n   📊 통계: 52,580자 (8,349단어)\n   🎯 목표 달성률: 175.3% (목표: 30,000자)\n   💾 DB 활용률: 6.6% (57/859개 문서)'}
{'timestamp': '21:31:10', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - final_report_with_refs: (내용이 길어 생략됨)'}
{'timestamp': '21:31:10', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - progress_message: 1/2: DB 완전 활용 바이패스 보고서 생성 완료. 파일 저장 시작...'}
{'timestamp': '21:31:10', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': "노드 'generate_bypassed_report' 완료 (소요시간: 271.36초)"}