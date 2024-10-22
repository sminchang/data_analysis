from urllib import request
import pandas as pd
import ssl

# SSL 인증서 검증 비활성화
ssl._create_default_https_context = ssl._create_unverified_context

df = pd.read_excel('codil_data_with_depth2.xlsx')

for index, row in df.iterrows():
    depth1_data = row.to_dict()
    url = depth1_data['#depth2_링크']
    fileName = f"./data2/{depth1_data['#depth2_제목']}.pdf"

    #url로부터 파일을 다운받고, 현재 디렉토리에 (경로)fileName으로 저장하는 함수
    request.urlretrieve(url, fileName)

print("다운로드를 완료했습니다.")
