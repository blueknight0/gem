# Log for node: generate_bypassed_report

{'timestamp': '22:38:07', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': ">>> 노드 'generate_bypassed_report' 시작"}
{'timestamp': '22:38:07', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '[1/2] 바이패스 모드로 전체 보고서 생성 시작'}
{'timestamp': '22:38:07', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'DB에서 주제 관련 문서 수집 시작...'}
{'timestamp': '22:38:08', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '총 60개의 관련 문서를 수집했습니다.'}
{'timestamp': '22:38:08', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '프롬프트 길이: 32,080자 (약 8,020 토큰)'}
{'timestamp': '22:38:08', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': '참고문서 60개를 포함하여 Gemini 2.5 Pro 극한 설정으로 보고서 생성 시작'}
{'timestamp': '22:43:32', 'level': 'INFO', 'node': 'generate_bypassed_report', 'message': 'Grounding 검색어 수: 17'}
{'timestamp': '22:43:32', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '검색어 목록: [\'네덜란드 ACP 제도 역사\', \'Roman-Dutch law professional secrecy\', \'네덜란드 법에 대한 나폴레옹 법전의 영향\', \'네덜란드 변호사-의뢰인 비밀유지 특권(ACP) 제도 연혁\', \'네덜란드 변호사법(Advocatenwet) 제11a조 입법 취지\', \'네덜란드 형사소송법(Wetboek van Strafvordering) 제218조 내용\', \'네덜란드 민사소송법(Wetboek van Burgerlijke Rechtsvordering) 제165조 내용\', \'네덜란드 사내변호사 ACP 인정 요건\', \'Akzo Nobel 판결 네덜란드 법에 미친 영향\', \'네덜란드 대법원 2024년 3월 1일 판결 ECLI:NL:HR:2024:375 디지털 증거 ACP\', \'네덜란드 자금세탁방지법(Wwft) 변호사 비밀유지 의무 충돌\', \'네덜란드 ACP 위반 시 민사, 형사, 징계 책임\', \'네덜란드 ACP 제도 효용성 분석\', \'유럽연합(EU)의 변호사-의뢰인 비밀유지 특권(ACP) 규정\', \'영국 변호사-의뢰인 비밀유지 특권(Legal Professional Privilege)\', \'독일 변호사 비밀유지 특권(Anwaltsgeheimnis)\', "프랑스 변호사 비밀유지 특권(Secret professionnel de l\'avocat)"]'}
{'timestamp': '22:43:32', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '총 42개 참고문헌 추가 (DB: 21개, 웹: 21개)'}
{'timestamp': '22:43:32', 'level': 'SUCCESS', 'node': 'generate_bypassed_report', 'message': '🎉 자료 완전 활용 바이패스 모드 보고서 생성 완료!\n   📊 통계: 48,726자 (7,998단어)\n   🎯 목표 달성률: 162.4% (목표: 30,000자)\n   💾 자료 활용률: 7.2% (60/839개 문서)'}
{'timestamp': '22:43:32', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - final_report_with_refs: (내용이 길어 생략됨)'}
{'timestamp': '22:43:32', 'level': 'DEBUG', 'node': 'generate_bypassed_report', 'message': '  - progress_message: 1/2: DB 완전 활용 바이패스 보고서 생성 완료. 파일 저장 시작...'}
{'timestamp': '22:43:32', 'level': 'SYSTEM', 'node': 'generate_bypassed_report', 'message': "노드 'generate_bypassed_report' 완료 (소요시간: 324.33초)"}