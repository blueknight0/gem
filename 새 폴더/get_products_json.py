import requests
import json

# Shopify 스토어의 products.json URL
JSON_URL = "https://shopdunssweden.se/products.json"

print(f"'{JSON_URL}'에서 제품 정보를 가져옵니다...")

try:
    # requests를 사용하여 JSON 데이터 요청
    response = requests.get(JSON_URL, timeout=15)
    response.raise_for_status()  # 요청 실패 시 예외 발생

    # JSON 응답을 파싱
    data = response.json()

    # 'products' 키가 있는지 확인
    if "products" in data and data["products"]:
        products = data["products"]
        print(f"총 {len(products)}개의 제품 데이터를 성공적으로 가져왔습니다.\n")
        print("---------- 제품 재고 분석 ----------")

        # 각 제품 정보 순회
        for product in products:
            product_title = product["title"]
            product_handle = product["handle"]  # 제품 페이지로 가는 URL 일부
            product_url = f"https://shopdunssweden.se/products/{product_handle}"

            print(f"\n--- 제품명: {product_title} ---")
            print(f"URL: {product_url}")

            # 제품의 각 옵션(variant)별로 재고 확인
            for variant in product["variants"]:
                variant_title = variant["title"]

                # 가격 정보 추출 (오류 처리 추가)
                try:
                    price = f"{variant['price']} {variant['presentment_prices'][0]['price']['currency_code']}"
                except (KeyError, IndexError):
                    price = "가격 정보 없음"

                # 재고가 있는지 여부 (가장 중요한 정보)
                is_available = variant["available"]

                stock_status = "재고 있음" if is_available else "품절"

                print(f"  - 옵션: {variant_title}")
                print(f"    가격: {price}")
                print(f"    재고 상태: {stock_status}")

    else:
        print("JSON 데이터에서 'products' 목록을 찾을 수 없거나 비어있습니다.")

except requests.exceptions.RequestException as e:
    print(f"데이터를 가져오는 중 오류 발생: {e}")
except json.JSONDecodeError:
    print("가져온 데이터를 JSON으로 파싱할 수 없습니다. 응답 내용을 확인하세요.")
except Exception as e:
    print(f"알 수 없는 오류 발생: {e}")
