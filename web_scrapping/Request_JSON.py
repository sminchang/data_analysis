import requests
import pandas as pd #pip install pandas, pip install openpyxl


data = []

# 요청 URL
API_url = "https://data.gg.go.kr/portal/data/dataset/searchDataset.do"

# 요청 헤더 데이터
request_headers = {
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
        response = requests.post(API_url, headers=request_headers, data=request_body) #content-type이 form data면 data= / json이면 json=

        # 응답 상태 코드 확인(오류 코드일 경우 예외 발생)
        response.raise_for_status()

        # JSON 데이터 파싱
        response_data = response.json()
        
        page = response_data["page"]

        for item in response_data["data"]:
            seq = item.get("seq", "") or ""
            infId = item.get("infId", "") or ""
            infNm = item.get("infNm", "") or ""
            infExp = item.get("infExp", "") or ""
            regDttm = item.get("regDttm", "") or ""
            updDttm = item.get("updDttm", "") or ""
            topCateId = item.get("topCateId", "") or ""
            topCateNm = item.get("topCateNm", "") or ""
            topCateId2 = item.get("topCateId2", "") or ""
            topCateNm2 = item.get("topCateNm2", "") or ""

            # 추출한 텍스트 내 html 요소가 포함된 경우 (import html, BeautifulSoup)
            # html_text = html.unescape(infExp) # html 태그가 html 엔티티로 인코딩된 경우, 디코딩
            # soup = BeautifulSoup(html_text, 'html.parser') #html 태그 파싱
            # infExp = soup.get_text()

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
