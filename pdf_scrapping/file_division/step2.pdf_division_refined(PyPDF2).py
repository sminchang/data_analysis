# pymupdf는 내장 폰트 등의 문서 리소스를 페이지 단위로 저장하고
# pypdf2는 내장 폰트 등의 문서 리소스를 파일 단위로 저장하기 때문에
# 파일 크기 측면에서 pypdf2가 3~4배 정도 작은 파일 크기로 분할한다.
# pymupdf는 pypdf2보다 다양한 pdf 구조를 처리할 수 있다.
# pypdf2에서 안정성이 떨어지는 경우가 아니라면 pypdf2가 나아보인다.


import pdfplumber  # pip install pdfplumber
from PyPDF2 import PdfReader, PdfWriter  # pip install PyPDF2
import re
import os
import logging

def pdf_division(input_path, output_path, division_num):
    
    # output 폴더가 없으면 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 로그 파일 설정
    logging.basicConfig(
        filename=os.path.join(output_path, 'pdf_division.log'),
        level=logging.INFO,
        format='%(message)s',
        encoding='utf-8'
    )

    # 폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):
        if file_name.endswith('.pdf'):
            # 파일 경로 설정
            file_path = os.path.join(input_path, file_name)
            
            try:
                # pdfplumber로 파일 열기
                with pdfplumber.open(file_path) as pdf:
                    # PyPDF2로 파일 열기
                    pdf_reader = PdfReader(file_path)
                    pdf_writer = PdfWriter()  # 새 PDF 파일을 위한 PyPDF2 writer 객체
                    output_file = None
                    
                    # 파일 내 모든 페이지 순회
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            # 페이지에서 테이블 추출
                            tables = page.extract_tables()
                            text = page.extract_text().strip()

                            # 새 챕터의 시작이 껴있는 경우, 마지막 세출에 새 챕터의 총괄-세입이 딸려오는 예외처리
                            if re.search(r"1\.\s+총\s*괄", text):
                                if output_file:
                                    prev_page = pdf.pages[page_num - 1]
                                    prev_text = prev_page.extract_text().strip()
                                    if len(prev_text) == 0 or re.match(r'^-\s*\d+\s*-$', prev_text):
                                        temp_writer = PdfWriter()
                                        for i in range(len(pdf_writer.pages) - 2):
                                            temp_writer.add_page(pdf_writer.pages[i])
                                        with open(output_file, 'wb') as output:
                                            temp_writer.write(output)
                                    else:
                                        with open(output_file, 'wb') as output:
                                            pdf_writer.write(output)
                                    logging.info(f"새 챕터 확인할 파일명: 2022_02_{division_num-1:05d}")
                                    pdf_writer = PdfWriter()
                                output_file = None
                                continue
                            
                            if len(tables) > 0:
                                expenditure_table = any(len(table) == 2 and len(table[0]) == 1 and re.fullmatch(r'사\s*업\s*명', table[0][0]) for table in tables)

                                # 세출 부분 분할
                                if expenditure_table  or re.search(r'사업\s+지원\s+형태', text): #사업명이 테이블로 인식되지 않는 경우가 있어 텍스트 정규 표현식도 조건에 추가
                                    # 이전 문건 저장
                                    if output_file and len(pdf_writer.pages) > 0:
                                        with open(output_file, 'wb') as output:
                                            pdf_writer.write(output)
                                    
                                    # 새 문건 시작
                                    pdf_writer = PdfWriter()  # 새로운 writer 생성
                                    output_file = os.path.join(output_path, f"2022_02_{division_num:05d}.pdf")
                                    pdf_writer.add_page(pdf_reader.pages[page_num])
                                    division_num += 1

                                # 테이블이 있지만 분할 기준이 없는 페이지
                                elif output_file:
                                        pdf_writer.add_page(pdf_reader.pages[page_num])

                            # 테이블이 없는 페이지
                            elif output_file:
                                    pdf_writer.add_page(pdf_reader.pages[page_num])

                        except Exception as page_error:
                            logging.error(f"페이지 {page_num + 1} 처리 중 오류 발생: {str(page_error)} - 이 페이지는 건너뜁니다.")
                    
                    # 마지막 문서 저장
                    if output_file and len(pdf_writer.pages) > 0:
                        with open(output_file, 'wb') as output:
                            pdf_writer.write(output)
                    
                logging.info(f"처리 완료: {file_name} / 마지막 파일명: {division_num-1}")
            
            except Exception as e:
                logging.error(f"error: {str(e)} in file: {file_name}")

# 실행
division_num = 6038  # 분할 시작 번호
input_path = r'C:\Users\User\Desktop\2021_pdf'
output_path = r'C:\Users\User\Desktop\2021_division'  # 저장될 경로 지정
pdf_division(input_path, output_path, division_num)
