import requests
import certifi
from bs4 import BeautifulSoup


#주요 기능
#1.정적 페이지에서 활용 가능한 기본적인 웹 스크래핑


#URL 및 헤더 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
base_url = 'https://www.codil.or.kr/viewSubTchStd.do?sType=type1All&sType2=&sortCase=ASC&pageIndex=' #뒤에 페이징 번호만 넣어주면 된다.

#페이지 번호 순회(1~68)
for page_num in range(1,69) :

    url = f'{base_url}{page_num}'

    response = requests.get(url,headers=headers,  verify=False) #SSL 검증 오류로 임시 비활성화 상태
    soup = BeautifulSoup(response.text, 'html.parser')

    #목록 불러오기
    limit_list = soup.select('#content > div > div.content > div.tb_group > div.srchTable > table > tbody > tr')

    for tr in limit_list :
        title = tr.select_one('td.title > a')
        sourceInfo = tr.select_one('td.title > p')
        place = tr.select_one('td:nth-child(4) > p:nth-child(1)')
        #print(f"Original Text: {repr(place.text)}") #&nbsp;로 인한 문자열 형식 오류 확인
        infoType = tr.select_one('td:nth-child(4) > p:nth-child(2) > span')

        print(title.text)
        print(f'https://www.codil.or.kr/{title.get('href')}')
        print(sourceInfo.text.replace('출처정보 : ', '').strip())
        print(place.text.replace('발 행 처\xa0\xa0:','').strip())
        print(infoType.text) #span id값 기반의 동적 요소로 추출되는 값이 없다. #infoType.get('id')로 span id값은 가져올 수 있다.
