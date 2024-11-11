# pypdf2에서 폰트 및 기타 리소스 인식에 문제가 생길 경우 pymupdf로 해당 파일을 분할해볼 것을 추천한다.

import fitz  # pip install PyMuPDF
import pdfplumber  # pip install pdfplumber
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
                # pdfplumber로 파일 열기 (테이블 추출용)
                with pdfplumber.open(file_path) as pdf, fitz.open(file_path) as doc:
                    output_doc = None
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
                                        if output_doc and output_doc.page_count > 2:
                                            output_doc.save(output_file, 
                                                          from_page=0, 
                                                          to_page=output_doc.page_count - 3)
                                    else:
                                        if output_doc:
                                            output_doc.save(output_file)
                                    logging.info(f"새 챕터 확인할 파일명: 2023_02_{division_num-1:05d}")
                                    output_doc.close()
                                    output_doc = fitz.open()
                                output_file = None
                                continue
                            
                            if len(tables) > 0:
                                expenditure_table = any(len(table) == 2 and len(table[0]) == 1 and re.fullmatch(r'사\s*업\s*명', table[0][0]) for table in tables)

                                # 세출 부분 분할
                                if expenditure_table or re.search(r'사업\s+지원\s+형태', text):
                                    # 이전 문건 저장
                                    if output_file and output_doc and output_doc.page_count > 0:
                                        output_doc.save(output_file)
                                        output_doc.close()
                                    
                                    # 새 문건 시작
                                    output_doc = fitz.open()
                                    output_file = os.path.join(output_path, f"2023_02_{division_num:05d}.pdf")
                                    output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                                    division_num += 1

                                # 테이블이 있지만 분할 기준이 없는 페이지
                                elif output_doc:
                                    output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                            # 테이블이 없는 페이지
                            elif output_doc:
                                output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                        except Exception as page_error:
                            logging.error(f"페이지 {page_num + 1} 처리 중 오류 발생: {str(page_error)} - 이 페이지는 건너뜁니다.")
                    
                    # 마지막 문서 저장
                    if output_file and output_doc and output_doc.page_count > 0:
                        output_doc.save(output_file)
                        output_doc.close()
                    
                logging.info(f"처리 완료: {file_name} / 마지막 파일명: {division_num-1}")
            
            except Exception as e:
                logging.error(f"error: {str(e)} in file: {file_name}")

# 실행
division_num = 1917  # 분할 시작 번호
input_path = r'C:\Users\User\Desktop\새 폴더'
output_path = r'C:\Users\User\Desktop\새 폴더'  # 저장될 경로 지정
pdf_division(input_path, output_path, division_num)
