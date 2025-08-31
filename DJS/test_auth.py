import json
import time
import requests


BASE = "http://127.0.0.1:8000"


def main():
    email = "test@example.com"
    password = "testpassword123"

    # 1) 회원가입
    try:
        r = requests.post(
            f"{BASE}/api/auth/register",
            json={"email": email, "password": password},
            timeout=10,
        )
        try:
            print("register:", r.status_code, r.json())
        except Exception:
            print("register raw:", r.status_code, r.text)
    except Exception as e:
        print("register error:", e)

    # 2) 로그인 (OAuth2PasswordRequestForm: username, password)
    try:
        r = requests.post(
            f"{BASE}/api/auth/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        token = r.json().get("access_token")
        print("token:", r.status_code, "obtained" if token else r.text)
    except Exception as e:
        print("token error:", e)
        return

    if not token:
        print("no token; abort")
        return

    # 3) /me
    try:
        r = requests.get(
            f"{BASE}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        print("me:", r.status_code, r.json())
    except Exception as e:
        print("me error:", e)

    # 4) 보호된 예시
    try:
        r = requests.get(
            f"{BASE}/api/auth/protected",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        print("protected:", r.status_code, r.json())
    except Exception as e:
        print("protected error:", e)


if __name__ == "__main__":
    main()
