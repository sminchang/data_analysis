import requests
import pandas as pd #pip install pandas, pip install openpyxl
import datetime

today_year = datetime.date.today().year

data = []

# 요청 URL
API_url = "https://likms.assembly.go.kr/inspections/getAtbFileList.do"

# 요청 헤더 데이터
request_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# batch 용도, 기본 세팅값
current_request_body = {
    "page": 1,
    "maxSize": "",
    "totalPage": "",
    "fromYear": today_year,
    "toYear": today_year,
    "committeeName": "전체",
    "audittypeCdb": "000281", #국정감사계획서 코드
    "query": "",
    "pageSize": 9999 # 임의 max값
}
past_request_body = {
    "page": 1,
    "maxSize": "",
    "totalPage": "",
    "fromYear": 2000,
    "toYear": 2023,
    "committeeName": "전체",
    "audittypeCdb": "000281", #국정감사계획서 코드
    "query": "",
    "pageSize": 9999 # 임의 max값
}


def getAtbFileList(request_data):
    try:
        response = requests.post(API_url, headers=request_headers, data=request_data)
        response.raise_for_status()
        response_data = response.json()

        for item in response_data["atbList"]:
            committeeName = item.get("committeeName", "") or ""
            bokkId = item.get("bokkId", "") or ""
            year = item.get("year", "") or ""

            row_data = {
                '파일ID(bokkId)': bokkId,
                '위원회명': committeeName,
                '연도': year,
                'PDF_link': f"https://likms.assembly.go.kr/inspection/plan/2023/pdf/{bokkId}.PDF",
                'HWP_link': f"https://likms.assembly.go.kr/inspection/plan/2023/hwp/{bokkId}.HWP"
            }
            data.append(row_data)
        
    except requests.exceptions.RequestException as e:
        print(f"error: {e}")


if __name__ == "__main__":

    # batch 용도, 매년 3월즈음(확인 필요) insert
    # getAtbFileList(current_request_body)

    # 과거 데이터 수집, 초기 수집 후 주석 처리
    getAtbFileList(past_request_body)

    # 데이터프레임 생성
    df = pd.DataFrame(data)

    # Excel 파일로 저장
    df.to_excel('국정감사계획서.xlsx', index=False)