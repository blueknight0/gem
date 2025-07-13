import requests

URL = "https://shopdunssweden.se/"
FILE_NAME = "shopdunssweden.html"

try:
    print(f"'{URL}'에서 HTML을 가져오는 중...")
    response = requests.get(URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    with open(FILE_NAME, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"HTML 콘텐츠를 '{FILE_NAME}' 파일로 성공적으로 저장했습니다.")

except requests.exceptions.RequestException as e:
    print(f"오류 발생: {e}")
