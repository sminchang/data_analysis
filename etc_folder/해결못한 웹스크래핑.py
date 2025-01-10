import requests
import pandas as pd #pip install pandas, pip install openpyxl

# 개발자 도구 켜고 들어오는 HTTP message 확인하면 JSON 응답 잘 들어오는데
# 내가 headers, payload(request body), session 받아서 똑같이 요청 보내면 에러 페이지를 응답한다.

data = []

# 요청 URL
API_url = "https://les.klef.go.kr/qaa/bbmn/wdmn/selectWordDicaryList.do"

# 요청 헤더 데이터
request_headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01", # 지워도 안됨
    "Origin": "https://les.klef.go.kr", # 지워도 안됨
    "Referer": "https://les.klef.go.kr/keris_ui/intr/QAABBMNWDMN002M01.do" # 지워도 안됨
    # 필수헤더 빼먹었나?
}

# 요청 본문 데이터
request_body = {
    "dsSrchParam": [
        {
            "wordNm": "",
            "flag": "true" # True도 해봤으나 안됨
        }
    ]
}

# 쿠키 저장
session = requests.session()

try:
    # 세션 문제인가 해서 홈페이지 get 요청으로 세션 받아오고 API 요청해봤으나 실패
    session.get("https://les.klef.go.kr/keris_ui/intr/QAABBMNWDMN002M01.do")
    print(f"GET 요청 쿠키: {session.cookies.get_dict()}") # 쿠키 값 확인

    # API POST 요청 전송
    response = session.post(API_url, headers=request_headers, json=request_body)

    # 응답 상태 코드 200 ok
    print(f"status code: {response.status_code}")
    response.raise_for_status()

    # 헤더 확인해보면 세션 정보 일치
    print(f"response headers: {response.headers}")

    # 응답 body로 JSON이 들어와야 정상이지만 HTML(에러 페이지) 응답
    print(response.text)
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
