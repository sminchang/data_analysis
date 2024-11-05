# pymupdf는 내장 폰트 등의 문서 리소스를 페이지 단위로 저장하고
# pypdf2는 내장 폰트 등의 문서 리소스를 파일 단위로 저장하기 때문에
# 파일 크기 측면에서 pypdf2가 3~4배 정도 작은 파일 크기로 분할한다.

# pymupdf는 pypdf2보다 다양한 pdf 구조를 인식해서 실행 중 오류가 거의 발생하지 않는다.

# 파일 크기 및 작업 속도 측면에서는 pypdf2가, 안정성 측면에서는 pymupdf가 유리한 것으로 보인다.

import pdfplumber #pip install pdfplumber
import fitz  # pip install PyMuPDF
import re
import os

def pdf_table_extract(input_path, output_path, division_num):
    
    # output 폴더가 없으면 생성
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 폴더 내 모든 파일 순회
    for file_name in os.listdir(input_path):
        if file_name.endswith('.pdf'):
            # 파일 경로 설정
            file_path = os.path.join(input_path, file_name)
            
            try:
                # pdfplumber로 파일 열기
                with pdfplumber.open(file_path) as pdf:

                    # PyMuPDF로 파일 열기
                    with fitz.open(file_path) as pdf_reader:
                        pdf_writer = fitz.open()  # 새 PDF 파일을 위한 PyMuPDF 문서 객체
                        output_file = None
                        
                        # 파일 내 모든 페이지 순회
                        for page_num, page in enumerate(pdf.pages):
                            try:
                                # 페이지에서 테이블 추출
                                tables = page.extract_tables()

                                text = page.extract_text().strip()

                                # 빈 페이지인 경우, 새 챕터의 시작을 알리기 때문에 총괄,세입을 지나 다음 세출이 나올 때까지 저장하지 않는다.
                                if len(text) == 0: # 빈 페이지라면
                                    if output_file:
                                        pdf_writer.delete_page(pdf_writer.page_count - 1)  # 마지막 페이지 삭제
                                        pdf_writer.save(output_file)  # 직전 페이지까지 저장
                                        pdf_writer.close()
                                    output_file = None  # output_file 초기화
                                    continue
                                
                                if len(tables) > 0:
                                    expenditure_table = any(len(table) == 2 and len(table[0]) == 1 and re.fullmatch(r'사\s*업\s*명', table[0][0]) for table in tables)

                                    # 세출 부분 분할
                                    if expenditure_table:
                                        # 이전 문건 저장
                                        if output_file and pdf_writer.page_count > 0:
                                            pdf_writer.save(output_file)  # 이전 문서를 저장
                                        # 새 문건 시작
                                        pdf_writer = fitz.open()  # 새로운 문서 시작
                                        output_file = os.path.join(output_path, f"2022_02_{division_num:05d}.pdf")
                                        pdf_writer.insert_pdf(pdf_reader, from_page=page_num, to_page=page_num)
                                        division_num += 1

                                    # 테이블이 있지만 분할 기준이 없는 페이지, 직전 문건에 이어서 저장
                                    else:
                                        if output_file:
                                            pdf_writer.insert_pdf(pdf_reader, from_page=page_num, to_page=page_num)

                                # 테이블이 없는 페이지, 직전 문건에 이어서 저장
                                else:
                                    if output_file:
                                        pdf_writer.insert_pdf(pdf_reader, from_page=page_num, to_page=page_num)

                            except Exception as page_error:
                                print(f"페이지 {page_num + 1} 처리 중 오류 발생: {str(page_error)} - 이 페이지는 건너뜁니다.")
                        
                        # 마지막 문서 저장
                        if output_file and pdf_writer.page_count > 0:
                            pdf_writer.save(output_file)
                            pdf_writer.close()  # 문서 닫기
                        
                    print(f"처리 완료: {file_name}")
                
            except Exception as e:
                print(f"error: {str(e)} in file: {file_name}")

# 실행
division_num = 1  # 분할 시작 번호
input_path = r'C:\Users\CS4_18\Desktop\2021_pdf'
output_path = r'C:\Users\CS4_18\Desktop\2021_division'  # 저장될 경로 지정
pdf_table_extract(input_path, output_path, division_num)
