import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

URL = "https://shopdunssweden.se/"
FILE_NAME = "shopdunssweden_selenium.html"

print("Selenium으로 브라우저를 실행합니다...")

# 브라우저가 자동으로 닫히지 않게 하고, 백그라운드에서 실행하는 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # GUI 없이 실행
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)


# 웹 드라이버 설정 및 실행
try:
    with webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_options
    ) as driver:
        print(f"'{URL}'로 이동합니다...")
        driver.get(URL)

        # 페이지가 완전히 로드되기를 기다림 (필요에 따라 시간 조절)
        print("페이지 로딩을 5초간 기다립니다...")
        time.sleep(5)

        print("페이지의 HTML 소스를 가져옵니다.")
        html_content = driver.page_source

        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML 콘텐츠를 '{FILE_NAME}' 파일로 성공적으로 저장했습니다.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")

finally:
    print("스크립트 실행을 종료합니다.")
