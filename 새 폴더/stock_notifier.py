import requests
import json
import smtplib
import time
from email.mime.text import MIMEText

# --- 설정 (사용자 정보 입력) ---
SMTP_SERVER = "smtp.gmail.com"  # 사용 중인 이메일 서비스의 SMTP 서버 (Gmail 예시)
SMTP_PORT = 587  # TLS 포트
SENDER_EMAIL = "YOUR_GMAIL@gmail.com"  # 보내는 사람 이메일 주소
SENDER_PASSWORD = "YOUR_APP_PASSWORD"  # 보내는 사람 이메일 앱 비밀번호
RECEIVER_EMAIL = "RECEIVER_EMAIL@example.com"  # 받는 사람 이메일 주소
# ------------------------------------

JSON_URL = "https://shopdunssweden.se/products.json"
STATUS_FILE = "stock_status.json"


def get_current_stock():
    """웹사이트에서 현재 재고 상태를 가져옵니다."""
    try:
        response = requests.get(JSON_URL, timeout=15)
        response.raise_for_status()
        products = response.json().get("products", [])

        current_stock = {}
        for product in products:
            for variant in product["variants"]:
                variant_id = variant["id"]
                product_title = product["title"]
                variant_title = variant["title"]
                product_url = f"https://shopdunssweden.se/products/{product['handle']}"

                current_stock[variant_id] = {
                    "name": f"{product_title} - {variant_title}",
                    "available": variant["available"],
                    "url": product_url,
                }
        return current_stock
    except Exception as e:
        print(f"재고 정보를 가져오는 중 오류 발생: {e}")
        return None


def load_previous_stock():
    """파일에 저장된 이전 재고 상태를 불러옵니다."""
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # 파일이 없으면 빈 딕셔너리 반환


def save_current_stock(stock_data):
    """현재 재고 상태를 파일에 저장합니다."""
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, indent=4, ensure_ascii=False)


def send_notification_email(restocked_items):
    """재입고된 상품 정보를 이메일로 보냅니다."""
    if not restocked_items:
        return

    # 이메일 내용 구성
    subject = "[재고 알림] DUNS Sweden 상품이 재입고되었습니다!"
    body = "안녕하세요,\n\n요청하신 상품이 재입고되어 알려드립니다.\n\n"
    for item in restocked_items:
        body += f"- 상품명: {item['name']}\n"
        body += f"  URL: {item['url']}\n\n"
    body += "감사합니다."

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        print("이메일 서버에 연결 중...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("이메일 발송 중...")
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("이메일이 성공적으로 발송되었습니다.")
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {e}")
    finally:
        if "server" in locals() and server:
            server.quit()


def main():
    print("재고 확인을 시작합니다...")
    current_stock = get_current_stock()
    if not current_stock:
        print("현재 재고 정보를 가져올 수 없어 프로그램을 종료합니다.")
        return

    previous_stock = load_previous_stock()
    restocked_items = []

    if not previous_stock:
        print("이전 재고 데이터가 없습니다. 현재 상태를 기준으로 초기화합니다.")
    else:
        for variant_id, new_status in current_stock.items():
            old_status = previous_stock.get(
                str(variant_id)
            )  # JSON 키는 문자열일 수 있음

            # 이전에는 품절(False)이었는데, 지금은 재고 있음(True)인 경우
            if old_status and not old_status["available"] and new_status["available"]:
                print(f"재입고 발견! -> {new_status['name']}")
                restocked_items.append(new_status)

    if restocked_items:
        send_notification_email(restocked_items)
    else:
        print("새로 재입고된 상품이 없습니다.")

    save_current_stock(current_stock)
    print(f"현재 재고 상태를 '{STATUS_FILE}'에 저장했습니다.")
    print("재고 확인 완료.")


if __name__ == "__main__":
    main()
