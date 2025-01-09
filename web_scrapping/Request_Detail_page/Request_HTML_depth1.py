import requests #pip install requests 
from bs4 import BeautifulSoup #pip install beautifulsoup4
import pandas as pd #pip install pandas, pip install openpyxl
import re

#데이터 저장할 리스트 생성
data = []
#URL 및 헤더 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

def depth1_extarction(base_url, output_path):
    #페이지 번호 순회(1~863)
    for page_num in range(1,864) :

        url = f'{base_url}{page_num}'

        response = requests.get(url, headers=headers, verify=False) #SSL 검증 오류로 임시 비활성화 상태
        
        # HTML element 추출
        soup = BeautifulSoup(response.text, 'html.parser')
        limit_list = soup.select('#container > div > div > table > tbody > tr')

        for tr in limit_list :
            seq = tr.select_one('td:nth-child(1)')
            dep2_tag = tr.select_one('td:nth-child(3) > a')
            
            # 추가 작업: seqWord 값 추출
            dep2_tag_value = dep2_tag.get('href')
            dep2_match = re.search(r"seqWord=(\d+)", dep2_tag_value)
            seqWord = dep2_match.group(1)

            # 행 생성성
            row_data = {
                "연번": seq.text,
                "seqWord": seqWord,
                "상세 링크": f'https://www.nhis.or.kr/lm/lmxsrv/word/lawWordInfo.do?seqWord={seqWord}'
            }
            data.append(row_data)

    # 데이터프레임 생성
    df = pd.DataFrame(data)
    # Excel 파일로 저장
    df.to_excel(output_path, index=False)

# Query Param으로 페이지 번호 입력이 가능한 경우로, 불가능할 경우 Request Body에 페이지 번호 넣어서 보내야함
base_url = 'https://www.nhis.or.kr/lm/lmxsrv/word/lawWordList.do?page='
output_path = r"C:\Users\User\Desktop\179.국민건강보험법령용어_depth1.xlsx"
depth1_extarction(base_url, output_path)