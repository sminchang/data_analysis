import pandas as pd
import requests
from urllib.parse import quote
import ssl
import os
import re
import logging
from datetime import datetime


# SSL 인증서 검증 비활성화 (보안상 권장되지 않음, 필요한 경우에만 사용)
ssl._create_default_https_context = ssl._create_unverified_context


# 로깅 설정
def setup_logging(download_folder):
    # 로그 파일 생성
    log_filename = os.path.join(download_folder, f'download_errors_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 로거 설정
    logging.basicConfig(
        filename=log_filename,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# 다운로드 폴더 생성 (존재하지 않으면)
def create_download_folder(folder_name):
    os.makedirs(folder_name, exist_ok=True)
    return folder_name


# Content-Disposition에서 확장자 추출 함수
def get_extension_name(content_disposition):
    if not content_disposition:
        return None
    # Content-Disposition에서 파일 이름 추출
    fname = re.findall('filename="(.+)"', content_disposition)
    if len(fname) == 0:
        fname = re.findall("filename\*=UTF-8''(.+)", content_disposition)
    
    if len(fname) > 0:
        # 파일 이름에서 확장자만 추출
        _, ext = os.path.splitext(fname[0])
        return ext
    return None


# 파일 다운로드 함수
def download_file(df, download_folder):
    setup_logging(download_folder)  # 로깅 설정
    
    for index, row in df.iterrows():
        excel_data = row.to_dict()
        file_name = str(excel_data['유니코드'])  # 파일 이름이 숫자인 경우 문자열로 변환
        url = excel_data['다운로드링크']

        encoded_url = quote(url, safe=':/?=&')  # URL 인코딩 (한글 부분만)

        try:
            # requests를 사용하여 파일 다운로드
            response = requests.get(encoded_url)
            response.raise_for_status()

            # Content-Disposition 헤더에서 확장자 추출
            content_disposition = response.headers.get('Content-Disposition')
            file_extension = get_extension_name(content_disposition)
            
            # 추출되는 확장자가 없으면 기본 확장자 사용
            if not file_extension:
                file_extension = ''
            
            # 기본 이름에 확장자를 추가
            file_name_with_ext = file_name + file_extension
            
            # 파일 경로를 'downloads' 폴더로 지정
            file_path = os.path.join(download_folder, file_name_with_ext)
            
            # 파일 저장
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
        except requests.RequestException as e:
            logging.error(f"'{file_name}' 다운로드 중 오류 발생: {e}")  # 로그 파일에 기록

    print("다운로드 작업이 완료되었습니다.")


folder_name = create_download_folder('downloads')  # 업로드 경로 설정
df = pd.read_excel('testA.xlsx', engine='openpyxl')  # 읽어올 Excel 경로
download_file(df, folder_name)  # 파일 다운로드
