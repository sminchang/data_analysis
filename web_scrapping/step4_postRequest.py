import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

#주요 기능
#1. function fn_egov_info_search(pageNo) {
# 			document.frm.pageIndex.value = pageNo;
# 			document.frm.action = "/helpdesk/search.do";
# 			document.frm.submit();
# 		} 다음 js 스크립트가 html에 껴있다.

#2. frm이 사용자 정의된 객체이므로 개발자 도구 elements에 frm을 검색해본다.
# <form name="frm" action="/helpdesk/search.do" method="post">
# 	<input type="hidden" name="bbsId" value="BBSMSTR_900000000202">
# 	<input type="hidden" name="nttId" value="0">
# 	<input type="hidden" name="bbsTyCode" value="BBST03">
# 	<input type="hidden" name="bbsAttrbCode" value="BBSA01">
# 	<input type="hidden" name="authFlag" value="">
# 	<input name="pageIndex" id="pageIndex" type="hidden" value="1">
# 	... </form> 

#3. post 요청으로 form 객체에 요청 정보를 담아서 보내는 구조이다.

#4. 페이징을 post 형식으로 request를 보내는 경우에 대한 웹 스크래핑을 진행한다.


# URL 설정
post_url = 'https://www.codil.or.kr/helpdesk/search.do'
depth2_url = 'https://www.codil.or.kr/helpdesk/read.do?'
#최초 요청 url: https://www.codil.or.kr/helpdesk/search.do?bbsId=BBSMSTR_900000000202&bbsAttrbCode=BBSA01

# 요청에 포함할 폼 데이터 설정
form_data = {
    'bbsId': 'BBSMSTR_900000000202',
    'nttId': '0',
    'bbsTyCode': 'BBST03',
    'bbsAttrbCode': 'BBSA01',
    'authFlag': '',
    'pageIndex': '1',  # 페이지 번호 (동적으로 변경 가능)
    'searchCnd': '0',  # 검색 조건 (0: 제목)
    'searchWrd': ''    # 검색어 (빈 값)
}

# 사용자 에이전트 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
}

# 데이터 저장할 리스트 생성
data = []

# 페이지 번호 순회
for page_num in range(1, 4):
    form_data['pageIndex'] = str(page_num)  # 페이지 번호 변경
    
    # POST 요청 보내기 (SSL 인증서 검증 비활성화)
    response = requests.post(post_url, data=form_data, headers=headers, verify=False)

    # 응답 데이터 파싱
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 목록 불러오기
    limit_list = soup.select('#content > div > div.content > table > tbody > tr')

    for tr in limit_list:
        depth2_link = tr.get('onclick')
        title = tr.select_one('td.title')

        depth2_start = depth2_link.find("?") + 1 #URL 시작 부분
        depth2_end = depth2_link.find("'", depth2_start) #URL 끝 부분
        depth2_href = depth2_link[depth2_start:depth2_end]

        # 데이터를 딕셔너리로 저장
        row_data = {
            '제목': title.text if title else '',
            '링크': f'{depth2_url}{depth2_href}',
        }

        # 데이터 리스트에 추가
        data.append(row_data)

# 데이터프레임 생성
df = pd.DataFrame(data)

# Excel 파일로 저장
df.to_excel('codil_data_post.xlsx', index=False)
