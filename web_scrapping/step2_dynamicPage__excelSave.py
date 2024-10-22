import requests
import certifi
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import pandas as pd

#주요 기능
#1.웹 드라이버를 활용한 동적 페이지 스크래핑
#2.추출한 데이터 엑셀 파일에 자동 저장

# 크롬 드라이버 자동 설치 및 실행 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

#URL 및 헤더 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
base_url = 'https://www.codil.or.kr/viewSubTchStd.do?sType=type1All&sType2=&sortCase=ASC&pageIndex=' #뒤에 페이징 번호만 넣어주면 된다.

#데이터 저장할 리스트 생성
data = []

#페이지 번호 순회(1~68)
for page_num in range(1,69) :

    url = f'{base_url}{page_num}'
    driver.get(url)
    time.sleep(5) #페이지 로딩 중 락킹 설정

    #페이지 요청 및 파싱
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    #목록 불러오기
    limit_list = soup.select('#content > div > div.content > div.tb_group > div.srchTable > table > tbody > tr')

    for tr in limit_list :
        title = tr.select_one('td.title > a')
        sourceInfo = tr.select_one('td.title > p')
        place = tr.select_one('td:nth-child(4) > p:nth-child(1)')
        #print(f"Original Text: {repr(place.text)}") #&nbsp;로 인한 문자열 형식 오류 확인
        infoType = tr.select_one('td:nth-child(4) > p:nth-child(2) > span')

        # 데이터를 딕셔너리로 저장
        row_data = {
            '제목': title.text if title else '',
            '링크': f'https://www.codil.or.kr/{title.get("href")}' if title else '',
            '출처정보': sourceInfo.text.replace('출처정보 : ', '').strip() if sourceInfo else '',
            '발행처': place.text.replace('발 행 처\xa0\xa0:', '').strip() if place else '',
            '정보유형': infoType.text if infoType else ''
        }

        # 데이터 리스트에 추가
        data.append(row_data)


driver.quit()


# 데이터프레임 생성
df = pd.DataFrame(data)

# Excel 파일로 저장
df.to_excel('codil_data.xlsx', index=False)
