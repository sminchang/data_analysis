import requests #pip install requests 
from bs4 import BeautifulSoup #pip install beautifulsoup4
import pandas as pd #pip install pandas, pip install openpyxl



data = []
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

def depth2_extarction(excel_path, output_path):
    
    # 엑셀 파일 읽기
    df = pd.read_excel(excel_path)
    try:
        # 엑셀 행 단위로 순회하며, 지정된 열 값 추출
        for index, row in df.iterrows():
            read_data = row.to_dict()
            seq = read_data['연번']
            seqWord = read_data['seqWord']
            url = read_data['상세 링크']

            # depth2로 요청-응답
            response = requests.get(url, headers=headers, verify=False)

            # HTML element 추출
            soup = BeautifulSoup(response.text, 'html.parser')
            limit_table = soup.select('#pop-wrap > div > table')

            for table in limit_table :
                title = table.select_one('tbody > tr:nth-child(1) > td')
                source = table.select_one('tbody > tr:nth-child(2) > td')
                content = table.select_one('tbody > tr:nth-child(3) > td')

                # 행 생성
                row_data = {
                    '연번': seq,
                    'seqWord': seqWord,
                    '용어명': title.text,
                    '출처': source.text,
                    '용어설명': content.text
                }
                data.append(row_data)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 데이터프레임 생성
        df = pd.DataFrame(data)

    # Excel 파일로 저장
    df.to_excel(output_path, index=False)

excel_path = r"C:\Users\User\Desktop\179.국민건강보험법령용어_depth1.xlsx"
output_path = r"C:\Users\User\Desktop\179.국민건강보험법령용어_depth2.xlsx"
depth2_extarction(excel_path, output_path)
