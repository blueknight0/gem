import requests
from bs4 import BeautifulSoup

# 로컬 HTML 파일 경로 (수정)
HTML_FILE = "shopdunssweden_selenium.html"

print("스크립트 실행 시작")

try:
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    print(f"'{HTML_FILE}' 파일 읽기 성공")

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, "html.parser")
    print("BeautifulSoup 객체 생성 완료")

    # 제품 목록을 담고 있는 컨테이너 찾기 (최종 수정)
    product_grid = soup.find("div", id="main-collection-product-grid")

    if product_grid:
        print("제품 그리드('main-collection-product-grid')를 찾았습니다.")
        # 각 제품 아이템을 찾기
        products = product_grid.find_all("div", class_="grid__item")
        print(f"총 {len(products)}개의 상품(grid__item)을 찾았습니다.\n")

        if not products:
            print(
                "'grid__item' 클래스를 가진 제품을 찾지 못했습니다. HTML 구조를 다시 확인해야 합니다."
            )
        else:
            print("---------- 제품 목록 ----------")

        for product in products:
            # 제품명
            name_tag = product.find("a", class_="full-unstyled-link")
            name = name_tag.text.strip() if name_tag else "이름 없음"

            # 가격
            price_tag = product.find("span", class_="price-item")
            price = (
                price_tag.text.strip().replace("From", "").strip()
                if price_tag
                else "가격 정보 없음"
            )

            # 품절 여부
            badge = product.find("div", class_="card__badge")
            is_sold_out = "품절" if badge and "Sold Out" in badge.text else "재고 있음"

            if "Sold Out" in name:
                is_sold_out = "품절"
                name = name.replace("— Sold Out", "").strip()

            if "가격 정보 없음" in price:
                continue

            print(f"제품명: {name}")
            print(f"가격: {price}")
            print(f"재고 상태: {is_sold_out}")
            print("-" * 20)

    else:
        print("제품 그리드('main-collection-product-grid')를 찾을 수 없습니다.")

except FileNotFoundError:
    print(
        f"오류: '{HTML_FILE}' 파일을 찾을 수 없습니다. 먼저 save_html.py를 실행하세요."
    )
except Exception as e:
    print(f"오류 발생: {e}")

print("스크립트 실행 종료")
