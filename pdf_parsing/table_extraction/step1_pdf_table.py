# 엑셀 파일에 pdfplumber가 인식하고 변환하는 table 형식을 출력하여 pdf의 table 구조를 분석하는데 활용

import pdfplumber #pip install pdfplumber
import pandas as pd #pip install pandas, pip install openpyxl
import os

# step1. 기본 테이블 구조를 파악하기 위해 헤더를 추출한다.

def pdf_table_extract(input_path, output_file):

    excel_data = []

    # 해당 폴더 안에 있는 파일 리스트(여러 파일) 불러오기
    for file_name in os.listdir(input_path):
        file_path = os.path.join(input_path, file_name)

        if file_name.endswith('.pdf'):
            file_name = os.path.splitext(file_name)[0] # 파일명에서 확장자 제거

            try:
                # PDF 파일 열기
                with pdfplumber.open(file_path) as pdf:
                    # 페이지 단위 순회
                    for page_num, page in enumerate(pdf.pages):

                        # 기본 추출 영역 확인
                        if not os.path.exists('table_debug'):
                            os.makedirs('table_debug')
                        page.to_image().debug_tablefinder().save(f"table_debug/{page_num}_debug.png")
                        
                        tables = page.extract_tables() 
                        # 테이블 단위 순회
                        for table in tables:
                            #행 단위 데이터 추출
                            for row in table:
                                excel_data.append([file_name] + row)
                            excel_data.append([]) # 테이블 간 공백 행 추가

            except Exception as e:
                print(f"오류 발생: {e}"+file_name)
                excel_data.append([file_name, "오류 발생"])

    #엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel(output_file, index=False, header=False)
    print(f"데이터가 {output_file}로 저장되었습니다.")

if __name__ == "__main__":
    input_path= r"C:\Users\yunis\바탕 화면\test"
    output_file = 'test_table.xlsx'

    pdf_table_extract(input_path, output_file)