import requests
import json
import pandas as pd #pip install pandas, pip install openpyxl

# data resource: https://data.gg.go.kr/portal/data/dataset/searchDatasetPage.do

# 보통 서버 렌더링 방식을 사용하면 HTML로는 페이지 구조만 만들어두고 실제 데이터는 비동기적으로 JSON 데이터를 요청해서 채운다.
# 동적 페이지에서 오가는 JSON 데이터를 스크래핑해와야할 때 JSON 요청을 찾아 직접 API 요청을 보내고 응답을 받는 방법은 다음과 같다. 
# 개발자 도구(F12) -> Network -> filter -> Fetch/XHR -> 페이지 새로고침
# 이렇게하면 비동기적으로 불러온 API 요청들이 조회된다.
# 조회된 요청들의 Response를 확인해서 원하는 JSON 데이터를 찾아내고
# Payload를 확인해서 요청 body에 필요한 포맷이나 값을 확인한다.
# Header를 확인해서 HTTP Metthod, URL, Content-Type, User-Agent 등을 입력해서
# 직접 요청을 보내고 JSON 데이터를 받아오면 된다.

data = []

# 요청 URL
API_url = "https://data.gg.go.kr/portal/data/dataset/searchDataset.do"

# 요청 헤더 데이터
request_header = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",  #User-Agent 추가
    # "Cookie" : # 필요한 경우 쿠키 값 추가(로그인 정보 등등)
    # 추가 헤더들
}

# 페이지 단위로 HTTP 요청
for page_num in range(1,201): #마지막 페이지 200까지

    # 요청 본문 데이터 (딕셔너리 형태)
    request_body = {
        "page": page_num,
        "rows": 10,
        "sortColumn": "",
        "sortDirection": "",
        "infId": "",
        "infSeq": "",
        "order": ""
        # 기타 파라미터
    }

    try:
        # POST 요청 전송
        response = requests.post(API_url, headers=request_header, data=request_body)

        # 응답 상태 코드 확인(오류 코드일 경우 예외 발생)
        response.raise_for_status()

        # JSON 데이터 파싱
        response_data = response.json()
        
        page = response_data["page"]

        for item in response_data["data"]:
            seq = item.get("seq", "")
            infId = item.get("infId", "")
            infNm = item.get("infNm", "")
            infExp = item.get("infExp", "")
            regDttm = item.get("regDttm", "")
            updDttm = item.get("updDttm", "")
            topCateId = item.get("topCateId", "")
            topCateNm = item.get("topCateNm", "")
            topCateId2 = item.get("topCateId2", "")
            topCateNm2 = item.get("topCateNm2", "")

            row_data = {
                "seq": seq,
                "infId": infId,
                '제목': infNm,
                '내용': infExp,
                '등록일자': regDttm,
                '마지막수정일자': updDttm,
                '사업 유형1 코드': topCateId,
                '사업 유형1 이름': topCateNm,
                '사업 유형2 코드': topCateId2,
                '사업 유형2 이름': topCateNm2,
                '상세링크': f"https://data.gg.go.kr/portal/data/service/selectServicePage.do?page={page}&rows=10&sortColumn=&sortDirection=&infId={infId}&infSeq=1&order="
            }

            data.append(row_data)
        
        # 데이터 확인
        # print(json.dumps(response_data, indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# 데이터프레임 생성
df = pd.DataFrame(data)

# Excel 파일로 저장
df.to_excel('json_data.xlsx', index=False)
