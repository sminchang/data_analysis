import pdfplumber
import PyPDF2
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
                # PDF 읽기 위한 객체들 생성
                pdf_reader = PyPDF2.PdfReader(file_path)
                pdf_writer = PyPDF2.PdfWriter()
                output_file = None
                
                # pdf 파일 열기
                with pdfplumber.open(file_path) as pdf:
                    # 파일 내 모든 페이지 순회
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            # 페이지에서 테이블 추출
                            tables = page.extract_tables()
                            
                            if len(tables) > 0:
                                expenditure_table = any(len(table) == 2 and len(table[0]) == 1 and re.search(r'사\s*업\s*명', table[0][0]) for table in tables)
                                
                                # 세출 부분 분할
                                if expenditure_table:
                                    # 이전 문건 저장
                                    if output_file and len(pdf_writer.pages) > 0:
                                        with open(output_file, 'wb') as f:
                                            pdf_writer.write(f)
                                    # 새 문건 시작
                                    pdf_writer = PyPDF2.PdfWriter()
                                    output_file = os.path.join(output_path, f"2022_02_{division_num:05d}.pdf")
                                    pdf_writer.add_page(pdf_reader.pages[page_num])
                                    division_num += 1

                                # 테이블이 있지만 분할 기준이 없는 페이지, 직전 문건에 이어서 저장
                                else:
                                    if output_file:
                                        pdf_writer.add_page(pdf_reader.pages[page_num])

                            # 테이블이 없는 페이지, 직전 문건에 이어서 저장
                            else:
                                if output_file:
                                    pdf_writer.add_page(pdf_reader.pages[page_num])

                        except Exception as page_error:
                            print(f"페이지 {page_num + 1} 처리 중 오류 발생: {str(page_error)} - 이 페이지는 건너뜁니다.")
                            
                    # 마지막 문서 저장
                    if output_file and len(pdf_writer.pages) > 0:
                        with open(output_file, 'wb') as f:
                            pdf_writer.write(f)
                            
                print(f"처리 완료: {file_name}")
                            
            except Exception as e:
                print(f"error: {str(e)} in file: {file_name}")

# 실행
division_num = 28 # 분할 시작 번호
input_path = r'C:\Users\User\Desktop\2022_pdf'
output_path = r'C:\Users\User\Desktop\2022_output'  # 저장될 경로 지정
pdf_table_extract(input_path, output_path, division_num)
