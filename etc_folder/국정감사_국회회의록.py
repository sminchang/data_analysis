import requests
import pandas as pd #pip install pandas, pip install openpyxl
from bs4 import BeautifulSoup #pip install beautifulsoup4
import datetime
import re

# batch 용도, 기본 세팅값
today_year = datetime.date.today().year
today_daeNum = (today_year - 1988) // 4 + 13 # 1988년 13대를 기준점으로 현재 연도의 제안대수 계산 (1988년부터 4년 주기가 확보되었기 때문)

# 엑셀 용도, 전역 리스트
data = []

# 공용 요청 헤더
request_headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}


def commCode_request():
    """현재 연도의 제안대수 내 국정감사가 이루어진 상임위원회 코드 정보 수집"""
    try:
        commCode_url = "https://likms.assembly.go.kr/record/mhs-40-010-0011.do"
        commCode_request_body = {
                "classCode": 5, #국정감사 카테고리 코드
                "subClassCode": "",
                "commName": "",
                "daeNum": today_daeNum,
                "commCode": "",
                "sesNum": "",
                "conferNum": "",
                "confDate": "",
                "degreeNum": "",
                "subcommCode": "",
                "confYear": "",
                "menuId": "",
                "angunType": "",
                "outConn": ""
            }
        commCode_response = requests.post(commCode_url, headers=request_headers, data=commCode_request_body) #content-type이 form data면 data= / json이면 json=
        commCode_response.encoding ='utf-8'
        commCode_response.raise_for_status() # 응답 상태 코드 확인(오류 코드일 경우 예외 발생)
        commCode_response_data = commCode_response.json()

        commCode_list = [item.get("commCode", "") or "" for item in commCode_response_data["comitList"]]
        commName_list = [item.get("commName", "") or "" for item in commCode_response_data["comitList"]]
        return commCode_list, commName_list

    except requests.exceptions.RequestException as e:
            print(f"commCode_request error: {e}")


def baGubun_request(conferNum):
    """부록이 있는 경우 == 서면질의서가 있는 경우, 서면질의서 파일번호 수집 함수"""
    try:
        baGubun_url = "https://likms.assembly.go.kr/record/mhs-40-030.do"
        baGubun_request_body = {
            "conferNum": conferNum,
            "baGubun": "A"
        }
        baGubun_response = requests.post(baGubun_url, headers=request_headers, data=baGubun_request_body) #content-type이 form data면 data= / json이면 json=
        baGubun_response.encoding ='utf-8'
        baGubun_response.raise_for_status()

        soup = BeautifulSoup(baGubun_response.text, 'html.parser')
        onclick_value = soup.select_one('#wrap > div.container_pop > div > div > ul > li:nth-child(1) > a').get('onclick')
        match = re.search(r"fn_fileDown\('([^']*)','([^']*)','([^']*)'\)", onclick_value)
        return match.group(2)

    except requests.exceptions.RequestException as e:
            print(f"baGubun_request error: {e}")


def conferNum_request(commCode_list, commName_list):
    """해당 연도의 모든 상임위원회별 post 요청하여 모든 국정감사 회의록 정보 수집"""
    conferNum_url = "https://likms.assembly.go.kr/record/mhs-40-010-0014.do"

    for i in range(len(commCode_list)):
        conferNum_request_body = {
            "classCode": 5, #국정감사 카테고리 코드
            "subClassCode": "",
            "commName": "",
            "daeNum": today_daeNum,
            "commCode": commCode_list[i], #상임위원회 코드
            "sesNum": "",
            "conferNum": "",
            "confDate": "",
            "degreeNum": "",
            "subcommCode": "",
            "confYear": today_year,
            "menuId": "",
            "angunType": "",
            "outConn": ""
        }

        try:
            conferNum_response = requests.post(conferNum_url, headers=request_headers, data=conferNum_request_body)
            conferNum_response.encoding ='utf-8'
            conferNum_response.raise_for_status()
            conferNum_response_data = conferNum_response.json()

            for item in conferNum_response_data["auditList"]:
                conferNum = item.get("conferNum", "") or ""
                commCode = item.get("commCode", "") or ""
                subName = item.get("subName", "") or ""
                daeDisp =item.get("daeDisp", "") or ""
                pdfFileId = item.get("pdfFileId", "") or ""
                hwpFileId = item.get("hwpFileId", "") or ""
                confDate1 = item.get("confDate1", "") or ""
                confDate2 = item.get("confDate2", "") or ""
                confDate3 = item.get("confDate3", "") or ""
                baGubun = item.get("baGubun", "") or ""
                baGubunFileId = ""

                if baGubun == "부록":
                    baGubunFileId = baGubun_request(conferNum)

                row_data = {
                    "회의번호": conferNum,
                    "제안대수": daeDisp,
                    "상임위원회코드": commCode,
                    "상임위원회명": commName_list[i],
                    "회의날짜": f"{confDate1}-{confDate2}-{confDate3}",
                    "피감사기관명": subName,
                    "pdf파일번호": pdfFileId,
                    "hwp파일번호": hwpFileId,
                    "서면질의_파일번호": baGubunFileId,
                    "pdf_link": f"https://likms.assembly.go.kr/record/mhs-10-040-0040.do?conferNum={conferNum}&fileId={pdfFileId}&deviceGubun=P" if pdfFileId != "" else "",
                    "hwp_link": f"https://likms.assembly.go.kr/record/mhs-10-040-0040.do?conferNum={conferNum}&fileId={hwpFileId}&deviceGubun=P" if hwpFileId != "" else "",
                    "서면질의_link": f"https://likms.assembly.go.kr/record/mhs-10-040-0040.do?conferNum={conferNum}&fileId={baGubunFileId}&deviceGubun=P" if baGubunFileId != "" else ""
                    #'상세링크B형식': f"https://likms.assembly.go.kr/record/new/getFileDown.jsp?CONFER_NUM={conferNum}"
                }
                data.append(row_data)

        except requests.exceptions.RequestException as e:
            print(f"conferNum_request error: {e}")


if __name__ == "__main__":
    

    # batch 자동 수집
    # commCode_list, commName_list = commCode_request()
    # conferNum_request(commCode_list, commName_list)
    
    # 과거 데이터 수집, 최초 수집 후 주석 처리
    for i in range(1988,2025):
        today_year = i
        today_daeNum = (today_year - 1988) // 4 + 13
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1957,1958):
        today_year = i
        today_daeNum = 3
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1958,1960):
        today_year = i
        today_daeNum = 4
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1960,1961):
        today_year = i
        today_daeNum = 5
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1964,1967):
        today_year = i
        today_daeNum = 6
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1967,1971):
        today_year = i
        today_daeNum = 7
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)
    for i in range(1971,1973):
        today_year = i
        today_daeNum = 8
        commCode_list, commName_list = commCode_request()
        conferNum_request(commCode_list, commName_list)

    # 엑셀 저장
    df = pd.DataFrame(data)
    df.to_excel('국정감사_국회회의록.xlsx', index=False)