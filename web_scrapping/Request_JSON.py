import requests
import json

# 보통 서버 렌더링 방식을 사용하면 HTML로는 페이지 구조만 만들어두고 실제 데이터는 비동기적으로 JSON 데이터를 요청해서 채운다.
# 동적 페이지에서 오가는 JSON 데이터를 스크래핑해와야할 때 JSON 요청을 찾아 직접 API 요청을 보내고 응답을 받는 방법은 다음과 같다. 
# 개발자 도구(F12) -> Network -> filter -> Fetch/XHR -> 페이지 새로고침
# 이렇게하면 비동기적으로 불러온 API 요청들이 조회된다.
# 조회된 요청들의 Response를 확인해서 원하는 JSON 데이터를 찾아내고
# Payload를 확인해서 요청 body에 필요한 포맷이나 값을 확인한다.
# Header를 확인해서 HTTP Metthod, URL, Content-Type, User-Agent 등을 입력해서
# 직접 요청을 보내고 JSON 데이터를 받아오면 된다.


API_url = "https://data.gg.go.kr/portal/data/dataset/searchDataset.do"

request_header = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",  #User-Agent 추가
    # "Cookie" : # 필요한 경우 쿠키 값 추가(로그인 정보 등등)
    # 추가 헤더들
}

# 요청 본문 데이터 (딕셔너리 형태)
request_body = {
    "page": "1",
    "rows": "10",
    "sortColumn": "",
    "sortDirection": "",
    "infId": "",
    "infSeq": "",
    "order": ""
    # 기타 파라미터
}

try:
    # POST 요청 전송
    response = requests.post(API_url, headers=request_header, json=request_body) # 또는 data=request_body

    # 응답 상태 코드 확인(오류 코드일 경우 예외 발생시킴킴)
    response.raise_for_status()

    # JSON 데이터 파싱
    response_data = response.json()
    
    # 데이터 확인
    print(json.dumps(response_data, indent=2, ensure_ascii=False))

    # # 데이터 추출
    # if "data" in response_data:
    #     for item in response_data["data"]:
    #         print(f"infId: {item['infId']}, infSeq: {item['infSeq']}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")